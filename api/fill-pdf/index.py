import json, os, base64, hashlib, hmac, httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC   = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FROM_EMAIL     = "offers@homeofferflow.com"
SUPPORT_EMAIL  = "support@homeofferflow.com"

BASE_DIR      = "/var/task"
MAIN_PDF      = os.path.join(BASE_DIR, "20-18_0.pdf")
FINANCING_PDF = os.path.join(BASE_DIR, "third_party_financing_addendum.pdf")
HOA_PDF       = os.path.join(BASE_DIR, "hoa_addendum.pdf")
SALE_PDF      = os.path.join(BASE_DIR, "sale_of_other_property_addendum.pdf")
BACKUP_PDF    = os.path.join(BASE_DIR, "back_up_contract_addendum.pdf")

def fmt_money(v):
    if not v: return ""
    try:
        return f"{int(float(v)):,}"
    except:
        return str(v)


def set_text_field(writer, name, value):
    if value is None: value = ""
    value = str(value)
    for page in writer.pages:
        if "/Annots" not in page: continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                if annot.get("/T") == name or str(annot.get("/T", "")) == name:
                    annot.update({NameObject("/V"): TextStringObject(value)})
            except:
                pass


def check_field(writer, name, checked=True):
    val = NameObject("/Yes") if checked else NameObject("/Off")
    for page in writer.pages:
        if "/Annots" not in page: continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                if annot.get("/T") == name or str(annot.get("/T", "")) == name:
                    annot.update({NameObject("/V"): val, NameObject("/AS"): val})
            except:
                pass


def fill_and_merge(offer):
    s = offer

    # ── Derived values ──
    addr_full  = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"
    buyer_full = s.get("buyer1", "")
    if s.get("buyer2"): buyer_full += f" and {s['buyer2']}"

    price = float(s.get("price", 0) or 0)
    loan  = float(s.get("loanAmount", 0) or 0)
    cash  = price - loan if loan > 0 else price

    has_loan = s.get("financing") in ["conventional", "fha", "va", "usda"]
    has_hoa  = s.get("hoa") in ["yes", "unknown"]
    has_sale = s.get("saleContingency") == "yes"
    has_bkup = s.get("backupOffer") == "yes"

    # Closing date — split into month/day and year
    closing_raw = s.get("closingDate", "")  # expected: "2025-04-04" or "April 4, 2025"
    closing_display = closing_raw  # e.g. "April 4, 2025" — adjust formatting as needed
    closing_year = ""
    if "-" in closing_raw:
        parts = closing_raw.split("-")
        closing_year = parts[0]
        from datetime import datetime
        try:
            dt = datetime.strptime(closing_raw, "%Y-%m-%d")
            closing_display = dt.strftime("%B %d, %Y")
            closing_year = dt.strftime("%Y")
        except:
            pass

    reader = PdfReader(MAIN_PDF)
    writer = PdfWriter()
    writer.append(reader)

    # ── TEXT FIELDS ──
    # Field names are EXACT AcroForm field names from the PDF
    text_map = {
        # Section 1 — Parties
        "1 PARTIES The parties to this contract are": s.get("seller", ""),   # Seller name(s)
        "Seller and":                                  buyer_full,             # Buyer name(s)

        # Section 2 — Property description
        "A LAND Lot":                                  s.get("lot", ""),
        "Block":                                       s.get("block", ""),
        "Addition City of":                            s.get("subdivision", ""),
        "County of":                                   s.get("county", ""),
        "Texas known as":                              addr_full,              # Full address + zip

        # Section 3 — Sales price
        "undefined_3":   fmt_money(int(cash)),                               # 3A cash portion
        "undefined_4":   fmt_money(int(loan)) if has_loan else "",           # 3B loan amount
        "undefined_5":   fmt_money(int(price)),                              # 3C total price

        # Section 5 — Earnest money & option
        "undefined_6":   s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW"),
        "undefined_7":   s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033"),
        "as earnest money to":   fmt_money(s.get("earnest", 0)),             # Earnest money $
        "as earnest money to 2": fmt_money(s.get("optionFee", 0)),           # Option fee $
        "the Title Company and Buyers lenders Check one box only": s.get("optionDays", "7"),  # Option days

        # Section 6 — Title & survey
        "insurance Title Policy issued by":            s.get("titleCompany", "Chicago Title DFW - Forgey Law Group PLLC"),
        "receipt or the date specified in this paragraph whichever is earlier": s.get("surveyDays", ""),
        "Commitment other than items 6A1 through 9 above or which prohibit the following use": s.get("intendedUse", ""),
        "the Commitment Exception Documents and the survey Buyers failure to object within the": s.get("disclosureDays", ""),

        # Section 7 — Property condition
        "following specific repairs and treatments":   s.get("repairs", ""),

        # Section 9 — Closing
        "A The closing of the sale will be on or before": closing_display,   # e.g. "April 4, 2025"
        "20":                                          closing_year,          # just the year

        # Section 12 — Seller concessions
        "Buyers Expenses as allowed by the lender":    fmt_money(s.get("sellerConcessions", 0)),

        # Section 21 — Notices to Buyer
        "when mailed to handdelivered at or transmitted by fax or electronic transmission as follows": s.get("buyerMailAddr",""),

        "Phone 51":                                    s.get("buyerPhone", ""),
        "AC1":                                         s.get("buyerEmail", ""),

        # Section 23 — Attorney info (leave blank unless collected)
        # "Attorney is":   s.get("buyerAttorney", ""),

        # Page 10 — Broker info (buyer's agent)
        "Associates Name numb 1":   s.get("agentName","")     if s.get("hasBuyerAgent") == "yes" else "",
        "License No":              s.get("agentLicense", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Associates Email Address": s.get("agentEmail", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Phone":                   s.get("agentPhone", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Other Broker Firm":       s.get("brokerageName", "") if s.get("hasBuyerAgent") == "yes" else "",
    }

    for name, value in text_map.items():
        set_text_field(writer, name, str(value) if value else "")

    # ── CHECKBOXES ──
    # Addenda checkboxes — exact field names from PDF
    check_field(writer, "Third Party Financing Addendum", has_loan)
    check_field(writer, "Addendum for Property Subject to", has_hoa)        # HOA addendum
    check_field(writer, "Addendum for Sale of Other Property by", has_sale) # Sale contingency
    check_field(writer, "Addendum for BackUp Contract", has_bkup)           # Back-up contract

    # Possession checkbox
    if s.get("possession") == "funding":
        check_field(writer, "upon", True)                                   # "upon closing and funding"

    # As-Is checkbox
    if s.get("asIs") == "yes":
        check_field(writer, "As Is", True)                                  # Buyer accepts As Is
    else:
        check_field(writer, "As Is except", True)                           # As Is with repairs

    # Title policy expense — default to Seller pays (most common in TX)
    check_field(writer, "Sellers", True)                                    # Seller furnishes title policy

    # HOA membership checkbox
    if has_hoa:
        check_field(writer, "is", True)                                     # Property IS subject to HOA
    else:
        check_field(writer, "is not", True)                                 # Property is NOT subject to HOA

    # Survey option — default to option 1 (Seller provides existing survey)
    # Uncomment and wire to wizard if you collect this:
    # check_field(writer, "1Within", True)

    # ── MERGE ADDENDA ──
    for path, flag in [
        (FINANCING_PDF, has_loan),
        (HOA_PDF,       has_hoa),
        (SALE_PDF,      has_sale),
        (BACKUP_PDF,    has_bkup),
    ]:
        if flag and os.path.exists(path):
            writer.append(PdfReader(path))

    out = BytesIO()
    writer.write(out)
    return out.getvalue()
    
    # MERGE ADDENDA
    for path, flag in [(FINANCING_PDF, has_loan), (HOA_PDF, has_hoa), (SALE_PDF, has_sale), (BACKUP_PDF, has_bkup)]:
        if flag and os.path.exists(path):
            writer.append(PdfReader(path))

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


# ── EMAIL & STRIPE (unchanged from your original) ──
def send_email(to_email, buyer_name, addr, pdf_bytes):
    # (keep your existing send_email function exactly as it was)
    pass  # ← paste your original send_email here if you want, or leave as-is

def handle_checkout(event):
    # (keep your existing handle_checkout function)
    pass  # ← paste your original handle_checkout here

class Handler(BaseHTTPRequestHandler):
   def do_GET(self):
    import os
    try:
        contents = os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else []
    except Exception as e:
        contents = str(e)
    out = {
        "status": "ok",
        "base_dir": BASE_DIR,
        "main_pdf_exists": os.path.exists(MAIN_PDF),
        "main_pdf_path": MAIN_PDF,
        "cwd": os.getcwd(),
        "dir_contents": contents
    }
    self.send_response(200)
    self.send_header("Content-Type", "application/json")
    self.end_headers()
    self.wfile.write(json.dumps(out).encode())

    def do_POST(self):
    try:
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        sig    = self.headers.get("stripe-signature","")
        if sig and not verify_stripe_signature(body, sig, STRIPE_WHSEC):
            self._json(401, {"error": "Invalid Stripe signature"}); return
        event = json.loads(body.decode("utf-8"))
        if event.get("type") == "checkout.session.completed":
            result = handle_checkout(event)
            self._json(200, result)
        else:
            self._json(200, {"status": "ignored"})
    except Exception as e:
        print("ERROR:", str(e))
        self._json(500, {"error": str(e)})

def _json(self, code, data):
    self.send_response(code)
    self.send_header("Content-Type","application/json")
    self.end_headers()
    self.wfile.write(json.dumps(data).encode())

handler = Handler
