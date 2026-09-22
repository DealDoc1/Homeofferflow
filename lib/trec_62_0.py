"""Private-source renderer and seller signing map for TREC 62-0."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from lib.repair_continuation import continuation_field
from lib.txr_addenda_layout import SourceAnswers, draw_entries
from lib.txr_source_imprint import remove_known_source_imprint


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
RENDER_REVISION = "trec-62-0-2026-09-22-source-v1"


def answer_layout(data):
    """Map only the blanks completed before Seller signs.

    The two escrow-agent receipt sections intentionally remain untouched.
    """
    answers = SourceAnswers(data, "TREC 62-0 - Seller Notice Continuation", 1)
    answers.put(data.get("property_address"), [(56, 674, 500)], "Property address", size=9)
    answers.put(" and ".join(data.get("buyer_names") or []), [(268, 617, 286)], "Buyer", size=9)
    answers.put(data.get("delivery_date"), [(379, 527, 108)], "Amended Effective Date", size=9)
    return answers


def _overlay(answers):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    draw_entries(canvas, answers.pages[1])
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_trec_62_0(source_pdf_bytes, data):
    """Overlay the notice answers while preserving the official source page."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TREC 62-0 source must contain exactly one page.")
    answers = answer_layout(data)
    overlay = PdfReader(BytesIO(_overlay(answers)))
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    remove_known_source_imprint(writer, source_pdf_bytes, "TREC-62-0")
    writer.pages[0].merge_page(overlay.pages[0])
    continuation = answers.continuation()
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_trec620(data, *, client_count=None):
    """Return Seller-only signature/date fields in SignWell's 96-DPI space."""
    sellers = data.get("seller_names") or []
    if not (1 <= len(sellers) <= 2):
        raise ValueError("TREC 62-0 requires one or two Sellers.")
    fields = [
        {"api_id": "trec620_seller1_signature_p1", "type": "signature", "page": 1,
         "x": 83, "y": 440, "recipient_id": "1", "required": True, "width": 222, "height": 24},
        {"api_id": "trec620_seller1_date_p1", "type": "date", "page": 1,
         "x": 310, "y": 440, "recipient_id": "1", "required": True, "width": 72, "height": 20,
         "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if len(sellers) == 2:
        fields.extend([
            {"api_id": "trec620_seller2_signature_p1", "type": "signature", "page": 1,
             "x": 443, "y": 440, "recipient_id": "2", "required": True, "width": 211, "height": 24},
            {"api_id": "trec620_seller2_date_p1", "type": "date", "page": 1,
             "x": 659, "y": 440, "recipient_id": "2", "required": True, "width": 72, "height": 20,
             "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    continuation = answer_layout(data).continuation()
    if continuation:
        for page_index in range(len(PdfReader(BytesIO(continuation)).pages)):
            for seller_index in range(len(sellers)):
                field = continuation_field(str(seller_index + 3), page_index + 2, page_index + 1, "trec620")
                field["recipient_id"] = str(seller_index + 1)
                field["api_id"] = f"trec620_continuation_{page_index + 1}_seller{seller_index + 1}_initials"
                fields.append(field)
    return [fields]
