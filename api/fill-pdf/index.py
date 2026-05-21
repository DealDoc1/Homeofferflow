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


def fmt_plain_money(val):
    try:
        if val is None or val == "":
            return ""
        return f"{int(float(val)):,}"
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


def fill_pdf_to_bytes(path, field_values=None, checkbox_values=None):
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(path)
    writer = PdfWriter()
    writer.append(reader)

    for field_name, value in (field_values or {}).items():
        safe_set(writer, field_name, value)

    for field_name, checked in (checkbox_values or {}).items():
        safe_check(writer, field_name, checked)

    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def append_pdf_bytes(main_writer, pdf_bytes):
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(pdf_bytes))
    main_writer.append(reader)


def build_main_contract_maps(s):
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

    survey = s.get("survey", "")
    title_payer = s.get("titlePayer", "seller")
    title_amend = s.get("titleAmendment", "i")
    seller_disc = s.get("sellerDisclosure", "received")
    as_is = s.get("asIs", "yes")

    field_values = {
        "1 PARTIES The parties to this contract are": s.get("seller", ""),
        "Seller and": buyer_name,

        "A LAND Lot": lot_num,
        "Block": block_num,
        "undefined": s.get("subdiv", ""),
        "Addition City of": s.get("city", ""),
        "County of": s.get("county", ""),
        "Texas known as": addr_full,

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
        "following specific repairs and treatments": s.get("repairsText", "") if as_is == "repairs" else "",

        "Within": str(s.get("disclosureDays", "3")) if seller_disc == "notReceived" else "",
        "receipt or the date specified in this paragraph whichever is earlier": str(s.get("surveyDays", "7")),

        "Contract Concerning": addr_full,
        "Contract Concerning_2": addr_full,
        "Contract Concerning_3": addr_full,
        "Contract Concerning_4": addr_full,
        "Address of Property": addr_full,
        "Address of Property_2": addr_full,
        "Addr of Prop": addr_full,

        "Escrow Agent": s.get("titleCompany", ""),
        "Escrow Agent_2": s.get("titleCompany", ""),
        "Escrow Agent_3": s.get("titleCompany", ""),
    }

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

        "1Within": survey == "sellerExisting",
        "2Within": survey == "buyerNew",
        "2 Within": survey == "buyerNew",

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

    return field_values, checkbox_values


def build_financing_maps(s):
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")
    financing = s.get("financing", "")
    loan_amount = s.get("loanAmount", "")

    loan_years = s.get("loanYears", "") or "30"
    interest_rate = s.get("interestRate", "") or ""
    approval_days = s.get("buyerApprovalDays", "") or "21"
    origination = s.get("originationPercent", "") or ""

    fields = {
        "Street Address and City": f"{s.get('address','')}, {s.get('city','')}",
        "Address of Property": addr_full,

        "any financed PMI premium due in full in 1": fmt_plain_money(loan_amount),
        "any financed PMI premium due in full in 2": loan_years,
        "per annum for the first": interest_rate,
        "shown on Buyers Loan Estimate for the loan not to exceed": origination,

        "excluding any financed MIP amortizable monthly for not less": fmt_plain_money(loan_amount),
        "than": loan_years,
        "years with interest not to exceed_2": interest_rate,
        "Charges as shown on Buyers Loan Estimate for the loan not to exceed": origination,

        "excluding any financed Funding Fee amortizable monthly for not less than": fmt_plain_money(loan_amount),
        "years": loan_years,
        "with interest not to exceed": interest_rate,
        "per annum for the first_4": "",
        "Origination Charges as shown on Buyers Loan Estimate for the loan not to exceed": origination,

        "any financed Funding Fee amortizable monthly for not less than": fmt_plain_money(loan_amount),
        "per annum for the first_3": interest_rate,

        "This contract is subject to Buyer obtaining Buyer Approval If Buyer cannot obtain Buyer": True,
        "Text1": approval_days,
        "value of the Property established by the Department of Veterans Affairs": fmt_plain_money(s.get("price", "")),
    }

    checks = {
        "1 Conventional Financing": financing == "conventional",
        "a A first mortgage loan in the principal amount of": financing == "conventional",
        "3 FHA Insured Financing A Section": financing == "fha",
        "4 VA Guaranteed Financing A VA guaranteed loan of not less than": financing == "va",
        "5 USDA Guaranteed Financing A USDAguaranteed loan of not less than": financing == "usda",
        "This contract is subject to Buyer obtaining Buyer Approval If Buyer cannot obtain Buyer": financing in ["conventional", "fha", "va", "usda"],
    }

    return fields, checks


def build_hoa_maps(s):
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")

    fields = {
        "Street Address and City": f"{s.get('address','')}, {s.get('city','')}",
        "Name of Property Owners Association Association and Phone Number": s.get("hoaName", "") or "TBD / See MLS or HOA documents",
        "the Subdivision Information to the Buyer If Seller delivers the Subdivision Information Buyer may terminate": s.get("hoaDeliveryDays", "") or "3",
        "D DEPOSITS FOR RESERVES Buyer shall pay any deposits for reserves required at closing by the Association": fmt_plain_money(s.get("hoaTransferCap", "") or "0"),
    }

    checks = {
        "1 Within": True,
        "undefined": False,
        "3Buyer has received and approved the Subdivision Information before signing the contract Buyer": False,
        "4Buyer does not require delivery of the Subdivision Information": False,
        "does": False,
        "does not require an updated resale certificate If Buyer requires an updated resale certificate Seller at": True,
        "Buyer": False,
        "Seller shall pay the Title Company the cost of obtaining the": True,
    }

    return fields, checks


def build_sale_contingency_maps(s):
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")

    contingency_date = s.get("saleContingencyDate", "") or s.get("closingDate", "")
    day, month, year = split_date(contingency_date)

    fields = {
        "Address of Property": addr_full,
        "Address on or before": s.get("saleContingencyAddress", "") or "Buyer’s current property address TBD",
        "Contingency is not satisfied or waived by Buyer by the above date the contract will terminate": f"{month} {day}".strip(),
        "20": year[-2:] if year else "",
        "terminate automatically and the earnest money will be refunded to Buyer": s.get("saleContingencyWaiverDays", "") or "2",
        "All notices and waivers must be in writing and are": fmt_plain_money(s.get("saleContingencyAdditionalEarnest", "") or "0"),
    }

    return fields, {}


def build_backup_maps(s):
    addr_full = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")

    first_contract_date = s.get("backupFirstContractDate", "")
    exp_date = s.get("backupExpirationDate", "") or s.get("closingDate", "")

    d1, m1, y1 = split_date(first_contract_date)
    d2, m2, y2 = split_date(exp_date)

    fields = {
        "Address of Property": addr_full,
        "Text1": fmt_plain_money(s.get("backupAdditionalEarnest", "") or "0"),
        "Text1 1": fmt_plain_money(s.get("backupAdditionalOptionFee", "") or "0"),
        "Text1 2": s.get("backupAdditionalDays", "") or "3",
        "Except as provided by this Addendum neither party is required to perform under the": f"{m1} {d1}".strip(),
        "20": y1[-2:] if y1 else "",
        "the BackUp Contract terminates and the earnest money will be refunded to Buyer  Seller must": f"{m2} {d2}".strip(),
        "20_2": y2[-2:] if y2 else "",
    }

    return fields, {}


def fill_and_merge(offer):
    from pypdf import PdfReader, PdfWriter

    s = offer or {}

    financing = s.get("financing", "")
    has_loan = financing in ["conventional", "fha", "va", "usda"]
    has_hoa = s.get("hoa") in ["yes", "unknown"]
    has_sale_cont = s.get("saleContingency") == "yes"
    has_backup = s.get("backupOffer") == "yes"

    main_fields, main_checks = build_main_contract_maps(s)

    main_bytes = fill_pdf_to_bytes(MAIN_PDF, main_fields, main_checks)

    final_writer = PdfWriter()
    final_writer.append(PdfReader(BytesIO(main_bytes)))

    addenda_info = []

    if has_loan:
        f_fields, f_checks = build_financing_maps(s)
        f_bytes = fill_pdf_to_bytes(FINANCING_PDF, f_fields, f_checks)
        append_pdf_bytes(final_writer, f_bytes)
        addenda_info.append(("financing", FINANCING_PDF))

    if has_hoa:
        h_fields, h_checks = build_hoa_maps(s)
        h_bytes = fill_pdf_to_bytes(HOA_PDF, h_fields, h_checks)
        append_pdf_bytes(final_writer, h_bytes)
        addenda_info.append(("hoa", HOA_PDF))

    if has_sale_cont:
        sc_fields, sc_checks = build_sale_contingency_maps(s)
        sc_bytes = fill_pdf_to_bytes(SALE_CONT_PDF, sc_fields, sc_checks)
        append_pdf_bytes(final_writer, sc_bytes)
        addenda_info.append(("sale_contingency", SALE_CONT_PDF))

    if has_backup:
        b_fields, b_checks = build_backup_maps(s)
        b_bytes = fill_pdf_to_bytes(BACKUP_PDF, b_fields, b_checks)
        append_pdf_bytes(final_writer, b_bytes)
        addenda_info.append(("backup", BACKUP_PDF))

    buf = BytesIO()
    final_writer.write(buf)
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
        "signwell": signwell_result,
        "addenda": addenda_info
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
