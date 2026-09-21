"""Private-source renderer for TXR-1917 environmental-review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.txr_addenda_layout import SourceAnswers, draw_entries


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
RENDER_REVISION = 'txr-1917-2026-09-18-source-blanks-v2'


def answer_layout(data):
    answers = SourceAnswers(data, 'TXR-1917 - Environmental Review Continuation', 1)
    answers.put(data.get('property_address'), [(42, 604, 532)], 'Property address', size=9)
    answers.put(data.get('termination_days'), [(97, 377, 22)], 'Termination period (days)')
    answers.names(1, (263, 192.5), [('Buyer', 55.5, 231), ('Seller', 325.5, 231)])
    return answers


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
    answers = answer_layout(data)
    draw_entries(canvas, answers.pages[1])
    selected = set(data.get("review_types") or [])
    for key, y in (("environmental", 540), ("species", 502.3), ("wetlands", 436.7)):
        if key in selected:
            _mark(canvas, 60, y)
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    writer.pages[0].merge_page(overlay.pages[0])
    continuation = answers.continuation()
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1917(data, *, client_count=None):
    """Return source-aligned TXR-1917 Buyer and Seller signature fields.

    The environmental-assessment addendum has two Buyer/Seller execution rows
    on its source page. This map uses HomeOfferFlow's SignWell 96-DPI,
    top-origin coordinate space, shared by standalone and combined packets.
    Completed-provider verification remains separate from these field bounds.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1917 requires one or two Buyers and one or two Sellers.")

    fields = [
        {"api_id": "txr1917_buyer1_signature_p1", "type": "signature", "page": 1, "x": 74, "y": 684, "recipient_id": "1", "required": True, "width": 308, "height": 24},
        {"api_id": "txr1917_seller1_signature_p1", "type": "signature", "page": 1, "x": 434, "y": 684, "recipient_id": str(len(buyers) + 1), "required": True, "width": 308, "height": 24},
    ]
    if len(buyers) == 2:
        fields.append({"api_id": "txr1917_buyer2_signature_p1", "type": "signature", "page": 1, "x": 74, "y": 778, "recipient_id": "2", "required": True, "width": 308, "height": 24})
    if len(sellers) == 2:
        fields.append({"api_id": "txr1917_seller2_signature_p1", "type": "signature", "page": 1, "x": 434, "y": 778, "recipient_id": str(len(buyers) + 2), "required": True, "width": 308, "height": 24})
    fields.extend(answer_layout(data).continuation_fields(2, 'txr1917'))
    return [fields]
