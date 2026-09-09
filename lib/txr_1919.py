"""Private-source renderer for TXR-1919 loan-assumption review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, *, size=8):
    value = _clean(value)
    if value:
        canvas.setFont("Helvetica", size)
        canvas.drawString(x, y, value)


def _mark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(x, y, "X")


def _page_one(data):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    _draw(canvas, data.get("property_address"), 185, 666, size=9)
    _draw(canvas, data.get("credit_days"), 96, 573)
    docs = set(data.get("credit_documents") or [])
    for key, x, y in (
        ("credit_report", 386, 579), ("employment", 475, 579),
        ("funds", 214, 568), ("financial_statement", 510, 568), ("other", 183, 557),
    ):
        if key in docs:
            _mark(canvas, x, y)
    if "other" in docs:
        _draw(canvas, data.get("credit_other"), 230, 557)
    loans = data.get("loans") or {}
    for key, y, lender_y, box_y in (("first", 356, 367, 374), ("second", 306, 317, 326)):
        loan = loans.get(key) or {}
        if loan.get("enabled"):
            _mark(canvas, 72, box_y)
            _draw(canvas, loan.get("lender"), 447 if key == "first" else 484, lender_y)
            _draw(canvas, loan.get("balance"), 474 if key == "first" else 472, y)
            _draw(canvas, loan.get("monthly_payment"), 102, y - 22)
    variance = data.get("variance") or {}
    if variance.get("adjustment") == "cash":
        _mark(canvas, 211, 265)
    else:
        _mark(canvas, 350, 265)
    _draw(canvas, variance.get("termination_threshold"), 84, 234)
    terms = data.get("loan_terms") or {}
    _draw(canvas, terms.get("first_fee_cap"), 316, 158)
    _draw(canvas, terms.get("second_fee_cap"), 435, 158)
    _draw(canvas, terms.get("first_rate_cap"), 310, 136)
    _draw(canvas, terms.get("second_rate_cap"), 412, 136)
    canvas.save()
    packet.seek(0)
    return packet.read()


def _page_two(data):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    _draw(canvas, data.get("property_address"), 245, 742, size=9)
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    _draw(canvas, buyers[0] if buyers else "", 58, 300, size=9)
    _draw(canvas, sellers[0] if sellers else "", 338, 300, size=9)
    if len(buyers) > 1:
        _draw(canvas, buyers[1], 58, 238, size=9)
    if len(sellers) > 1:
        _draw(canvas, sellers[1], 338, 238, size=9)
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1919(source_pdf_bytes, data):
    """Overlay review values without creating signature fields or a send path."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 2:
        raise ValueError("TXR-1919 source must contain exactly two pages.")
    overlays = [PdfReader(BytesIO(_page_one(data))), PdfReader(BytesIO(_page_two(data)))]
    writer = PdfWriter()
    for index, page in enumerate(source.pages):
        writer.add_page(page)
        writer.pages[index].merge_page(overlays[index].pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1919(data, *, client_count=None):
    """Return the TXR-1919 Buyer and Seller signature fields.

    TXR-1919 has two Buyer/Seller execution rows on page two. Coordinates are
    calibrated from those printed source rules in the 96-DPI, top-origin
    coordinate space required by the SignWell integration. The map stays
    isolated until a completed provider PDF verifies the live widget output.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1919 requires one or two Buyers and one or two Sellers.")

    fields = [
        {"api_id": "txr1919_buyer1_signature_p2", "type": "signature", "page": 2, "x": 60, "y": 632, "recipient_id": "1", "required": True, "width": 325, "height": 24},
        {"api_id": "txr1919_seller1_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 632, "recipient_id": str(len(buyers) + 1), "required": True, "width": 325, "height": 24},
    ]
    if len(buyers) == 2:
        fields.append({"api_id": "txr1919_buyer2_signature_p2", "type": "signature", "page": 2, "x": 60, "y": 716, "recipient_id": "2", "required": True, "width": 325, "height": 24})
    if len(sellers) == 2:
        fields.append({"api_id": "txr1919_seller2_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 716, "recipient_id": str(len(buyers) + 2), "required": True, "width": 325, "height": 24})
    return [fields]
