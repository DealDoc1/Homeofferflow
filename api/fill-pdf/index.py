import json, os, base64, hashlib, hmac, httpx
from io import BytesIO
from http.server import BaseHTTPRequestHandler

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    NameObject,
    BooleanObject,
    DictionaryObject,
    TextStringObject,
)

from reportlab.pdfgen import canvas

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIPE_WHSEC = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

FROM_EMAIL = "offers@homeofferflow.com"
SUPPORT_EMAIL = "support@homeofferflow.com"

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

MAIN_PDF = os.path.join(BASE_DIR, "20-18_0.pdf")


def fmt_money(v):
    try:
        if v in [None, ""]:
            return ""
        return f"{int(float(v)):,}"
    except:
        return str(v or "")


def split_date(v):
    if not v:
        return "", ""

    try:
        from datetime import datetime

        d = datetime.strptime(v, "%Y-%m-%d")

        return (
            d.strftime("%B %d").replace(" 0", " "),
            str(d.year)[-2:]
        )

    except:
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

        return any(
            hmac.compare_digest(expected, s)
            for s in signatures
        )

    except:
        return False


def field_name_from_annot(annot):
    try:
        if annot.get("/T"):
            return str(annot.get("/T"))

        parent = annot.get("/Parent")

        if parent:
            p = parent.get_object()

            if p.get("/T"):
                return str(p.get("/T"))

    except:
        pass

    return ""


def build_field_positions(reader):
    positions = {}

    for page_index, page in enumerate(reader.pages):

        if "/Annots" not in page:
            continue

        for annot_ref in page["/Annots"]:

            try:
                annot = annot_ref.get_object()

                name = field_name_from_annot(annot)

                if not name:
                    continue

                rect = [float(x) for x in annot["/Rect"]]

                positions.setdefault(name, []).append({
                    "page": page_index,
                    "rect": rect
                })

            except:
                continue

    return positions


def overlay_page(width, height):
    buf = BytesIO()

    c = canvas.Canvas(
        buf,
        pagesize=(width, height)
    )

    c.setFillColorRGB(0, 0, 0)

    return buf, c


def draw_text(c, rect, value, size=8):
    if value in [None, ""]:
        return

    x1, y1, x2, y2 = rect

    x = min(x1, x2) + 2
    y = min(y1, y2) + 3

    c.setFont("Helvetica", size)
    c.drawString(x, y, str(value))


def draw_money(c, rect, value, size=8):
    if value in [None, ""]:
        return

    x1, y1, x2, y2 = rect

    x = max(x1, x2) - 2
    y = min(y1, y2) + 3

    c.setFont("Helvetica", size)
    c.drawRightString(x, y, fmt_money(value))


def draw_check(c, rect):
    x1, y1, x2, y2 = rect

    x = min(x1, x2) + 2
    y = min(y1, y2) + 1

    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, "X")


def set_pdf_field_value(reader, name, value):

    for page in reader.pages:

        if "/Annots" not in page:
            continue

        for annot_ref in page["/Annots"]:

            try:
                annot = annot_ref.get_object()

                fname = field_name_from_annot(annot)

                if fname == name:

                    annot.update({
                        NameObject("/V"): TextStringObject(str(value))
                    })

            except:
                pass


def stamp_pdf(pdf_path, text_values, money_values, checks):

    reader = PdfReader(pdf_path)

    positions = build_field_positions(reader)

    overlays = {}

    for page_index, page in enumerate(reader.pages):

        w = float(page.mediabox.width)
        h = float(page.mediabox.height)

        overlays[page_index] = overlay_page(w, h)

    for name, value in text_values.items():

        if value in [None, ""]:
            continue

        set_pdf_field_value(reader, name, value)

        for pos in positions.get(name, []):

            _, c = overlays[pos["page"]]

            draw_text(c, pos["rect"], value)

    for name, value in money_values.items():

        if value in [None, ""]:
            continue

        set_pdf_field_value(reader, name, fmt_money(value))

        for pos in positions.get(name, []):

            _, c = overlays[pos["page"]]

            draw_money(c, pos["rect"], value)

    for name in checks:

        for pos in positions.get(name, []):

            _, c = overlays[pos["page"]]

            draw_check(c, pos["rect"])

    writer = PdfWriter()

    for page_index, page in enumerate(reader.pages):

        buf, c = overlays[page_index]

        c.save()

        buf.seek(0)

        overlay_reader = PdfReader(buf)

        if len(overlay_reader.pages) > 0:
            page.merge_page(overlay_reader.pages[0])

        writer.add_page(page)

    out = BytesIO()

    writer.write(out)

    return out.getvalue()


def build_maps(s):

    lot, block = parse_lot_block(s.get("lot", ""))

    addr = f"{s.get('address','')}, {s.get('city','')}, TX {s.get('zip','')}"

    buyer = s.get("buyer1", "")

    if s.get("buyer2"):
        buyer += f" and {s.get('buyer2')}"

    price = float(s.get("price", 0) or 0)
    loan = float(s.get("loanAmount", 0) or 0)
    cash = price - loan

    closing_md, closing_yy = split_date(
        s.get("closingDate")
    )

    text_values = {
        "1 PARTIES The parties to this contract are": s.get("seller", ""),
        "Seller and": buyer,
        "A LAND Lot": lot,
        "Block": block,
        "undefined": s.get("subdiv", ""),
        "Addition City of": s.get("city", ""),
        "County of": s.get("county", ""),
        "Texas known as": addr,

        "undefined_6": s.get("titleCompany", ""),
        "undefined_7": s.get("titleAddress", ""),

        "A The closing of the sale will be on or before": closing_md,
        "20": closing_yy,

        "Option Fee in the form of": fmt_money(s.get("optionFee")),

        "the Title Company and Buyers lenders Check one box only": s.get("terminationDays", "7"),

        "receipt or the date specified in this paragraph whichever is earlier": s.get("surveyDays", "7"),

        "Buyers Expenses as allowed by the lender": fmt_money(
            s.get("concessionAmount")
        ),

        "following specific repairs and treatments": s.get(
            "repairsText",
            ""
        ),
    }

    money_values = {
        "undefined_3": cash,
        "undefined_4": loan,
        "undefined_5": price,

        "as earnest money to": s.get("earnest"),
        "as earnest money to 2": s.get("optionFee"),
    }

    checks = [
        "B Sum of all financing described in the attached",
        "Third Party Financing Addendum",
        "Sellers",
        "i will not be amended or deleted from the title policy or",
        "1Within",
        "is",
        "2 Buyer accepts the Property As Is provided Seller at Sellers expense shall complete the",
        "upon",
        "Addendum for Property Subject to",
    ]

    return text_values, money_values, checks


def fill_and_merge(offer):

    text_values, money_values, checks = build_maps(offer)

    pdf_bytes = stamp_pdf(
        MAIN_PDF,
        text_values,
        money_values,
        checks
    )

    return pdf_bytes


def send_confirmation_email(
    to_email,
    buyer_name,
    addr,
    pdf_bytes
):

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "bcc": [SUPPORT_EMAIL],
        "subject": f"Your Filled Offer PDF — {addr}",
        "html": f"""
        <div style="font-family:Arial;">
          <h2>Your filled HomeOfferFlow PDF is ready.</h2>
          <p>{buyer_name}</p>
        </div>
        """,
        "attachments": [{
            "filename": "HomeOfferFlow_Offer.pdf",
            "content": base64.b64encode(pdf_bytes).decode(),
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
        raise Exception(
            f"Resend error {r.status_code}: {r.text}"
        )


def handle_checkout(event):

    session = event.get("data", {}).get("object", {})

    metadata = session.get("metadata", {}) or {}

    offer = json.loads(metadata["offer_data"])

    pdf_bytes = fill_and_merge(offer)

    send_confirmation_email(
        offer.get("buyerEmail"),
        offer.get("buyer1"),
        offer.get("address"),
        pdf_bytes
    )

    return {
        "status": "ok"
    }


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        self._json(200, {
            "status": "field-coordinate stamped fill-pdf live",
            "main_pdf_exists": os.path.exists(MAIN_PDF),
            "resend_key_set": bool(RESEND_API_KEY),
            "stripe_webhook_secret_set": bool(STRIPE_WHSEC)
        })

    def do_POST(self):

        try:

            length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(length)

            sig = self.headers.get(
                "stripe-signature",
                ""
            )

            if sig and not verify_stripe_signature(
                body,
                sig,
                STRIPE_WHSEC
            ):
                self._json(401, {
                    "error": "Invalid Stripe signature"
                })
                return

            event = json.loads(body.decode("utf-8"))

            if event.get("type") == "checkout.session.completed":

                result = handle_checkout(event)

                self._json(200, result)

                return

            self._json(200, {
                "status": "ignored"
            })

        except Exception as e:

            print("ERROR:", str(e))

            self._json(500, {
                "error": str(e)
            })

    def _json(self, code, data):

        self.send_response(code)
        self.send_header(
            "Content-Type",
            "application/json"
        )
        self.end_headers()

        self.wfile.write(
            json.dumps(data).encode()
        )


handler = Handler