import json, os, base64, hashlib, hmac, httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

FROM_EMAIL = "offers@homeofferflow.com"
SUPPORT_EMAIL = "support@homeofferflow.com"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAIN_PDF = os.path.join(BASE_DIR, "20-18_0.pdf")
FINANCING_PDF = os.path.join(BASE_DIR, "third_party_financing_addendum.pdf")
HOA_PDF = os.path.join(BASE_DIR, "hoa_addendum.pdf")
SALE_CONT_PDF = os.path.join(BASE_DIR, "sale_of_other_property_addendum.pdf")
BACKUP_PDF = os.path.join(BASE_DIR, "back_up_contract_addendum.pdf")


def fmt_money(v):
    try:
        if v in [None, ""]:
            return ""
        return f"{int(float(v)):,}"
    except Exception:
        return str(v or "")


def split_date(v):
    if not v:
        return "", ""
    try:
        from datetime import datetime
        d = datetime.strptime(v, "%Y-%m-%d")
        return d.strftime("%B %d").replace(" 0", " "), str(d.year)[-2:]
    except Exception:
        return str(v), ""


def parse_lot_block(v):
    import re
    lot = ""
    block = ""
    if not v:
        return lot, block
    m = re.search(r"lot\s*([A-Za-z0-9\-]+)", v, re.I)
    if m:
        lot = m.group(1)
    m = re.search(r"block\s*([A-Za-z0-9\-]+)", v, re.I)
    if m:
        block = m.group(1)
    return lot, block


def verify_stripe_signature(body, sig_header, secret):
    if not secret:
        return True
    try:
        parts = {}
        for item in sig_header.split(","):
            k, v = item.split("=", 1)
            parts.setdefault(k, []).append(v)

        timestamp = parts.get("t", [""])[0]
        signatures = parts.get("v1", [])
        expected = hmac.new(
            secret.encode(),
            timestamp.encode() + b"." + body,
            hashlib.sha256
        ).hexdigest()

        return any(hmac.compare_digest(expected, s) for s in signatures)
    except Exception:
        return False


def text(c, x, y, value, size=9):
    if value in [None, ""]:
        return
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", size)
    c.drawString(x, y, str(value))


def money(c, x, y, value, size=9):
    if value in [None, ""]:
        return
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", size)
    c.drawRightString(x, y, fmt_money(value))


def check(c, x, y):
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "X")


def overlay_page(width=612, height=792):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))

    # Prevent blank overlay PDFs from having zero pages.
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica", 1)
    c.drawString(0, 0, ".")

    c.setFillColorRGB(0, 0, 0)
    return buf, c


def merge_overlay(page, buf):
    buf.seek(0)
    overlay = PdfReader(buf)
    if len(overlay.pages) > 0:
        page.merge_page(overlay.pages[0])


def stamp_main_contract(pdf_bytes, offer):
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    s = offer or {}
    lot, block = parse_lot_block(s.get("lot", ""))
    addr = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}".strip(", ")

    buyer = s.get("buyer1", "")
    if s.get("buyer2"):
        buyer += f" and {s.get('buyer2')}"

    price = float(s.get("price", 0) or 0)
    loan = float(s.get("loanAmount", 0) or 0)
    cash = price - loan

    financing = s.get("financing", "")
    has_loan = financing in ["conventional", "fha", "va", "usda"]
    has_hoa = s.get("hoa") in ["yes", "unknown"]

    closing_md, closing_yy = split_date(s.get("closingDate"))

    for i, page in enumerate(reader.pages):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        buf, c = overlay_page(width, height)

        if i == 0:
            text(c, 242, 642, s.get("seller", ""), 9)
            text(c, 395, 642, buyer, 9)

            text(c, 118, 562, lot, 9)
            text(c, 190, 562, block, 9)
            text(c, 260, 562, s.get("subdiv", ""), 9)
            text(c, 152, 548, s.get("city", ""), 9)
            text(c, 288, 548, s.get("county", ""), 9)
            text(c, 138, 533, addr, 9)

            money(c, 557, 319, cash if has_loan else price, 9)

            if has_loan:
                check(c, 382, 286)
                money(c, 557, 286, loan, 9)

            money(c, 557, 262, price, 9)

        elif i == 1:
            escrow = s.get("escrowAgent") or s.get("titleCompany", "")
            escrow_addr = s.get("escrowAddress") or s.get("titleAddress", "")

            text(c, 258, 711, escrow, 9)
            text(c, 142, 696, escrow_addr, 9)
            money(c, 355, 696, s.get("earnest"), 9)
            money(c, 520, 696, s.get("optionFee"), 9)

            text(c, 264, 476, s.get("optionDays", "7"), 9)

            if s.get("titlePayer", "seller") == "seller":
                check(c, 341, 323)
            else:
                check(c, 395, 323)

            text(c, 292, 307, s.get("titleCompany", ""), 9)

            if s.get("titleAmendment", "i") == "i":
                check(c, 86, 177)
            else:
                check(c, 86, 158)
                if s.get("titleAmendment") == "ii_buyer":
                    check(c, 417, 158)
                else:
                    check(c, 470, 158)

        elif i == 2:
            survey = s.get("survey", "sellerExisting")
            survey_days = s.get("surveyDays", "7")

            if survey == "sellerExisting":
                check(c, 54, 708)
                text(c, 96, 708, survey_days, 9)
                if s.get("surveyIfRejectedPaidBy", "buyer") == "seller":
                    check(c, 461, 621)
                else:
                    check(c, 515, 621)
            elif survey == "buyerNew":
                check(c, 54, 604)
                text(c, 96, 604, survey_days, 9)
            elif survey == "sellerNew":
                check(c, 54, 556)
                text(c, 96, 556, survey_days, 9)

            text(c, 438, 423, s.get("intendedUse", ""), 9)
            text(c, 361, 394, s.get("objectionDays", ""), 9)

            if has_hoa:
                check(c, 355, 288)
            else:
                check(c, 382, 288)

        elif i == 3:
            disc = s.get("sellerDisclosure", "notReceived")
            if disc == "received":
                check(c, 52, 276)
            elif disc == "notReceived":
                check(c, 52, 254)
                text(c, 219, 254, s.get("disclosureDays", "3"), 9)
            elif disc == "exempt":
                check(c, 52, 211)

        elif i == 4:
            if s.get("asIs", "yes") == "repairs":
                check(c, 52, 731)
                text(c, 96, 697, s.get("repairsText", ""), 8)
            else:
                check(c, 52, 751)

            text(c, 445, 413, closing_md, 9)
            text(c, 538, 413, closing_yy, 9)

        elif i == 5:
            if s.get("possession", "funding") == "funding":
                check(c, 414, 715)
            else:
                check(c, 510, 715)

            if s.get("wantsConcessions") == "yes":
                check(c, 394, 351)
                money(c, 514, 337, s.get("concessionAmount"), 9)

        elif i == 7:
            text(c, 120, 205, s.get("buyerMailAddr", addr), 8)
            text(c, 90, 174, s.get("buyerPhone", ""), 8)
            text(c, 105, 144, s.get("buyerEmail", ""), 8)

            if has_loan:
                check(c, 52, 669)
            if has_hoa:
                check(c, 52, 621)
            if s.get("saleContingency") == "yes":
                check(c, 52, 572)
            if s.get("backupOffer") == "yes":
                check(c, 52, 536)
            if s.get("mud") in ["yes", "unknown"]:
                check(c, 366, 567)

        elif i == 10:
            escrow = s.get("escrowAgent") or s.get("titleCompany", "")
            money(c, 126, 147, s.get("earnest"), 9)
            text(c, 70, 117, escrow, 8)
            money(c, 126, 73, s.get("optionFee"), 9)
            text(c, 70, 44, escrow, 8)

        c.save()
        merge_overlay(page, buf)
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def stamp_financing_addendum(path, offer):
    reader = PdfReader(path)
    writer = PdfWriter()
    s = offer or {}

    addr = f"{s.get('address','')}, {s.get('city','')}"
    financing = s.get("financing", "")
    loan = s.get("loanAmount", "")
    years = s.get("loanYears", "30")
    rate = s.get("interestRate", "")
    approval_days = s.get("buyerApprovalDays", "21")

    for i, page in enumerate(reader.pages):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        buf, c = overlay_page(width, height)

        if i == 0:
            text(c, 230, 623, addr, 9)

            if financing == "conventional":
                check(c, 52, 547)
                check(c, 88, 531)
                money(c, 392, 522, loan, 9)
                text(c, 277, 503, years, 9)
                text(c, 443, 503, rate, 9)

            elif financing == "fha":
                check(c, 52, 397)
                money(c, 325, 374, loan, 9)
                text(c, 170, 354, years, 9)
                text(c, 302, 354, rate, 9)

            elif financing == "va":
                check(c, 52, 329)
                money(c, 405, 321, loan, 9)
                text(c, 232, 302, years, 9)
                text(c, 347, 302, rate, 9)

            elif financing == "usda":
                check(c, 52, 263)
                money(c, 414, 254, loan, 9)
                text(c, 222, 236, years, 9)
                text(c, 345, 236, rate, 9)

        elif i == 1:
            text(c, 230, 88, f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}", 8)
            check(c, 52, 718)
            text(c, 307, 710, approval_days, 9)

        c.save()
        merge_overlay(page, buf)
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def stamp_hoa_addendum(path, offer):
    reader = PdfReader(path)
    writer = PdfWriter()
    s = offer or {}

    for i, page in enumerate(reader.pages):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        buf, c = overlay_page(width, height)

        if i == 0:
            text(c, 190, 666, f"{s.get('address','')}, {s.get('city','')}", 9)
            text(c, 210, 644, s.get("hoaName", "TBD"), 9)
            check(c, 52, 589)
            text(c, 102, 589, s.get("hoaDeliveryDays", "3"), 9)
            money(c, 470, 327, s.get("hoaTransferCap", "0"), 9)

            if s.get("hoaInfoPayer", "seller") == "buyer":
                check(c, 399, 246)
            else:
                check(c, 448, 246)

        c.save()
        merge_overlay(page, buf)
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def stamp_sale_contingency(path, offer):
    reader = PdfReader(path)
    writer = PdfWriter()
    s = offer or {}

    md, yy = split_date(s.get("saleContingencyDate") or s.get("closingDate"))
    addr = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"

    for i, page in enumerate(reader.pages):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        buf, c = overlay_page(width, height)

        if i == 0:
            text(c, 200, 648, addr, 9)
            text(c, 135, 560, s.get("saleContingencyAddress", ""), 9)
            text(c, 315, 550, md, 9)
            text(c, 410, 550, yy, 9)
            text(c, 251, 469, s.get("saleContingencyWaiverDays", ""), 9)
            money(c, 377, 397, s.get("saleContingencyAdditionalEarnest", ""), 9)

        c.save()
        merge_overlay(page, buf)
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def stamp_backup(path, offer):
    reader = PdfReader(path)
    writer = PdfWriter()
    s = offer or {}

    first_md, first_yy = split_date(s.get("backupFirstContractDate"))
    exp_md, exp_yy = split_date(s.get("backupExpirationDate") or s.get("closingDate"))
    addr = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"

    for i, page in enumerate(reader.pages):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        buf, c = overlay_page(width, height)

        if i == 0:
            text(c, 210, 666, addr, 9)
            money(c, 256, 555, s.get("backupAdditionalEarnest", ""), 9)
            money(c, 434, 555, s.get("backupAdditionalOptionFee", ""), 9)
            text(c, 287, 537, s.get("backupAdditionalDays", ""), 9)
            text(c, 340, 284, first_md, 9)
            text(c, 420, 284, first_yy, 9)
            text(c, 330, 234, exp_md, 9)
            text(c, 410, 234, exp_yy, 9)

        c.save()
        merge_overlay(page, buf)
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def fill_and_merge(offer):
    s = offer or {}
    final_writer = PdfWriter()

    main_stamped = stamp_main_contract(open(MAIN_PDF, "rb").read(), s)
    final_writer.append(PdfReader(BytesIO(main_stamped)))

    if s.get("financing") in ["conventional", "fha", "va", "usda"]:
        final_writer.append(PdfReader(BytesIO(stamp_financing_addendum(FINANCING_PDF, s))))

    if s.get("hoa") in ["yes", "unknown"]:
        final_writer.append(PdfReader(BytesIO(stamp_hoa_addendum(HOA_PDF, s))))

    if s.get("saleContingency") == "yes":
        final_writer.append(PdfReader(BytesIO(stamp_sale_contingency(SALE_CONT_PDF, s))))

    if s.get("backupOffer") == "yes":
        final_writer.append(PdfReader(BytesIO(stamp_backup(BACKUP_PDF, s))))

    out = BytesIO()
    final_writer.write(out)
    return out.getvalue(), []


def send_confirmation_email(to_email, buyer_name, addr, pdf_bytes=None):
    if not RESEND_API_KEY:
        raise Exception("Missing RESEND_API_KEY")

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "bcc": [SUPPORT_EMAIL],
        "subject": f"Your Filled Offer PDF — {addr}",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <h2>Your HomeOfferFlow offer PDF is ready, {buyer_name}.</h2>
          <p>Your payment was successful and your filled offer for <strong>{addr}</strong> is attached.</p>
          <p><strong>Review every field carefully.</strong></p>
          <p style="background:#fff3cd;padding:1rem;border-radius:8px;font-size:0.9rem;">
            HomeOfferFlow is not a law firm and does not provide legal advice.
          </p>
        </div>
        """
    }

    if pdf_bytes:
        safe_addr = (addr or "Property").replace(" ", "_").replace("/", "_")
        payload["attachments"] = [{
            "filename": f"HomeOfferFlow_Offer_{safe_addr}.pdf",
            "content": base64.b64encode(pdf_bytes).decode(),
            "content_type": "application/pdf"
        }]

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
        parts = int(metadata.get("offer_parts", 0) or 0)
        combined = "".join(metadata.get(f"offer_{i}", "") for i in range(parts))

        if not combined:
            raise Exception("No offer data found in Stripe session metadata")

        offer = json.loads(combined)

    if not offer.get("buyerEmail") and customer_email:
        offer["buyerEmail"] = customer_email

    pdf_bytes, _ = fill_and_merge(offer)

    send_confirmation_email(
        offer.get("buyerEmail") or customer_email,
        offer.get("buyer1", "Buyer"),
        offer.get("address", "Property"),
        pdf_bytes
    )

    return {"status": "ok", "message": "Stamped PDF created and emailed"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._json(200, {
            "status": "stamped fill-pdf live v2",
            "main_pdf_exists": os.path.exists(MAIN_PDF),
            "financing_pdf_exists": os.path.exists(FINANCING_PDF),
            "hoa_pdf_exists": os.path.exists(HOA_PDF),
            "sale_cont_pdf_exists": os.path.exists(SALE_CONT_PDF),
            "backup_pdf_exists": os.path.exists(BACKUP_PDF),
            "resend_key_set": bool(RESEND_API_KEY),
            "stripe_webhook_secret_set": bool(STRIPE_WHSEC)
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            sig = self.headers.get("stripe-signature", "")
            if sig and not verify_stripe_signature(body, sig, STRIPE_WHSEC):
                self._json(401, {"error": "Invalid Stripe signature"})
                return

            event = json.loads(body.decode("utf-8"))

            if event.get("type") == "checkout.session.completed":
                self._json(200, handle_stripe_checkout(event))
                return

            self._json(200, {"status": "ignored", "event_type": event.get("type")})

        except Exception as e:
            print("ERROR:", str(e))
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


handler = Handler