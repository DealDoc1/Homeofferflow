"""Private-source renderer and signer map for TXR-1507 Short Form.

The source PDF is supplied by an authorized brokerage administrator and is
never checked into the repository. This module only overlays the approved
intake values and returns SignWell field metadata; it does not select a form,
infer compensation, or bypass the brokerage/source authorization gates.
"""

from io import BytesIO
from textwrap import wrap

from pypdf import PdfReader, PdfWriter
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
    c.setFont(FONT_BOLD if bold else FONT, size)
    c.drawString(x, y, text)


def _draw_wrapped(c, text, x, y, width_chars, *, line_height=11, size=FONT_SIZE):
    words = _clean(text)
    if not words:
        return
    for index, line in enumerate(wrap(words, width_chars)):
        _draw(c, line, x, y - (index * line_height), size=size)


def _draw_check(c, x, y):
    """Draw a compact X inside the source's small printed checkbox.

    Selection marks must stay entirely inside the printed square; a prior
    wide check visually ran into the adjacent label on completed agreements.
    """
    c.setLineWidth(1.0)
    c.line(x + 1, y + 1, x + 7, y + 7)
    c.line(x + 1, y + 7, x + 7, y + 1)


def _draw_signing_role_check(c, x, y):
    """Mark one broker/associate execution checkbox with a compact X."""
    c.setLineWidth(1.1)
    # This source's execution squares sit slightly below the supplied anchor.
    # Keep the mark within the measured y-3 through y+5 cell.
    c.line(x + 1, y - 2, x + 7, y + 4)
    c.line(x + 1, y + 4, x + 7, y - 2)


def _overlay(data, brokerage, associate):
    """Return an overlay PDF for the exact two-page TXR-1507 source."""
    clients = data["client_names"]
    compensation = data["compensation"]
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    canvas.setFillColorRGB(0, 0, 0)

    # Page 1 - parties, market area, term, services, and compensation.
    _draw(canvas, ", ".join(clients), 286, 645, size=8)
    _draw(canvas, brokerage.get("legal_name") or brokerage.get("name") or brokerage.get("dba_name"), 338, 632, size=8)
    _draw_wrapped(canvas, data["market_area"], 93, 556, 82, size=8, line_height=10)
    _draw(canvas, data["term_start"], 224, 519, size=8)
    _draw(canvas, data["term_end"], 431, 519, size=8)

    if data["service_level"] == "full_services":
        # The Full Services box on the 06-15-26 source sits at x=56/y=461
        # in ReportLab's bottom-origin letter coordinates.  The prior y=455
        # mark landed below the printed square and made a selected service
        # level look blank in the rendered preview.
        _draw_check(canvas, 56, 461)
    else:
        _draw_check(canvas, 57, 425)
        _draw(canvas, data["showing_fee"], 316, 425, size=8)

    # The source prints the percent sign at roughly x=216.  Keep the entered
    # percentage inside the preceding blank rather than overprinting "%".
    _draw(canvas, compensation.get("purchase_percentage"), 190, 196, size=8)
    _draw(canvas, compensation.get("purchase_flat_fee"), 480, 196, size=8)
    _draw(canvas, compensation.get("lease_one_month_percentage"), 231, 177, size=8)
    _draw(canvas, compensation.get("lease_total_rents_percentage"), 385, 177, size=8)
    _draw(canvas, compensation.get("lease_flat_fee"), 480, 177, size=8)

    canvas.showPage()

    # Page 2 - intermediary choice, printed names, and license fields. The
    # signature/date widgets are supplied separately to SignWell.
    if data["intermediary"] == "authorized":
        # On the 06-15-26 source the first intermediary box begins at
        # x=177/y=643 (ReportLab bottom-origin points).  A prior x=202 map
        # placed the mark over the following “does” text instead of inside
        # the selected square.
        _draw_check(canvas, 177, 643)
    else:
        # The second printed intermediary cell is separate, immediately
        # before "does not authorize"; it begins at x=233 rather than in
        # the following sentence.
        _draw_check(canvas, 233, 643)

    broker_name = brokerage.get("legal_name") or brokerage.get("name") or brokerage.get("dba_name")
    broker_license = brokerage.get("license_number") or ""
    # ``hof_agent_profiles`` provides ``agent_name``.  Keep it visible on
    # the source when the same person is assigned as the signing associate.
    associate_name = associate.get("name") or associate.get("agent_name") or ""
    associate_license = associate.get("license_number") or ""
    _draw(canvas, broker_name, 56, 296, size=8)
    _draw(canvas, broker_license, 238, 296, size=8)
    _draw(canvas, ", ".join(clients[:1]), 338, 296, size=8)
    _draw(canvas, associate_name, 56, 226, size=8)
    _draw(canvas, associate_license, 238, 226, size=8)
    if len(clients) > 1:
        _draw(canvas, clients[1], 338, 226, size=8)
    # The broker/associate signature rule is shared.  Mark the source's
    # matching role checkbox so a completed agreement identifies the signer.
    if data.get("signer_plan") == "clients_and_associate":
        # ReportLab uses a bottom-origin coordinate system.  On the 06-15-26
        # source, the lower Associate square is at y=242; the earlier y=268
        # mark appeared above both execution choices in the completed PDF.
        _draw_signing_role_check(canvas, 37, 242)
    elif data.get("signer_plan") == "clients_and_broker":
        # The Broker square is the upper of the two execution choices.
        _draw_signing_role_check(canvas, 37, 255)
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
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1507(data, *, client_count=1):
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
        {"api_id": f"txr1507_{role}_initials_p1", "type": "initials", "page": 1, "x": 435, "y": 984, "recipient_id": role, "required": True, "width": 47, "height": 14},
        {"api_id": "txr1507_client1_initials_p1", "type": "initials", "page": 1, "x": 542, "y": 984, "recipient_id": "1", "required": True, "width": 47, "height": 14},
        # Page two's first Client execution line runs from source x=324.1
        # through 576.1 at top-origin y=534.0.  SignWell uses a 4/3 scale.
        # Keep the signature left of the printed Date caption and make each
        # field finish on the actual source rule.  The former map was both
        # left of and above this row in the completed packet.
        {"api_id": "txr1507_client1_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 688, "recipient_id": "1", "required": True, "width": 272, "height": 24},
        {"api_id": "txr1507_client1_date_p2", "type": "date", "page": 2, "x": 720, "y": 694, "recipient_id": "1", "required": True, "width": 48, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1507_client2_initials_p1", "type": "initials", "page": 1, "x": 596, "y": 984, "recipient_id": "2", "required": True, "width": 47, "height": 14},
            # The second Client's signature rule is the lower page-two row
            # (source y=616.8, or SignWell y=822.4), not a second copy of
            # the first Client's field shifted only a small amount down.
            {"api_id": "txr1507_client2_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 798, "recipient_id": "2", "required": True, "width": 272, "height": 24},
            {"api_id": "txr1507_client2_date_p2", "type": "date", "page": 2, "x": 720, "y": 804, "recipient_id": "2", "required": True, "width": 48, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    # The source uses checkboxes to identify whether the broker or the
    # broker's associate signs, followed by one shared signature/date rule.
    # The shared Broker/Associate rule is source x=36.0 through 288.1 at
    # top-origin y=534.0.  It shares the first Client's row.  Use the same
    # rule-ending placement convention as the Client fields, without covering
    # the printed role choices, labels, or date caption.
    role_y = 688
    role_signature_x = 48
    role_date_x = 336
    fields.extend([
        {"api_id": f"txr1507_{role}_signature_p2", "type": "signature", "page": 2, "x": role_signature_x, "y": role_y, "recipient_id": role, "required": True, "width": 240, "height": 24},
        {"api_id": f"txr1507_{role}_date_p2", "type": "date", "page": 2, "x": role_date_x, "y": 694, "recipient_id": role, "required": True, "width": 48, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ])
    return [fields]
