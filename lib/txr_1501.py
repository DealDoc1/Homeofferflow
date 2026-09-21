"""Private-source renderer and signer map for TXR-1501 Long Form.

The authorized TXR-1501 source is supplied privately by a brokerage and is
never checked into the repository. This module only overlays explicitly
entered, broker-approved intake values and returns source-specific SignWell
field metadata. It does not select a form, infer compensation, or send/sign a
document.
"""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.pdf_text import draw_text, text_width as stringWidth
from lib.txr1501_answers import answer_layout, render_continuation, continuation_fields
from lib.txr_source_imprint import remove_known_source_imprint


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
    draw_text(canvas, value, x, y, size, FONT)


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


def _draw_party_header(canvas, clients, broker_name):
    """Repeat party identification within the source blank on pages 2-6."""
    parties = " and ".join(filter(None, (
        ", ".join(filter(None, (_clean(name) for name in clients))), _clean(broker_name),
    )))
    # All five source headers share x=244.13..576.10, rule top y=42.48.
    # Keep complete names readable; refer to the full party block if too long.
    for size in (8, 7.5, 7):
        if stringWidth(parties, FONT, size) <= 328:
            _draw(canvas, parties, 246, 752, size=size)
            return
    _draw(canvas, "Client(s) and Broker identified in Paragraph 1", 246, 752, size=8)


def _overlay(data, brokerage, associate):
    clients = data.get("client_names") or []
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    canvas.setFillColorRGB(0, 0, 0)

    broker_name = brokerage.get("legal_name") or brokerage.get("name") or brokerage.get("dba_name") or ""
    # The authenticated profile stores its display name as ``agent_name``;
    # accept the normalized renderer shape as well.  Without this fallback a
    # real agent can be the SignWell recipient while their printed name is
    # blank on the completed agreement.
    pages, overflow = answer_layout(data, brokerage, associate)
    def draw_page(number):
        for x, y, value, size in pages[number]:
            _draw(canvas, value, x, y, size=size)

    # Page 1: party/contact block, market area, and term. These coordinates are
    # deliberately isolated from purchase-packet and TXR-1507 coordinates.
    # Anchor each value at the beginning of the printed rule.  The previous
    # positions were measured from the label, leaving completed values visibly
    # adrift in the middle of the rule on the released TXR-1501 source.
    draw_page(1)
    canvas.showPage()

    # Page 2: broker/client agreement title and compensation terms.
    _draw_party_header(canvas, clients, broker_name)
    draw_page(2)
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
    _draw_party_header(canvas, clients, broker_name)
    draw_page(3)
    canvas.showPage()

    # Page 4: intermediary choice. A and B checkboxes are visibly distinct.
    _draw_party_header(canvas, clients, broker_name)
    if data.get("intermediary") == "authorized":
        _check(canvas, 45, 707)
    else:
        _check(canvas, 45, 455)
    canvas.showPage()

    # Page 5: Special Provisions is intentionally blank unless a future,
    # separately approved field is added; do not write into boilerplate.
    _draw_party_header(canvas, clients, broker_name)
    draw_page(5)
    if overflow:
        _check(canvas, 64, 276)
    canvas.showPage()

    # Page 6: printed names only. Signature/date widgets are supplied to
    # SignWell after the broker or associate signer plan is selected.
    _draw_party_header(canvas, clients, broker_name)
    draw_page(6)
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
    for page in source.pages:
        # Attach the source page before merging.  Newer pypdf versions no
        # longer guarantee reliable content replacement on detached pages.
        writer.add_page(page)
    remove_known_source_imprint(writer, source_pdf_bytes, 'TXR-1501')
    for index in range(len(source.pages)):
        writer.pages[index].merge_page(overlay.pages[index])
    continuation = render_continuation(data, answer_layout(data, brokerage, associate)[1])
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1501(data, *, client_count=1, page_count=6):
    """Return footer initials and final signatures for the selected parties."""
    signer_plan = data.get("signer_plan")
    if signer_plan not in {"clients_and_associate", "clients_and_broker"}:
        raise ValueError("Choose whether the broker or associate will sign the TXR-1501 agreement.")
    fields = [
        # The execution row is below the printed-name line.  The previous
        # map used the name-line y-coordinate, which made completed fields
        # cover the printed names rather than the signature rule.
        # The Client execution rule begins at source x=324, not beside the
        # broker column. Leave a separate 54-point date area: provider-rendered
        # MM/DD/YYYY text measured 49.21 points in the short-form QA specimen,
        # wider than the old 36-point date widget. Keep both inside the rule.
        {"api_id": "txr1501_client1_signature_p6", "type": "signature", "page": 6, "x": 432, "y": 566, "recipient_id": "1", "required": True, "width": 240, "height": 24},
        {"api_id": "txr1501_client1_date_p6", "type": "date", "page": 6, "x": 696, "y": 572, "recipient_id": "1", "required": True, "width": 72, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1501_client2_signature_p6", "type": "signature", "page": 6, "x": 432, "y": 677, "recipient_id": "2", "required": True, "width": 240, "height": 24},
            {"api_id": "txr1501_client2_date_p6", "type": "date", "page": 6, "x": 696, "y": 683, "recipient_id": "2", "required": True, "width": 72, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    if signer_plan == "clients_and_associate":
        fields.extend([
            # The 06-15-26 source has ONE left execution rule, above two role
            # checkboxes. The lower left rule is for the associate's PRINTED
            # name, not a second signature. Both selected roles sign here.
            {"api_id": "txr1501_associate_signature_p6", "type": "signature", "page": 6, "x": 48, "y": 566, "recipient_id": "associate", "required": True, "width": 240, "height": 24},
            {"api_id": "txr1501_associate_date_p6", "type": "date", "page": 6, "x": 312, "y": 572, "recipient_id": "associate", "required": True, "width": 72, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    if signer_plan == "clients_and_broker":
        fields.extend([
            {"api_id": "txr1501_broker_signature_p6", "type": "signature", "page": 6, "x": 48, "y": 566, "recipient_id": "broker", "required": True, "width": 240, "height": 24},
            {"api_id": "txr1501_broker_date_p6", "type": "date", "page": 6, "x": 312, "y": 572, "recipient_id": "broker", "required": True, "width": 72, "height": 18, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    role = 'associate' if signer_plan == 'clients_and_associate' else 'broker'
    # Pages 1-5 identify the document with initials from each signing party.
    # Source underscore blanks are 325.982..361.064, 406.523..444.026 and
    # 446.555..481.529 on page 1; later client blanks move <0.35pt right.
    # These rectangles fit the common intersection on every page.
    initial_signers = [(role, role, 435), ('client1', '1', 543)]
    if client_count == 2:
        initial_signers.append(('client2', '2', 596))
    for page in range(1, 6):
        for label, recipient, x in initial_signers:
            fields.append({'api_id': f'txr1501_{label}_initials_p{page}',
                           'type': 'initials', 'page': page, 'x': x, 'y': 976,
                           'recipient_id': recipient, 'required': True,
                           'width': 45 if recipient == '1' else 46, 'height': 14})
    fields.extend(continuation_fields(data, client_count, page_count))
    return [fields]
