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


# ── HELPERS ──────────────────────────────────────────────────────────────────

def fmt_money(v):
    if not v: return ""
    try:
        return f"{int(float(v)):,}"
    except:
        return str(v)


def split_date(v):
    if not v: return "", ""
    try:
        from datetime import datetime
        d = datetime.strptime(v, "%Y-%m-%d")
        return d.strftime("%B %d").replace(" 0", " "), str(d.year)[-2:]
    except:
        return str(v), ""


def parse_lot_block(v):
    import re
    lot = block = ""
    if not v: return lot, block
    m = re.search(r"lot\s*([A-Za-z0-9\-]+)", v, re.I)
    if m: lot = m.group(1)
    m = re.search(r"block\s*([A-Za-z0-9\-]+)", v, re.I)
    if m: block = m.group(1)
    return lot, block


def set_field(writer, name, value):
    if value is None: value = ""
    value = str(value)
    for page in writer.pages:
        if "/Annots" not in page: continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                t = annot.get("/T", "")
                if hasattr(t, "original_bytes"):
                    t = t.original_bytes.decode("utf-8", errors="replace")
                else:
                    t = str(t)
                if t == name:
                    annot.update({NameObject("/V"): TextStringObject(value)})
            except:
                pass


def check_box(writer, name, checked=True):
    val = NameObject("/Yes") if checked else NameObject("/Off")
    for page in writer.pages:
        if "/Annots" not in page: continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                t = annot.get("/T", "")
                if hasattr(t, "original_bytes"):
                    t = t.original_bytes.decode("utf-8", errors="replace")
                else:
                    t = str(t)
                if t == name:
                    annot_ref.get_object().update({
                        NameObject("/V"): val,
                        NameObject("/AS"): val
                    })
            except:
                pass


def verify_stripe_signature(body, sig_header, secret):
    if not secret: return True
    try:
        parts = {}
        for item in sig_header.split(","):
            k, v = item.split("=", 1)
            parts.setdefault(k, []).append(v)
        timestamp  = parts.get("t", [""])[0]
        signatures = parts.get("v1", [])
        expected   = hmac.new(
            secret.encode(),
            timestamp.encode() + b"." + body,
            hashlib.sha256
        ).hexdigest()
        return any(hmac.compare_digest(expected, s) for s in signatures)
    except:
        return False


# ── FILL + MERGE ──────────────────────────────────────────────────────────────

def fill_and_merge(offer):
    s = offer
    lot, block = parse_lot_block(s.get("lot", ""))
    addr_full  = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"
    closing_md, closing_yy = split_date(s.get("closingDate"))

    buyer = s.get("buyer1", "")
    if s.get("buyer2"): buyer += f" and {s['buyer2']}"

    try:
        price = float(s.get("price", 0) or 0)
        loan  = float(s.get("loanAmount", 0) or 0)
        cash  = price - loan if loan else price
    except:
        price = loan = cash = 0

    has_loan = s.get("financing") in ["conventional", "fha", "va", "usda"]
    has_hoa  = s.get("hoa") in ["yes", "unknown"]
    has_sale = s.get("saleContingency") == "yes"
    has_bkup = s.get("backupOffer") == "yes"

    reader = PdfReader(MAIN_PDF)
    writer = PdfWriter()
    writer.append(reader)

    text_fields = {
        "1 PARTIES The parties to this contract are": s.get("seller", ""),
        "Seller and":                                  buyer,
        "A LAND Lot":       lot,
        "Block":            block,
        "undefined":        s.get("subdiv", ""),
        "Addition City of": s.get("city", ""),
        "County of":        s.get("county", ""),
        "Texas known as":   addr_full,
        "undefined_3":      fmt_money(cash) if has_loan else fmt_money(price),
        "undefined_4":      fmt_money(loan) if has_loan else "",
        "undefined_5":      fmt_money(price),
        "as earnest money to":   fmt_money(s.get("earnest")),
        "as earnest money to 2": fmt_money(s.get("optionFee")),
        "the Title Company and Buyers lenders Check one box only": str(s.get("optionDays", "7")),
        "Buyers Expenses as allowed by the lender": fmt_money(s.get("concessionAmount")) if s.get("wantsConcessions") == "yes" else "",
        "undefined_6": s.get("escrowAgent", "Kate Lewis Tucker - Chicago Title DFW"),
        "undefined_7": s.get("escrowAddress", "2770 Main Street, Suite 114, Frisco, TX 75033"),
        "receipt or the date specified in this paragraph whichever is earlier": str(s.get("surveyDays", "7")),
        "Commitment other than items 6A1 through 9 above or which prohibit the following use": s.get("intendedUse", ""),
        "the Commitment Exception Documents and the survey Buyers failure to object within the": str(s.get("disclosureDays", "3")) if s.get("sellerDisclosure") == "notReceived" else "",
        "following specific repairs and treatments": s.get("repairsText", "") if s.get("asIs") == "repairs" else "",
        "A The closing of the sale will be on or before": closing_md,
        "20":  closing_yy,
        "insurance Title Policy issued by": s.get("titleCompany", "Chicago Title DFW - Forgey Law Group PLLC"),
        "when mailed to handdelivered at or transmitted by fax or electronic transmission as follows": s.get("buyerMailAddr", ""),
        "Phone 51":       s.get("buyerPhone", ""),
        "AC1":            s.get("buyerEmail", ""),
        "Associates Name numb 1":   s.get("agentName", "")    if s.get("hasBuyerAgent") == "yes" else "",
        "License No":               s.get("agentLicense", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Associates Email Address":  s.get("agentEmail", "")  if s.get("hasBuyerAgent") == "yes" else "",
        "Phone":                    s.get("agentPhone", "")   if s.get("hasBuyerAgent") == "yes" else "",
        "Other Broker Firm":        s.get("agentBrokerage", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Contract Concerning":   addr_full,
        "Contract Concerning_2": addr_full,
        "Contract Concerning_3": addr_full,
        "Contract Concerning_4": addr_full,
        "Address of Property":   addr_full,
        "Address of Property_2": addr_full,
        "Addr of Prop":          addr_full,
    }

    for name, value in text_fields.items():
        set_field(writer, name, str(value) if value else "")

    title_payer  = s.get("titlePayer", "seller")
    title_amend  = s.get("titleAmendment", "i")
    survey       = s.get("survey", "")
    seller_disc  = s.get("sellerDisclosure", "received")
    as_is        = s.get("asIs", "yes")
    possession   = s.get("possession", "funding")

    checkbox_map = {
        "B Sum of all financing described in the attached": has_loan,
        "Third Party Financing Addendum":                   has_loan,
        "A TITLE POLICY Seller shall furnish to Buyer at":  title_payer == "seller",
        "Sellers":    title_payer == "seller",
        "Seller":     title_payer == "buyer",
        "i will not be amended or deleted from the title policy or": title_amend == "i",
        "ii will be amended to read shortages in area at the expense of": title_amend in ["ii_buyer", "ii_seller"],
        "Buyer":      title_amend == "ii_buyer",
        "1Within":    survey == "sellerExisting",
        "2 Within":   survey == "buyerNew",
        "3Within":    survey == "noSurvey",
        "is":         has_hoa,
        "is not":     not has_hoa,
        "Within one":   seller_disc == "received",
        "Within two":   seller_disc == "notReceived",
        "Within three": seller_disc == "exempt",
        "1 Buyer accepts the Property As Is": as_is == "yes",
        "2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the": as_is == "repairs",
        "upon": possession == "funding",
        "Addendum for Property Subject to":       has_hoa,
        "Addendum for Sale of Other Property by": has_sale,
        "Addendum for BackUp Contract":           has_bkup,
        "Buyer only": s.get("hasBuyerAgent") == "yes",
        "PID": s.get("mud") in ["yes", "unknown"],
    }

    for name, checked in checkbox_map.items():
        check_box(writer, name, checked)

    for path, flag in [
        (FINANCING_PDF, has_loan),
        (HOA_PDF,       has_hoa),
        (SALE_PDF,      has_sale),
        (BACKUP_PDF,    has_bkup),
    ]:
        if flag and os.path.exists(path):
            try:
                writer.append(PdfReader(path))
            except Exception as e:
                print(f"Warning: could not load {path}: {e}")

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


# ── EMAIL ─────────────────────────────────────────────────────────────────────

def send_email(to_email, buyer_name, addr, pdf_bytes):
    filename = f"HomeOfferFlow_Offer_{addr.replace(' ','_').replace(',','')}.pdf"
    payload = {
        "from": FROM_EMAIL,
        "to":   [to_email],
        "bcc":  [SUPPORT_EMAIL],
        "subject": f"Your HomeOfferFlow Offer — {addr}",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2 style="color:#1a2f4a;">Your Offer is Ready, {buyer_name}!</h2>
          <p>Your filled TREC offer for <strong>{addr}</strong> is attached.</p>
          <h3>Next Steps:</h3>
          <ol>
            <li>Review the attached PDF carefully</li>
            <li>Sign and send to the listing agent</li>
            <li>Deliver earnest money within 3 days of acceptance</li>
            <li>Schedule your inspection immediately — don't wait</li>
          </ol>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.85rem;">
            ⚠️ <strong>Not legal advice.</strong> Consider having a licensed Texas agent or attorney review before submitting.
          </p>
        </div>""",
        "attachments": [{
            "filename": filename,
            "content":  base64.b64encode(pdf_bytes).decode(),
            "content_type": "application/pdf"
        }]
    }
    r = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30
    )
    if r.status_code not in [200, 201, 202]:
        raise Exception(f"Resend error {r.status_code}: {r.text[:200]}")


# ── STRIPE HANDLER ────────────────────────────────────────────────────────────

def handle_checkout(event):
    session        = event.get("data", {}).get("object", {})
    customer_email = (session.get("customer_email") or
                      session.get("customer_details", {}).get("email", ""))
    metadata       = session.get("metadata", {}) or {}

    # Reassemble chunked offer data
    if "offer_data" in metadata:
        offer = json.loads(metadata["offer_data"])
    else:
        parts    = int(metadata.get("offer_parts", 0) or 0)
        combined = "".join(metadata.get(f"offer_{i}", "") for i in range(parts))
        if not combined:
            raise Exception(f"No offer data found. Metadata keys: {list(metadata.keys())}")
        offer = json.loads(combined)

    if not offer.get("buyerEmail") and customer_email:
        offer["buyerEmail"] = customer_email

    pdf_bytes = fill_and_merge(offer)

    send_email(
        offer.get("buyerEmail") or customer_email,
        offer.get("buyer1", "Buyer"),
        offer.get("address", "Property"),
        pdf_bytes
    )

    return {"status": "ok", "message": "PDF created and emailed"}


# ── HTTP HANDLER ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            contents = os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else []
        except Exception as e:
            contents = str(e)
        self._json(200, {
            "status": "ok",
            "base_dir": BASE_DIR,
            "main_pdf_exists": os.path.exists(MAIN_PDF),
            "main_pdf_path": MAIN_PDF,
            "cwd": os.getcwd(),
            "dir_contents": contents
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            sig    = self.headers.get("stripe-signature", "")
            if sig and not verify_stripe_signature(body, sig, STRIPE_WHSEC):
                self._json(401, {"error": "Invalid Stripe signature"})
                return
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
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


handler = Handler
