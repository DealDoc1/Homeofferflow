"""Private-source renderer and signer map for TXR-1507 Short Form.

The source PDF is supplied by an authorized brokerage administrator and is
never checked into the repository. This module only overlays the approved
intake values and returns SignWell field metadata; it does not select a form,
infer compensation, or bypass the brokerage/source authorization gates.
"""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from lib.pdf_text import draw_text, text_width as stringWidth
from lib.txr1507_answers import answer_layout, render_continuation, continuation_fields
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_SIZE = 9
SMALL_SIZE = 8


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(c, text, x, y, *, size=FONT_SIZE, bold=False):
    text = _clean(text)
    if not text:
        return
    draw_text(c, text, x, y, size, base_font=FONT_BOLD if bold else FONT)


def _draw_check(c, x, y):
    """Draw a compact X inside the source's small printed checkbox.

    Selection marks must stay entirely inside the printed square; a prior
    wide check visually ran into the adjacent label on completed agreements.
    """
    c.setLineWidth(1.0)
    c.line(x + 1, y + 1, x + 6, y + 6)
    c.line(x + 1, y + 6, x + 6, y + 1)


def _draw_signing_role_check(c, x, y):
    """Mark one broker/associate execution checkbox with a compact X."""
    c.setLineWidth(1.1)
    # This source's execution squares sit slightly below the supplied anchor.
    # Keep the mark within the measured y-3 through y+5 cell.
    c.line(x + 1, y - 2, x + 6, y + 3)
    c.line(x + 1, y + 3, x + 6, y - 2)


def _draw_party_header(c, clients, broker_name):
    """Identify page two without running beyond its measured title blank."""
    parties = " and ".join(filter(None, (
        ", ".join(_clean(name) for name in clients), _clean(broker_name),
    )))
    # Source: blank x=244.13..576.10, top-origin rule y=42.48.
    # Do not crop a legal name or shrink it to unreadable text. Paragraph 1
    # remains the authoritative party identification for unusually long names.
    for size in (8, 7.5, 7):
        if stringWidth(parties, FONT, size) <= 328:
            _draw(c, parties, 246, 752, size=size)
            return
    _draw(c, "Client(s) and Broker identified in Paragraph 1", 246, 752, size=8)


def _overlay(data, brokerage, associate):
    """Return an overlay PDF for the exact two-page TXR-1507 source."""
    clients = data["client_names"]
    broker_name = brokerage.get("legal_name") or brokerage.get("name") or brokerage.get("dba_name")
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    canvas.setFillColorRGB(0, 0, 0)

    # Page 1 - parties, market area, term, services, and compensation.
    pages, _ = answer_layout(data, brokerage, associate)
    for x, y, value, size in pages[1]:
        _draw(canvas, value, x, y, size=size)

    if data["service_level"] == "full_services":
        # Keep the complete stroked X inside the printed Wingdings cell,
        # not merely its starting point (06-15-26 source).
        _draw_check(canvas, 55, 459)
    else:
        _draw_check(canvas, 55, 427)

    canvas.showPage()

    # Page 2 - intermediary choice, printed names, and license fields. The
    # signature/date widgets are supplied separately to SignWell.
    _draw_party_header(canvas, clients, broker_name)
    if data["intermediary"] == "authorized":
        _draw_check(canvas, 178, 637)
    else:
        # The second printed intermediary cell is separate, immediately
        # before "does not authorize"; it shares the same calibrated
        # vertical center as the first cell.
        _draw_check(canvas, 234, 637)

    for x, y, value, size in pages[2]:
        _draw(canvas, value, x, y, size=size)
    # The broker/associate signature rule is shared.  Mark the source's
    # matching role checkbox so a completed agreement identifies the signer.
    if data.get("signer_plan") == "clients_and_associate":
        # The complete stroke belongs inside the lower Associate cell.
        _draw_signing_role_check(canvas, 37, 240)
    elif data.get("signer_plan") == "clients_and_broker":
        # The Broker square is the upper of the two execution choices.
        _draw_signing_role_check(canvas, 37, 251)
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1507(source_pdf_bytes, data, brokerage, associate):
    """Overlay approved values onto the private source PDF without flattening."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 2:
        raise ValueError("TXR-1507 source must contain exactly two pages.")
    overlay = PdfReader(BytesIO(_overlay(data, brokerage, associate)))
    writer = PdfWriter()
    for index, page in enumerate(source.pages):
        # Merge only after the page belongs to this writer; detached-page
        # content replacement is deprecated in current pypdf releases.
        writer.add_page(page)
        writer.pages[index].merge_page(overlay.pages[index])
    continuation = render_continuation(data, answer_layout(data, brokerage, associate)[1])
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1507(data, *, client_count=1, page_count=2):
    """Return explicit signer fields for the two-page source.

    Coordinates are source-specific and must remain separate from the 20-19
    purchase-packet map. The agent/broker recipient is not added automatically:
    the source-owner signing plan must supply that decision first.
    """
    # SignWell's letter-page coordinates use a 4/3 scale and a top-origin
    # system in the existing HomeOfferFlow integration. These positions are
    # intentionally separate from the purchase-packet map.
    signer_plan = data.get("signer_plan")
    if signer_plan not in {"clients_and_associate", "clients_and_broker"}:
        raise ValueError("Choose whether the broker or associate will sign the TXR-1507 agreement.")
    role = "associate" if signer_plan == "clients_and_associate" else "broker"
    fields = [
        # The footer requires initials from the selected Broker/Associate and
        # each Client. These source-calibrated rectangles start on the three
        # printed underscore blanks, not on the surrounding labels.
        {"api_id": f"txr1507_{role}_initials_p1", "type": "initials", "page": 1, "x": 435, "y": 976, "recipient_id": role, "required": True, "width": 46, "height": 14},
        {"api_id": "txr1507_client1_initials_p1", "type": "initials", "page": 1, "x": 543, "y": 976, "recipient_id": "1", "required": True, "width": 46, "height": 14},
        # Page two's first Client execution line runs from source x=324.1
        # through 576.1 at top-origin y=534.0.  SignWell uses a 4/3 scale.
        # The entire rectangle must END above PDF top=533.95, not start
        # there. Completed date text measured about 49 PDF points wide;
        # allocate 54 points and shift left to stay within the 576.1 edge.
        {"api_id": "txr1507_client1_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 684, "recipient_id": "1", "required": True, "width": 240, "height": 24},
        {"api_id": "txr1507_client1_date_p2", "type": "date", "page": 2, "x": 696, "y": 692, "recipient_id": "1", "required": True, "width": 72, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1507_client2_initials_p1", "type": "initials", "page": 1, "x": 596, "y": 976, "recipient_id": "2", "required": True, "width": 46, "height": 14},
            # Apply the same completed-packet correction to the second
            # client's execution row.
            {"api_id": "txr1507_client2_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 794, "recipient_id": "2", "required": True, "width": 240, "height": 24},
            {"api_id": "txr1507_client2_date_p2", "type": "date", "page": 2, "x": 696, "y": 802, "recipient_id": "2", "required": True, "width": 72, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    # The source uses checkboxes to identify whether the broker or the
    # broker's associate signs, followed by one shared signature/date rule.
    # The shared Broker/Associate rule is source x=36.0 through 288.1 at
    # top-origin y=534.0.  It shares the first Client's row.  Use the same
    # rule-ending placement convention as the Client fields, without covering
    # the printed role choices, labels, or date caption.
    role_y = 684
    role_signature_x = 48
    role_date_x = 312
    fields.extend([
        {"api_id": f"txr1507_{role}_signature_p2", "type": "signature", "page": 2, "x": role_signature_x, "y": role_y, "recipient_id": role, "required": True, "width": 240, "height": 24},
        {"api_id": f"txr1507_{role}_date_p2", "type": "date", "page": 2, "x": role_date_x, "y": 692, "recipient_id": role, "required": True, "width": 72, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ])
    fields.extend(continuation_fields(data, client_count, page_count))
    return [fields]
