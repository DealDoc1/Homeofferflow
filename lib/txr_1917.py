"""Private-source renderer for TXR-1917 environmental-review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, size=8):
    value = _clean(value)
    if value:
        canvas.setFont("Helvetica", size)
        canvas.drawString(x, y, value)


def _mark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(x, y, "X")


def render_txr_1917(source_pdf_bytes, data):
    """Overlay an unsigned TXR-1917 private review draft on its source PDF."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1917 source must contain exactly one page.")
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    _draw(canvas, data.get("property_address"), 185, 600, 9)
    selected = set(data.get("review_types") or [])
    for key, y in (("environmental", 545), ("species", 509), ("wetlands", 443)):
        if key in selected:
            _mark(canvas, 60, y)
    _draw(canvas, data.get("termination_days"), 121, 379)
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    _draw(canvas, buyers[0] if buyers else "", 58, 260, 9)
    _draw(canvas, sellers[0] if sellers else "", 330, 260, 9)
    if len(buyers) > 1:
        _draw(canvas, buyers[1], 58, 188, 9)
    if len(sellers) > 1:
        _draw(canvas, sellers[1], 330, 188, 9)
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    source.pages[0].merge_page(overlay.pages[0])
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
