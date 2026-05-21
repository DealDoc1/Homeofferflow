import json
import os
import base64
import hashlib
import hmac
import httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
SIGNWELL_API_KEY = os.environ.get("SIGNWELL_API_KEY", "")

FROM_EMAIL = "offers@homeofferflow.com"
SUPPORT_EMAIL = "support@homeofferflow.com"
BASE_URL = "https://www.homeofferflow.com"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAIN_PDF = os.path.join(BASE_DIR, "20-18_0.pdf")
FINANCING_PDF = os.path.join(BASE_DIR, "third_party_financing_addendum.pdf")
HOA_PDF = os.path.join(BASE_DIR, "hoa_addendum.pdf")
SALE_CONT_PDF = os.path.join(BASE_DIR, "sale_of_other_property_addendum.pdf")
BACKUP_PDF = os.path.join(BASE_DIR, "back_up_contract_addendum.pdf")


def fmt_money(val):
    try:
        if val is None or val == "":
            return ""
        return f"${int(float(val)):,}"
    except Exception:
        return str(val) if val else ""


def fmt_date(val):
    if not val:
        return ""
    try:
        from datetime import datetime
        d = datetime.strptime(val, "%Y-%m-%d")
        return d.strftime("%B %d, %Y").replace(" 0", " ")
    except Exception:
        return val


def split_date(val):
    if not val:
        return "", "", ""
    try:
        from datetime import datetime
        d = datetime.strptime(val, "%Y-%m-%d")
        return str(d.day), d.strftime("%B"), str(d.year)
    except Exception:
        return "", "", ""


def parse_lot_block(lot_str):
    import re
    lot_num = ""
    block_num = ""

    if not lot_str:
        return lot_num, block_num

    lot_m = re.search(r"lot\s*([A-Za-z0-9\-]+)", lot_str, re.I)
    blk_m = re.search(r"block\s*([A-Za-z0-9\-]+)", lot_str, re.I)

    if lot_m:
        lot_num = lot_m.group(1)

    if blk_m:
        block_num = blk_m.group(1)

    return lot_num, block_num


def verify_stripe_signature(body_bytes, sig_header, secret):
    if not secret:
        return True

    try:
        parts = {}
        for item in sig_header.split(","):
            k, v = item.split("=", 1)
            parts.setdefault(k, []).append(v)

        timestamp = parts.get("t", [""])[0]
        signatures = parts.get("v1", [])

        signed_payload = timestamp.encode() + b"." + body_bytes
        expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()

        return any(hmac.compare_digest(expected, sig) for sig in signatures)
    except Exception:
        return False


def safe_set(writer, field_name, value):
    if value is None:
        value = ""
    try:
        for page in writer.pages:
            writer.update_page_form_field_values(page, {field_name: str(value)})
    except Exception:
        pass


def safe_check(writer, field_name, checked):
    try:
        for page in writer.pages:
            writer.update_page_form_field_values(page, {field_name: "/Yes" if checked else "/Off"})
    except Exception:
        pass


def get_pdf_fields(path):
    from pypdf import PdfReader
    reader = PdfReader(path)
    out = {}
    fields = reader.get_fields()
    if fields:
        for k, v in fields.items():
            out[k] = {
                "value": str(v.get("/V", "")),
                "type": str(v.get("/FT", ""))
            }
    return out


def fill_and_merge(offer):
    from pypdf import PdfReader, PdfWriter

    s = offer or {}

    lot_num, block_num = parse_lot_block(s.get("lot", ""))
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")

    try:
        price = float(s.get("price", 0) or 0)
        loan = float(s.get("loanAmount", 0) or 0)
        cash = price - loan
    except Exception:
        price = 0
        loan = 0
        cash = 0

    buyer_name = s.get("buyer1", "")
    if s.get("buyer2"):
        buyer_name += f" and {s.get('buyer2')}"

    financing = s.get("financing", "")
    has_loan = financing in ["conventional", "fha", "va", "usda"]
    has_hoa = s.get("hoa") in ["yes", "unknown"]
    has_sale_cont = s.get("saleContingency") == "yes"
    has_backup = s.get("backupOffer") == "yes"
    has_mud = s.get("mud") in ["yes", "unknown"]

    reader = PdfReader(MAIN_PDF)
    writer = PdfWriter()
    writer.append(reader)

    field_values = {
        "1 PARTIES The parties to this contract are": s.get("seller", ""),
        "Seller and": buyer_name,

        "A LAND Lot": lot_num,
        "Block": block_num,
        "undefined": s.get("subdiv", ""),
        "Addition City of": s.get("city", ""),
        "County of": s.get("county", ""),
        "Texas known as": addr_full,

        # IMPORTANT FIX:
        # undefined_2 was wrong. It hits exclusions area.
        "be removed prior to delivery of possession": "",
        "undefined_2": "",
        "undefined_3": fmt_money(cash) if has_loan else fmt_money(price),
        "undefined_4": fmt_money(loan) if has_loan else "",
        "undefined_5": fmt_money(price),

        "as earnest money to": fmt_money(s.get("earnest")),
        "as earnest money to 2": fmt_money(s.get("earnest")),
        "earnest money of": fmt_money(s.get("earnest")),

        "acknowledged by Seller and Buyers agreement to pay Seller": fmt_money(s.get("optionFee")),
        "acknowledged by Seller and Buyers agreement to pay Seller 1": str(s.get("optionDays", "")),
        "acknowledged by Seller and Buyers agreement to pay Seller2": fmt_money(s.get("optionFee")),
        "Option Fee in the form of": fmt_money(s.get("optionFee")),

        "insurance Title Policy issued by": s.get("titleCompany", ""),
        "A The closing of the sale will be on or before": fmt_date(s.get("closingDate")),
        "20": "",

        "when mailed to": s.get("buyerMailAddr", ""),
        "Phone 51": s.get("buyerPhone", ""),
        "AC1": s.get("buyerEmail", ""),

        "Associates Name": s.get("agentName", "") if s.get("hasBuyerAgent") == "yes" else "",
        "License No": s.get("agentLicense", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Associates Email Address": s.get("agentEmail", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Phone": s.get("agentPhone", "") if s.get("hasBuyerAgent") == "yes" else "",
        "Other Broker Firm": s.get("agentBrokerage", "") if s.get("hasBuyerAgent") == "yes" else "",

        "Buyers Expenses as allowed by the lender": fmt_money(s.get("concessionAmount", "")) if s.get("wantsConcessions") == "yes" else "",

        "Commitment other than items 6A1 through 9 above or which prohibit the following use": s.get("intendedUse", ""),
        "following specific repairs and treatments": s.get("repairsText", "") if s.get("asIs") == "repairs" else "",

        "Within": str(s.get("disclosureDays", "3")) if s.get("sellerDisclosure") == "notReceived" else "",
        "receipt or the date specified in this paragraph whichever is earlier": str(s.get("surveyDays", "7")),

        "Contract Concerning": addr_full,
        "Contract Concerning_2": addr_full,
        "Contract Concerning_3": addr_full,
        "Contract Concerning_4": addr_full,
        "Address of Property": addr_full,
        "Address of Property_2": addr_full,
        "Addr of Prop": addr_full,
    }

    for field_name, value in field_values.items():
        safe_set(writer, field_name, value)

    survey = s.get("survey", "")
    title_payer = s.get("titlePayer", "seller")
    title_amend = s.get("titleAmendment", "i")
    seller_disc = s.get("sellerDisclosure", "received")
    as_is = s.get("asIs", "yes")

    checkbox_values = {
        "Third Party Financing Addendum": has_loan,
        "B Sum of all financing described in the attached": has_loan,

        "A TITLE POLICY Seller shall furnish to Buyer at": title_payer == "seller",
        "Sellers": title_payer == "seller",
        "Seller": title_payer == "buyer",

        "i will not be amended or deleted from the title policy or": title_amend == "i",
        "ii will be amended to read shortages in area at the expense of": title_amend in ["ii_buyer", "ii_seller"],
        "Buyer": title_amend == "ii_buyer",

        "is": has_hoa,
        "is not": not has_hoa,

        # IMPORTANT FIX:
        # actual checkbox is 2Within, not 2 Within.
        "1Within": survey == "sellerExisting",
        "2Within": survey == "buyerNew",
        "2 Within": survey == "buyerNew",
        "3Within": survey == "noSurvey",

        "Within one": seller_disc == "received",
        "Within two": seller_disc == "notReceived",
        "Within three": seller_disc == "exempt",

        "1 Buyer accepts the Property As Is": as_is == "yes",
        "As Is": as_is == "yes",
        "2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the": as_is == "repairs",
        "As Is except": as_is == "repairs",

        "upon": s.get("possession") == "funding",

        "Addendum for Property Subject to": has_hoa,
        "Addendum for Sale of Other Property by": has_sale_cont,
        "Addendum for BackUp Contract": has_backup,
        "PID": has_mud,

        "Buyer only": s.get("hasBuyerAgent") == "yes",
    }

    for field_name, checked in checkbox_values.items():
        safe_check(writer, field_name, checked)

    addenda_info = []

    if has_loan:
        addenda_info.append((FINANCING_PDF, 2, True))

    if has_hoa:
        addenda_info.append((HOA_PDF, 1, False))

    if has_sale_cont:
        addenda_info.append((SALE_CONT_PDF, 1, False))

    if has_backup:
        addenda_info.append((BACKUP_PDF, 2, True))

    for path, pages, has_init in addenda_info:
        try:
            writer.append(PdfReader(path))
        except Exception as e:
            print(f"Could not append addendum {path}: {e}")

    buf = BytesIO()
    writer.write(buf)

    return buf.getvalue(), addenda_info


def send_confirmation_email(to_email, buyer_name, addr, pdf_bytes=None):
    if not RESEND_API_KEY:
        raise Exception("Missing RESEND_API_KEY")

    safe_addr = (addr or "Property").replace(" ", "_").replace("/", "_")

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "bcc": [SUPPORT_EMAIL],
        "subject": f"Your Filled Offer PDF — {addr}",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2>Your HomeOfferFlow offer PDF is ready, {buyer_name}.</h2>
          <p>Your payment was successful and your filled offer for <strong>{addr}</strong> is attached.</p>
          <p><strong>Review every field carefully.</strong> This version is for testing PDF field accuracy before SignWell is re-enabled.</p>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.9rem;">
            HomeOfferFlow is not a law firm and does not provide legal advice.
          </p>
        </div>
        """
    }

    if pdf_bytes:
        payload["attachments"] = [
            {
                "filename": f"HomeOfferFlow_Offer_{safe_addr}.pdf",
                "content": base64.b64encode(pdf_bytes).decode(),
                "content_type": "application/pdf"
            }
        ]

    resp = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30
    )

    if resp.status_code not in [200, 201, 202]:
        raise Exception(f"Resend error {resp.status_code}: {resp.text[:1000]}")

    return resp.json()


def handle_stripe_checkout(event):
    session = event.get("data", {}).get("object", {})

    customer_email = (
        session.get("customer_email")
        or session.get("customer_details", {}).get("email")
        or ""
    )

    metadata = session.get("metadata", {}) or {}

    if "offer_data" in metadata:
        offer = json.loads(metadata["offer_data"])
    else:
        offer_parts = int(metadata.get("offer_parts", 0) or 0)
        combined = ""

        for i in range(offer_parts):
            combined += metadata.get(f"offer_{i}", "")

        if not combined:
            raise Exception("No offer data found in Stripe session metadata")

        offer = json.loads(combined)

    if customer_email:
        offer["_paymentEmail"] = customer_email

    if not offer.get("buyerEmail") and customer_email:
        offer["buyerEmail"] = customer_email

    pdf_bytes, addenda_info = fill_and_merge(offer)

    signwell_result = {
        "skipped": "SignWell temporarily disabled while testing PDF field accuracy"
    }

    send_confirmation_email(
        offer.get("buyerEmail") or customer_email,
        offer.get("buyer1", "Buyer"),
        offer.get("address", "Property"),
        pdf_bytes
    )

    return {
        "status": "ok",
        "message": "PDF created and emailed for review",
        "signwell": signwell_result
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            if "debug" in query:
                self._json(200, {
                    "main_fields": get_pdf_fields(MAIN_PDF),
                    "financing_fields": get_pdf_fields(FINANCING_PDF) if os.path.exists(FINANCING_PDF) else {},
                    "hoa_fields": get_pdf_fields(HOA_PDF) if os.path.exists(HOA_PDF) else {},
                    "sale_cont_fields": get_pdf_fields(SALE_CONT_PDF) if os.path.exists(SALE_CONT_PDF) else {},
                    "backup_fields": get_pdf_fields(BACKUP_PDF) if os.path.exists(BACKUP_PDF) else {},
                })
                return

            self._json(200, {
                "status": "fill-pdf live",
                "debug_fields_url": "/api/fill-pdf?debug=1",
                "main_pdf_exists": os.path.exists(MAIN_PDF),
                "financing_pdf_exists": os.path.exists(FINANCING_PDF),
                "hoa_pdf_exists": os.path.exists(HOA_PDF),
                "sale_cont_pdf_exists": os.path.exists(SALE_CONT_PDF),
                "backup_pdf_exists": os.path.exists(BACKUP_PDF),
                "signwell_key_set": bool(SIGNWELL_API_KEY),
                "resend_key_set": bool(RESEND_API_KEY),
                "stripe_webhook_secret_set": bool(STRIPE_WHSEC)
            })

        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            sig_header = self.headers.get("stripe-signature", "")

            if sig_header:
                if not verify_stripe_signature(body, sig_header, STRIPE_WHSEC):
                    self._json(401, {"error": "Invalid Stripe signature"})
                    return

            event = json.loads(body.decode("utf-8"))

            if event.get("type") == "checkout.session.completed":
                result = handle_stripe_checkout(event)
                self._json(200, result)
                return

            self._json(200, {
                "status": "ignored",
                "event_type": event.get("type")
            })

        except Exception as e:
            print("ERROR:", str(e))
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


handler = Handler
