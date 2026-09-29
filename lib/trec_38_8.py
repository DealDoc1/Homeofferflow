"""Official-source renderer and Buyer signing map for TREC 38-8."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from lib.repair_continuation import continuation_field
from lib.txr_addenda_layout import SourceAnswers, draw_entries


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
RENDER_REVISION = "trec-38-8-2026-09-22-source-v1"

REASON_MARKS = {
    "option_period": (58, 566),
    "buyer_approval": (58, 542),
    "property_approval": (58, 507),
    "hoa_documents": (58, 470),
    "seller_disclosure": (58, 445),
    "appraisal": (58, 420),
    "title_objections": (58, 384),
    "other": (59, 348),
}


def answer_layout(data):
    answers = SourceAnswers(data, "TREC 38-8 - Buyer Termination Notice Continuation", 1)
    answers.put(data.get("property_address"), [(50, 666, 508)], "Property address", size=9)
    # Both source blanks after “BETWEEN THE UNDERSIGNED BUYER AND” identify
    # the Seller; the second line ends at the printed “(SELLER)” label. Buyer
    # identity is established by the execution lines and must never be printed
    # into this Seller continuation blank.
    answers.put(
        " and ".join(data.get("seller_names") or []),
        [(265, 630, 292), (50, 611, 450)],
        "Seller",
        size=9,
    )
    for reason in data.get("termination_reasons") or []:
        x, y = REASON_MARKS[reason]
        answers.put("X", [(x, y, 11)], f"Termination reason: {reason}", size=10)
    if "other" in (data.get("termination_reasons") or []):
        answers.put(
            data.get("other_termination_basis"),
            [(441, 347, 108), (91, 332, 459), (91, 318, 459), (91, 304, 459), (91, 290, 459)],
            "Other termination basis",
            size=8,
        )
    return answers


def _overlay(answers):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    draw_entries(canvas, answers.pages[1])
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_trec_38_8(source_pdf_bytes, data):
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TREC 38-8 source must contain exactly one page.")
    answers = answer_layout(data)
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    writer.pages[0].merge_page(PdfReader(BytesIO(_overlay(answers))).pages[0])
    continuation = answers.continuation()
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_trec388(data, *, client_count=None):
    buyers = data.get("buyer_names") or []
    if not (1 <= len(buyers) <= 2):
        raise ValueError("TREC 38-8 requires one or two Buyers.")
    fields = [
        {"api_id": "trec388_buyer1_signature_p1", "type": "signature", "page": 1,
         "x": 93, "y": 848, "recipient_id": "1", "required": True, "width": 245, "height": 26},
        {"api_id": "trec388_buyer1_date_p1", "type": "date", "page": 1,
         "x": 340, "y": 851, "recipient_id": "1", "required": True, "width": 64, "height": 24,
         "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if len(buyers) == 2:
        fields.extend([
            {"api_id": "trec388_buyer2_signature_p1", "type": "signature", "page": 1,
             "x": 429, "y": 848, "recipient_id": "2", "required": True, "width": 243, "height": 26},
            {"api_id": "trec388_buyer2_date_p1", "type": "date", "page": 1,
             "x": 675, "y": 851, "recipient_id": "2", "required": True, "width": 67, "height": 24,
             "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    continuation = answer_layout(data).continuation()
    if continuation:
        for page_index in range(len(PdfReader(BytesIO(continuation)).pages)):
            for buyer_index in range(len(buyers)):
                field = continuation_field(str(buyer_index + 1), page_index + 2, page_index + 1, "trec388")
                field["recipient_id"] = str(buyer_index + 1)
                field["api_id"] = f"trec388_continuation_{page_index + 1}_buyer{buyer_index + 1}_initials"
                fields.append(field)
    return [fields]
