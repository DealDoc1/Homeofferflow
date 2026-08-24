"""Private-source renderer for TXR-1948 appraisal-waiver review drafts."""

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
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(x, y, "X")


def render_txr_1948(source_pdf_bytes, data):
    """Overlay an unsigned TXR-1948 private review draft on its source PDF."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1948 source must contain exactly one page.")
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    _draw(canvas, data.get("property_address"), 228, 653, 9)
    choice = data.get("appraisal_choice")
    if choice == "waiver":
        _mark(canvas, 49, 546)
    elif choice == "partial_waiver":
        _mark(canvas, 49, 466)
        _draw(canvas, data.get("partial_value"), 234, 402, 9)
    elif choice == "additional_right":
        _mark(canvas, 49, 344)
        _draw(canvas, data.get("additional_days"), 68, 322, 9)
        _draw(canvas, data.get("additional_value"), 128, 289, 9)
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    _draw(canvas, buyers[0] if buyers else "", 48, 207, 9)
    _draw(canvas, sellers[0] if sellers else "", 322, 207, 9)
    if len(buyers) > 1:
        _draw(canvas, buyers[1], 48, 141, 9)
    if len(sellers) > 1:
        _draw(canvas, sellers[1], 322, 141, 9)
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    source.pages[0].merge_page(overlay.pages[0])
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
