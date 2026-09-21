"""Private-source renderer for TXR-1905 mineral-reservation review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.txr_addenda_layout import SourceAnswers, clean, draw_entries, mark_cell
from lib.txr_source_imprint import remove_known_source_imprint


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
RENDER_REVISION = 'txr-1905-2026-09-18-neutral-source-v3'


def answer_layout(data):
    answers = SourceAnswers(data, 'TXR-1905 - Mineral Reservation Continuation', 1)
    answers.put(data.get('property_address'), [(40, 687, 534)], 'Property address', size=9)
    if data.get('reservation_choice') == 'undivided_interest':
        value = clean(data.get('undivided_interest'))
        answers.put(value + '%' if value else '', [(243, 493, 44)],
                    'Paragraph B(2) - undivided mineral-interest percentage', size=9)
    answers.names(1, (171, 115), [('Buyer', 58, 252), ('Seller', 332, 227)])
    return answers


def _overlay(data, answers):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    draw_entries(canvas, answers.pages[1])
    if data.get("reservation_choice") == "all":
        mark_cell(canvas, 79.67, 517.11)
    elif data.get('reservation_choice') == 'undivided_interest':
        mark_cell(canvas, 79.67, 495.57)
    if data.get("surface_rights") == "waived":
        mark_cell(canvas, 110.09, 454.77)
    elif data.get('surface_rights') == 'not_waived':
        mark_cell(canvas, 153.23, 454.77)
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1905(source_pdf_bytes, data):
    """Overlay the selected TXR-1905 values without adding signature fields."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1905 source must contain exactly one page.")
    answers = answer_layout(data)
    overlay = PdfReader(BytesIO(_overlay(data, answers)))
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    remove_known_source_imprint(writer, source_pdf_bytes, 'TXR-1905')
    writer.pages[0].merge_page(overlay.pages[0])
    continuation = answers.continuation()
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
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
        {"api_id": "txr1905_seller1_signature_p1", "type": "signature", "page": 1, "x": 440, "y": 807, "recipient_id": str(len(buyers) + 1), "required": True, "width": 306, "height": 24},
    ]
    if len(buyers) == 2:
        fields.append({"api_id": "txr1905_buyer2_signature_p1", "type": "signature", "page": 1, "x": 75, "y": 881, "recipient_id": "2", "required": True, "width": 340, "height": 24})
    if len(sellers) == 2:
        fields.append({"api_id": "txr1905_seller2_signature_p1", "type": "signature", "page": 1, "x": 440, "y": 881, "recipient_id": str(len(buyers) + 2), "required": True, "width": 306, "height": 24})
    fields.extend(answer_layout(data).continuation_fields(2, 'txr1905'))
    return [fields]
