"""Private-source renderer and signer map for TXR-1506 consumer notice."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from lib.txr_source_imprint import remove_known_source_imprint
from lib.txr1506_answers import answer_layout, render_continuation, continuation_fields
from lib.txr_addenda_layout import draw_entries
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _overlay(data, brokerage):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    pages, _ = answer_layout(data, brokerage)
    for page in range(1, 7):
        draw_entries(canvas, pages[page])
        canvas.showPage()
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1506(source_pdf_bytes, data, brokerage):
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 6:
        raise ValueError("TXR-1506 source must contain exactly six pages.")
    overlay = PdfReader(BytesIO(_overlay(data, brokerage)))
    writer = PdfWriter()
    for page in source.pages:
        # Merge only after the page belongs to this writer; this keeps the
        # overlay stable with current and future pypdf releases.
        writer.add_page(page)
    remove_known_source_imprint(writer, source_pdf_bytes, 'TXR-1506')
    for index in range(len(source.pages)):
        writer.pages[index].merge_page(overlay.pages[index])
    continuation = render_continuation(data, answer_layout(data, brokerage)[1])
    if continuation:
        for page in PdfReader(BytesIO(continuation)).pages:
            writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1506(data, *, client_count=1, page_count=6):
    """Return explicit receipt-initial and signature/date fields."""
    signer_plan = data.get("signer_plan")
    if signer_plan not in {"consumers_and_associate", "consumers_and_broker"}:
        raise ValueError("Choose whether the broker or associate will sign the TXR-1506 notice.")
    fields = []
    # Page 1 uses shorter, left-shifted acknowledgement blanks. Pages 2–5
    # share a wider pair farther right. One coordinate for all five pages put
    # the first signer in the wrong blank and the second beyond it.
    initials_rows = {
        1: ((444, 50), (512, 40)),
        2: ((480, 55), (554, 55)),
        3: ((480, 55), (554, 55)),
        4: ((480, 55), (554, 55)),
        5: ((480, 55), (554, 55)),
    }
    for page in range(1, 6):
        (client1_x, client1_width), (client2_x, client2_width) = initials_rows[page]
        fields.append({"api_id": f"txr1506_client1_initials_p{page}", "type": "initials", "page": page, "x": client1_x, "y": 976, "recipient_id": "1", "required": True, "width": client1_width, "height": 16})
        if client_count == 2:
            fields.append({"api_id": f"txr1506_client2_initials_p{page}", "type": "initials", "page": page, "x": client2_x, "y": 976, "recipient_id": "2", "required": True, "width": client2_width, "height": 16})
    fields.extend([
        # Page six uses a full-width consumer rule. The widget must reach the
        # complete printed line; a shorter centered field makes a signed name
        # look detached from the acknowledgement it completes.
        {"api_id": "txr1506_client1_signature_p6", "type": "signature", "page": 6, "x": 48, "y": 893, "recipient_id": "1", "required": True, "width": 336, "height": 26},
        {"api_id": "txr1506_client1_date_p6", "type": "date", "page": 6, "x": 432, "y": 893, "recipient_id": "1", "required": True, "width": 96, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ])
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1506_client2_signature_p6", "type": "signature", "page": 6, "x": 48, "y": 939, "recipient_id": "2", "required": True, "width": 336, "height": 26},
            {"api_id": "txr1506_client2_date_p6", "type": "date", "page": 6, "x": 432, "y": 939, "recipient_id": "2", "required": True, "width": 96, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    role = "associate" if signer_plan == "consumers_and_associate" else "broker"
    fields.extend([
        # The source prefixes this rule with a printed "By:". Start after
        # that prefix, while reaching the end of the complete printed rule.
        # This leaves the "By:" text visible without making a provider's
        # completed signature look truncated.
        {"api_id": f"txr1506_{role}_signature_p6", "type": "signature", "page": 6, "x": 80, "y": 799, "recipient_id": role, "required": True, "width": 304, "height": 26},
        # The source uses the same right-hand Date column for the provider
        # acknowledgement and each consumer acknowledgement. Keeping each
        # widget inside that printed rule prevents it from covering the
        # caption or extending into the page margin.
        {"api_id": f"txr1506_{role}_date_p6", "type": "date", "page": 6, "x": 432, "y": 800, "recipient_id": role, "required": True, "width": 96, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ])
    fields.extend(continuation_fields(data, client_count, page_count))
    return [fields]
