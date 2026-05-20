# force redeploy 2026-05-20
import json
import os
import base64
import hashlib
import hmac
import httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
SIGNWELL_API_KEY = os.environ.get("SIGNWELL_API_KEY", "")

FROM_EMAIL = "offers@homeofferflow.com"
SUPPORT_EMAIL = "support@homeofferflow.com"
BASE_URL = "https://homeofferflow.com"

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

    has_loan = s.get("financing") in ["conventional", "fha", "va", "usda"]
    has_hoa = s.get("hoa") in ["yes", "unknown"]
    has_sale_cont = s.get("saleContingency") == "yes"
    has_backup = s.get("backupOffer") == "yes"
    has_mud = s.get("mud") in ["yes", "unknown"]

    field_values = {
        "1 PARTIES The parties to this contract are": s.get("seller", ""),
        "Seller and": buyer_name,

        "A LAND Lot": lot_num,
        "Block": block_num,
        "undefined": s.get("subdiv", ""),
        "Addition City of": s.get("city", ""),
        "County of": s.get("county", ""),
        "Texas known as": addr_full,

        "undefined_2": fmt_money(cash) if has_loan else fmt_money(price),
        "undefined_4": fmt_money(loan) if has_loan else "",
        "undefined_5": fmt_money(price),

        "as earnest money to": fmt_money(s.get("earnest")),
        "as earnest money to 2": fmt_money(s.get("earnest")),

        "acknowledged by Seller and Buyers agreement to pay Seller": fmt_money(s.get("optionFee")),
        "acknowledged by Seller and Buyers agreement to pay Seller 1": str(s.get("optionDays", "")),
        "acknowledged by Seller and Buyers agreement to pay Seller2": fmt_money(s.get("optionFee")),
        "Option Fee in the form of": fmt_money(s.get("optionFee")),

        "insurance Title Policy issued by": s.get("titleCompany", ""),
        "A The closing of the sale will be on or before": fmt_date(s.get("closingDate")),

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

    reader = PdfReader(MAIN_PDF)
    writer = PdfWriter()
    writer.append(reader)

    for page in writer.pages:
        writer.update_page_form_field_values(page, field_values)

    checkbox_map = {
        "Third Party Financing Addendum": has_loan,

        "1Within": s.get("survey") == "sellerExisting",
        "2 Within": s.get("survey") == "buyerNew",
        "3Within": s.get("survey") == "noSurvey",

        "A TITLE POLICY Seller shall furnish to Buyer at": s.get("titlePayer", "seller") == "seller",
        "Sellers": s.get("titlePayer", "seller") == "seller",
        "Seller": s.get("titlePayer") == "buyer",

        "i will not be amended or deleted from the title policy or": s.get("titleAmendment", "i") == "i",
        "ii will be amended to read shortages in area at the expense of": s.get("titleAmendment") in ["ii_buyer", "ii_seller"],
        "Buyer": s.get("titleAmendment") == "ii_buyer",

        "is": has_hoa,
        "is not": not has_hoa,

        "1 Buyer accepts the Property As Is": s.get("asIs", "yes") == "yes",
        "2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the": s.get("asIs") == "repairs",

        "upon": s.get("possession") == "funding",

        "Addendum for Property Subject to": has_hoa,
        "Addendum for Sale of Other Property by": has_sale_cont,
        "Addendum for BackUp Contract": has_backup,
        "PID": has_mud,

        "Within one": s.get("sellerDisclosure", "received") == "received",
        "Within two": s.get("sellerDisclosure") == "notReceived",
        "Within three": s.get("sellerDisclosure") == "exempt",

        "Buyer only": s.get("hasBuyerAgent") == "yes",
    }

    for field_name, should_check in checkbox_map.items():
        try:
            for page in writer.pages:
                writer.update_page_form_field_values(page, {field_name: "/Yes" if should_check else "/Off"})
        except Exception:
            pass

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


def build_signwell_payload(pdf_bytes, offer, addenda_info):
    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    buyer1_name = offer.get("buyer1") or "Buyer"
    buyer1_email = offer.get("buyerEmail") or offer.get("_paymentEmail") or ""

    buyer2_name = offer.get("buyer2", "").strip()
    buyer2_email = offer.get("buyer2Email", "").strip()

    addr = offer.get("address") or "Property"

    signers = [
        {
            "id": "1",
            "name": buyer1_name,
            "email": buyer1_email,
            "order": 1
        }
    ]

    if buyer2_name and buyer2_email:
        signers.append({
            "id": "2",
            "name": buyer2_name,
            "email": buyer2_email,
            "order": 2
        })

    return {
        "test_mode": False,
        "name": f"Offer — {addr}",
        "subject": f"Please sign your offer: {addr}",
        "message": f"Your HomeOfferFlow offer for {addr} is ready to sign. Please review and sign below.",
        "files": [
            {
                "name": f"HomeOfferFlow_Offer_{addr.replace(' ', '_')}.pdf",
                "file_base64": pdf_b64
            }
        ],
        "recipients": signers,
        "send_email": True,
        "callback_url": f"{BASE_URL}/api/fill-pdf"
    }


def send_to_signwell(pdf_bytes, offer, addenda_info):
    if not SIGNWELL_API_KEY:
        raise Exception("Missing SIGNWELL_API_KEY")

    payload = build_signwell_payload(pdf_bytes, offer, addenda_info)

    resp = httpx.post(
        "https://www.signwell.com/api/v1/documents/",
        headers={
            "X-Api-Key": SIGNWELL_API_KEY,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    if resp.status_code not in [200, 201]:
        raise Exception(f"SignWell error {resp.status_code}: {resp.text[:1000]}")

    return resp.json()


def send_confirmation_email(to_email, buyer_name, addr):
    if not RESEND_API_KEY:
        raise Exception("Missing RESEND_API_KEY")

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "bcc": [SUPPORT_EMAIL],
        "subject": f"Your Offer is Being Prepared — {addr}",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2>Your HomeOfferFlow offer is being prepared, {buyer_name}.</h2>
          <p>Your payment was successful and your offer for <strong>{addr}</strong> is being sent for signature.</p>
          <p>Please watch for a separate signing email from HomeOfferFlow or SignWell.</p>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.9rem;">
            HomeOfferFlow is not a law firm and does not provide legal advice.
          </p>
        </div>
        """
    }

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

    signwell_result = send_to_signwell(pdf_bytes, offer, addenda_info)

    send_confirmation_email(
        offer.get("buyerEmail") or customer_email,
        offer.get("buyer1", "Buyer"),
        offer.get("address", "Property")
    )

    return {
        "status": "ok",
        "message": "PDF created and sent to SignWell",
        "signwell": signwell_result
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._json(200, {
            "status": "fill-pdf live",
            "main_pdf_exists": os.path.exists(MAIN_PDF),
            "signwell_key_set": bool(SIGNWELL_API_KEY),
            "resend_key_set": bool(RESEND_API_KEY),
            "stripe_webhook_secret_set": bool(STRIPE_WHSEC)
        })

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
            self._json(500, {
                "error": str(e)
            })

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
