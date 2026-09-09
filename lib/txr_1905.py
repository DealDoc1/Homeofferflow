"""Private-source renderer for TXR-1905 mineral-reservation review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, *, size=8):
    value = _clean(value)
    if not value:
        return
    canvas.setFont("Helvetica", size)
    canvas.drawString(x, y, value)


def _mark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(x, y, "X")


def _overlay(data):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    _draw(canvas, data.get("property_address"), 235, 688, size=9)
    if data.get("reservation_choice") == "all":
        _mark(canvas, 80, 518)
    else:
        _mark(canvas, 80, 497)
        _draw(canvas, data.get("undivided_interest"), 239, 497, size=9)
    if data.get("surface_rights") == "waived":
        _mark(canvas, 109, 454)
    else:
        _mark(canvas, 149, 454)
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    # Write each party name immediately above its signature rule; the printed
    # Buyer/Seller captions sit below those rules on the source.
    _draw(canvas, buyers[0] if buyers else "", 58, 176, size=9)
    _draw(canvas, sellers[0] if sellers else "", 333, 176, size=9)
    if len(buyers) > 1:
        _draw(canvas, buyers[1], 58, 118, size=9)
    if len(sellers) > 1:
        _draw(canvas, sellers[1], 333, 118, size=9)
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1905(source_pdf_bytes, data):
    """Overlay the selected TXR-1905 values without adding signature fields."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1905 source must contain exactly one page.")
    overlay = PdfReader(BytesIO(_overlay(data)))
    writer = PdfWriter()
    source.pages[0].merge_page(overlay.pages[0])
    writer.add_page(source.pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1905(data, *, client_count=None):
    """Return source-aligned TXR-1905 Buyer and Seller signature fields.

    This mineral-reservation addendum has two Buyer/Seller signature rows on
    page one. The map uses HomeOfferFlow's 96-DPI, top-origin SignWell space
    and remains isolated until a completed provider PDF validates the live
    signing widgets.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1905 requires one or two Buyers and one or two Sellers.")

    fields = [
        {"api_id": "txr1905_buyer1_signature_p1", "type": "signature", "page": 1, "x": 75, "y": 807, "recipient_id": "1", "required": True, "width": 340, "height": 24},
        {"api_id": "txr1905_seller1_signature_p1", "type": "signature", "page": 1, "x": 440, "y": 807, "recipient_id": str(len(buyers) + 1), "required": True, "width": 310, "height": 24},
    ]
    if len(buyers) == 2:
        fields.append({"api_id": "txr1905_buyer2_signature_p1", "type": "signature", "page": 1, "x": 75, "y": 883, "recipient_id": "2", "required": True, "width": 340, "height": 24})
    if len(sellers) == 2:
        fields.append({"api_id": "txr1905_seller2_signature_p1", "type": "signature", "page": 1, "x": 440, "y": 883, "recipient_id": str(len(buyers) + 2), "required": True, "width": 310, "height": 24})
    return [fields]
