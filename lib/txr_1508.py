"""Private-source renderer and signer map for TXR-1508.

TXR-1508 is strictly an unrepresented-customer showing acknowledgement. It
must never be used to imply representation, compensation, advice, or other
brokerage services.
"""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from lib.txr_source_imprint import remove_known_source_imprint
from lib.txr1508_answers import answer_layout, render_continuation, continuation_fields
from lib.txr_addenda_layout import draw_entries
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _check(canvas, x, y):
    """Draw a compact check inside the source's small printed checkbox.

    TXR-1508's acknowledgement cells are only about eight points wide.  The
    former 15-point stroke could visibly run into the following customer text
    in a completed packet.
    """
    canvas.setLineWidth(1.3)
    canvas.line(x + 1, y + 3, x + 3.5, y + .5)
    canvas.line(x + 3.5, y + .5, x + 7, y + 6)


def _overlay(data, brokerage, associate):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    other_broker = data.get("other_broker_agreement") or []
    draw_entries(canvas, answer_layout(data, brokerage, associate)[0])
    if data.get("signer_plan") == "associate_and_clients":
        _check(canvas, 92, 275)
    if other_broker and other_broker[0] == "yes":
        _check(canvas, 297, 219)
    if len(other_broker) > 1 and other_broker[1] == "yes":
        _check(canvas, 297, 175)
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1508(source_pdf_bytes, data, brokerage, associate):
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1508 source must contain exactly one page.")
    overlay = PdfReader(BytesIO(_overlay(data, brokerage, associate)))
    writer = PdfWriter()
    # Merge only after the page belongs to this writer; detached-page
    # content replacement is deprecated in current pypdf releases.
    writer.add_page(source.pages[0])
    remove_known_source_imprint(writer, source_pdf_bytes, 'TXR-1508')
    writer.pages[0].merge_page(overlay.pages[0])
    continuation = render_continuation(data, answer_layout(data, brokerage, associate)[1])
    if continuation:
        for page in PdfReader(BytesIO(continuation)).pages:
            writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1508(data, *, client_count=1, page_count=1):
    """Return explicit acknowledgement initials/date fields.

    The signer role is deliberate: the form may be acknowledged by the broker
    or the broker's associate, plus each unrepresented customer.
    """
    signer_plan = data.get("signer_plan")
    if signer_plan not in {"associate_and_clients", "broker_and_clients"}:
        raise ValueError("Choose whether the broker or associate will acknowledge TXR-1508.")
    fields = [
        # The agent acknowledgement has its own initials rule.  On the
        # released source that rule starts immediately after the printed
        # ``Initials:`` label at x=347.  The exact vertical placement is
        # calibrated against a completed provider PDF rather than inferred
        # from the generic widget bounds.
        # SignWell paints initials and dates at the upper edge of a widget.
        # A completed provider PDF showed the former boxes (659/657 and
        # 716/714) leaving each value visibly above its printed rule.  Move
        # the boxes down 20 SignWell pixels so the painted values sit on the
        # acknowledgement rules while preserving clear space before the next
        # customer row.
        {"api_id": "txr1508_agent_initials_p1", "type": "initials", "page": 1, "x": 347, "y": 679, "recipient_id": "associate" if signer_plan == "associate_and_clients" else "broker", "required": True, "width": 95, "height": 18},
        {"api_id": "txr1508_agent_date_p1", "type": "date", "page": 1, "x": 625, "y": 677, "recipient_id": "associate" if signer_plan == "associate_and_clients" else "broker", "required": True, "width": 121, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        {"api_id": "txr1508_client1_initials_p1", "type": "initials", "page": 1, "x": 518, "y": 736, "recipient_id": "1", "required": True, "width": 61, "height": 18},
        {"api_id": "txr1508_client1_date_p1", "type": "date", "page": 1, "x": 625, "y": 734, "recipient_id": "1", "required": True, "width": 121, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1508_client2_initials_p1", "type": "initials", "page": 1, "x": 518, "y": 794, "recipient_id": "2", "required": True, "width": 61, "height": 18},
            {"api_id": "txr1508_client2_date_p1", "type": "date", "page": 1, "x": 625, "y": 792, "recipient_id": "2", "required": True, "width": 121, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    fields.extend(continuation_fields(data, client_count, page_count))
    return [fields]
