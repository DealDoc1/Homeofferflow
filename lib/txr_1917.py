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
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    writer.pages[0].merge_page(overlay.pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1917(data, *, client_count=None):
    """Return source-aligned TXR-1917 Buyer and Seller signature fields.

    The environmental-assessment addendum has two Buyer/Seller execution rows
    on its single page. This isolated map uses the HomeOfferFlow SignWell
    96-DPI, top-origin coordinate space and remains unconnected to a live
    package until completed-provider PDF verification is recorded.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1917 requires one or two Buyers and one or two Sellers.")

    fields = [
        {"api_id": "txr1917_buyer1_signature_p1", "type": "signature", "page": 1, "x": 70, "y": 686, "recipient_id": "1", "required": True, "width": 313, "height": 24},
        {"api_id": "txr1917_seller1_signature_p1", "type": "signature", "page": 1, "x": 433, "y": 686, "recipient_id": str(len(buyers) + 1), "required": True, "width": 313, "height": 24},
    ]
    if len(buyers) == 2:
        fields.append({"api_id": "txr1917_buyer2_signature_p1", "type": "signature", "page": 1, "x": 70, "y": 780, "recipient_id": "2", "required": True, "width": 313, "height": 24})
    if len(sellers) == 2:
        fields.append({"api_id": "txr1917_seller2_signature_p1", "type": "signature", "page": 1, "x": 433, "y": 780, "recipient_id": str(len(buyers) + 2), "required": True, "width": 313, "height": 24})
    return [fields]
