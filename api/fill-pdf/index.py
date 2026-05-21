import json, os, base64, hashlib, hmac, httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC   = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FROM_EMAIL     = "offers@homeofferflow.com"
SUPPORT_EMAIL  = "support@homeofferflow.com"

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"
    buyer_full = s.get("buyer1", "")
    if s.get("buyer2"): buyer_full += f" and {s['buyer2']}"

    price = float(s.get("price", 0) or 0)
    loan  = float(s.get("loanAmount", 0) or 0)
    cash  = price - loan if loan > 0 else price

    has_loan = s.get("financing") in ["conventional", "fha", "va", "usda"]
    has_hoa  = s.get("hoa") in ["yes", "unknown"]
    has_sale = s.get("saleContingency") == "yes"
    has_bkup = s.get("backupOffer") == "yes"

    reader = PdfReader(MAIN_PDF)
    writer = PdfWriter()
    writer.append(reader)

    # TEXT FIELDS
    text_map = {
        "Buyer": buyer_full,
        "Seller": s.get("seller", ""),
        "Lot": s.get("lot", ""),
        "Block": "",
        "Addition, City of": s.get("city", ""),
        "County of": s.get("county", ""),
        "Texas, known as": addr_full,
        "3A": f"{int(cash):,}" if has_loan else f"{int(price):,}",
        "3B": f"{int(loan):,}" if has_loan else "",
        "3C": f"{int(price):,}",
        "earnest money": f"{int(s.get('earnest',0)):,}",
        "Option Fee": f"{int(s.get('optionFee',0)):,}",
        "Option Period": s.get("optionDays", "7"),
        "Closing Date": s.get("closingDate", ""),
        "To Buyer at": s.get("buyerMailAddr", ""),
        "Phone": s.get("buyerPhone", ""),
        "E-mail": s.get("buyerEmail", ""),
        "Associate's Name": s.get("agentName", "") if s.get("hasBuyerAgent") == "yes" else "",
        "License No.": s.get("agentLicense", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Associate's Email Address": s.get("agentEmail", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Escrow Agent": s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW"),
        "Escrow Address": s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033"),
    }

    for name, value in text_map.items():
        set_text_field(writer, name, value)

    # CHECKBOXES
    check_field(writer, "Third Party Financing Addendum", has_loan)
    check_field(writer, "Addendum for Property Subject to Mandatory Membership in a Property Owners Association", has_hoa)
    check_field(writer, "Addendum for Sale of Other Property by Buyer", has_sale)
    check_field(writer, 'Addendum for "Back-Up" Contract', has_bkup)

    if s.get("possession") == "funding":
        check_field(writer, "upon closing and funding", True)
    if s.get("asIs") == "yes":
        check_field(writer, "Buyer accepts the Property As Is", True)

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
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def do_POST(self):
        # (keep your existing POST logic with Stripe webhook)
        pass  # ← paste your original do_POST here

handler = Handler