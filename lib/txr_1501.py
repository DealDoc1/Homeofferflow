"""Private-source renderer and signer map for TXR-1501 Long Form.

The authorized TXR-1501 source is supplied privately by a brokerage and is
never checked into the repository. This module only overlays explicitly
entered, broker-approved intake values and returns source-specific SignWell
field metadata. It does not select a form, infer compensation, or send/sign a
document.
"""

from io import BytesIO
from textwrap import wrap

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
FONT = "Helvetica"
FONT_SIZE = 8


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, *, size=FONT_SIZE):
    value = _clean(value)
    if not value:
        return
    canvas.setFont(FONT, size)
    canvas.drawString(x, y, value)


def _draw_wrapped(canvas, value, x, y, width_chars=84, line_height=10, size=FONT_SIZE):
    value = _clean(value)
    if not value:
        return
    for index, line in enumerate(wrap(value, width_chars)):
        _draw(canvas, line, x, y - index * line_height, size=size)


def _check(canvas, x, y):
    """Draw a compact check inside a small source checkbox."""
    canvas.setLineWidth(1.3)
    canvas.line(x + 1, y + 3, x + 3.5, y + .5)
    canvas.line(x + 3.5, y + .5, x + 7, y + 6)


def _check_signing_role(canvas, x, y):
    """Mark one of the compact broker/associate execution boxes.

    The source's execution boxes are appreciably smaller than the service
    option boxes.  Keep the mark inside the printed square so the selected
    signer role remains legible in a completed packet.
    """
    canvas.setLineWidth(1.1)
    canvas.line(x + 1, y + 1, x + 7, y + 7)
    canvas.line(x + 1, y + 7, x + 7, y + 1)


def _overlay(data, brokerage, associate):
    clients = data.get("client_names") or []
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    canvas.setFillColorRGB(0, 0, 0)

    broker_name = brokerage.get("legal_name") or brokerage.get("name") or brokerage.get("dba_name") or ""
    broker_license = brokerage.get("license_number") or ""
    # The authenticated profile stores its display name as ``agent_name``;
    # accept the normalized renderer shape as well.  Without this fallback a
    # real agent can be the SignWell recipient while their printed name is
    # blank on the completed agreement.
    associate_name = associate.get("name") or associate.get("agent_name") or ""
    associate_license = associate.get("license_number") or ""

    # Page 1: party/contact block, market area, and term. These coordinates are
    # deliberately isolated from purchase-packet and TXR-1507 coordinates.
    # Anchor each value at the beginning of the printed rule.  The previous
    # positions were measured from the label, leaving completed values visibly
    # adrift in the middle of the rule on the released TXR-1501 source.
    _draw(canvas, ", ".join(clients), 108, 612)
    _draw(canvas, data.get("client_address"), 128, 594)
    _draw(canvas, data.get("client_city_state_zip"), 158, 578)
    _draw(canvas, data.get("client_phone"), 117, 562)
    _draw(canvas, data.get("client_email"), 115, 546)
    _draw(canvas, broker_name, 108, 531)
    _draw(canvas, brokerage.get("address"), 125, 510)
    _draw(canvas, brokerage.get("city_state_zip"), 156, 494)
    _draw(canvas, brokerage.get("phone"), 117, 478)
    _draw(canvas, brokerage.get("email"), 112, 462)
    _draw_wrapped(canvas, data.get("market_area"), 145, 302, width_chars=86)
    _draw(canvas, data.get("term_start"), 224, 176)
    _draw(canvas, data.get("term_end"), 430, 176)
    canvas.showPage()

    # Page 2: broker/client agreement title and compensation terms.
    _draw(canvas, ", ".join(clients), 300, 744, size=7)
    compensation = data.get("compensation") or {}
    _draw(canvas, compensation.get("purchase_percentage"), 210, 480)
    _draw(canvas, compensation.get("purchase_flat_fee"), 475, 480)
    _draw(canvas, compensation.get("lease_one_month_percentage"), 225, 460)
    _draw(canvas, compensation.get("lease_total_rents_percentage"), 385, 460)
    _draw(canvas, compensation.get("lease_flat_fee"), 470, 442)
    _draw(canvas, data.get("retainer_amount"), 220, 418)
    if data.get("retainer_treatment") == "apply":
        # The page-two “will” selection square starts at x=262/y=414.
        # The older x=284/y=398 map marked the surrounding sentence below
        # and to the right of the printed cell.
        _check(canvas, 262, 414)
    elif data.get("retainer_treatment") == "not_apply":
        # The “will not” square is the separate cell at x=320 on the same
        # line, not the beginning of the printed words that follow it.
        _check(canvas, 320, 414)
    canvas.showPage()

    # Page 3: service-provider compensation, protection period, and county.
    _draw(canvas, data.get("protection_days"), 240, 470)
    _draw(canvas, data.get("payment_county"), 470, 312)
    canvas.showPage()

    # Page 4: intermediary choice. A and B checkboxes are visibly distinct.
    if data.get("intermediary") == "authorized":
        _check(canvas, 48, 712)
    else:
        _check(canvas, 48, 480)
    canvas.showPage()

    # Page 5: Special Provisions is intentionally blank unless a future,
    # separately approved field is added; do not write into boilerplate.
    canvas.showPage()

    # Page 6: printed names only. Signature/date widgets are supplied to
    # SignWell after a source-owner signer plan is deliberately selected.
    _draw(canvas, broker_name, 36, 400, size=7)
    _draw(canvas, broker_license, 240, 400, size=7)
    _draw(canvas, clients[0] if clients else "", 324, 400, size=7)
    _draw(canvas, associate_name, 36, 309, size=7)
    _draw(canvas, associate_license, 240, 309, size=7)
    if len(clients) > 1:
        _draw(canvas, clients[1], 324, 309, size=7)
    # The chosen signer must also be visible on the source's broker versus
    # broker-associate checkbox pair.  A signature alone on the shared rule
    # leaves the completed agreement ambiguous.
    if data.get("signer_plan") == "clients_and_associate":
        # The Associate square spans source x=36..44 and bottom-origin
        # y=327..336. Earlier coordinates started left of and below the
        # printed cell, leaving its intended X effectively invisible.
        _check_signing_role(canvas, 36, 327)
    elif data.get("signer_plan") == "clients_and_broker":
        # The Broker square directly above spans y=338..347.
        _check_signing_role(canvas, 36, 338)
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1501(source_pdf_bytes, data, brokerage, associate):
    """Overlay approved values onto the exact six-page private source."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 6:
        raise ValueError("TXR-1501 source must contain exactly six pages.")
    overlay = PdfReader(BytesIO(_overlay(data, brokerage, associate)))
    writer = PdfWriter()
    for index, page in enumerate(source.pages):
        # Attach the source page before merging.  Newer pypdf versions no
        # longer guarantee reliable content replacement on detached pages.
        writer.add_page(page)
        writer.pages[index].merge_page(overlay.pages[index])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1501(data, *, client_count=1):
    """Return explicit page-6 signer fields for a deliberate signer plan."""
    signer_plan = data.get("signer_plan")
    if signer_plan not in {"clients_and_associate", "clients_and_broker"}:
        raise ValueError("Choose whether the broker or associate will sign the TXR-1501 agreement.")
    fields = [
        # The execution row is below the printed-name line.  The previous
        # map used the name-line y-coordinate, which made completed fields
        # cover the printed names rather than the signature rule.
        # The Client execution rule begins at source x=324, not beside the
        # broker column.  SignWell uses 4/3 source coordinates, so the
        # signature and date rectangles begin at 432 and 720 respectively.
        # The date starts just above its printed caption rather than replacing
        # the "Client's Signature" label.
        {"api_id": "txr1501_client1_signature_p6", "type": "signature", "page": 6, "x": 432, "y": 590, "recipient_id": "1", "required": True, "width": 272, "height": 24},
        {"api_id": "txr1501_client1_date_p6", "type": "date", "page": 6, "x": 720, "y": 596, "recipient_id": "1", "required": True, "width": 48, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1501_client2_signature_p6", "type": "signature", "page": 6, "x": 432, "y": 700, "recipient_id": "2", "required": True, "width": 272, "height": 24},
            {"api_id": "txr1501_client2_date_p6", "type": "date", "page": 6, "x": 720, "y": 706, "recipient_id": "2", "required": True, "width": 48, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    if signer_plan == "clients_and_associate":
        fields.extend([
            # The associate selection is below the execution row, but the
            # selected associate signs on the shared upper broker execution
            # line. The lower right row is reserved for a second client.
            {"api_id": "txr1501_associate_signature_p6", "type": "signature", "page": 6, "x": 48, "y": 590, "recipient_id": "associate", "required": True, "width": 240, "height": 24},
            {"api_id": "txr1501_associate_date_p6", "type": "date", "page": 6, "x": 336, "y": 596, "recipient_id": "associate", "required": True, "width": 48, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    if signer_plan == "clients_and_broker":
        fields.extend([
            {"api_id": "txr1501_broker_signature_p6", "type": "signature", "page": 6, "x": 48, "y": 590, "recipient_id": "broker", "required": True, "width": 240, "height": 24},
            {"api_id": "txr1501_broker_date_p6", "type": "date", "page": 6, "x": 336, "y": 596, "recipient_id": "broker", "required": True, "width": 48, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    return [fields]
