"""Private-source renderer for TXR-1953 residential-lease review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, size=7):
    value = _clean(value)
    if value:
        canvas.setFont("Helvetica", size)
        canvas.drawString(x, y, value)


def _mark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(x, y, "X")


def render_txr_1953(source_pdf_bytes, data):
    """Overlay an unsigned TXR-1953 private review draft on its source PDF."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1953 source must contain exactly one page.")
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    _draw(canvas, data.get("property_address"), 246, 686, 8)
    status = data.get("lease_status")
    if status == "termination":
        _mark(canvas, 33, 613)
    elif status == "assignment":
        _mark(canvas, 33, 558)
        delivery = data.get("delivery_choice")
        if delivery == "received":
            _mark(canvas, 75, 520)
        elif delivery == "not_received":
            _mark(canvas, 75, 509)
            _draw(canvas, data.get("delivery_days"), 169, 491, 8)
        elif delivery == "oral_notice":
            _mark(canvas, 75, 470)
            _draw(canvas, data.get("oral_lease_notice"), 103, 447, 7)
    explanation = data.get("explanation")
    if explanation:
        _draw(canvas, explanation, 84, 279, 6)
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    _draw(canvas, buyers[0] if buyers else "", 55, 178, 8)
    _draw(canvas, sellers[0] if sellers else "", 329, 178, 8)
    if len(buyers) > 1:
        _draw(canvas, buyers[1], 55, 122, 8)
    if len(sellers) > 1:
        _draw(canvas, sellers[1], 329, 122, 8)
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    source.pages[0].merge_page(overlay.pages[0])
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
