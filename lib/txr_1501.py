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
    canvas.setLineWidth(1.3)
    canvas.line(x, y, x + 7, y + 7)
    canvas.line(x + 7, y + 7, x + 15, y - 4)


def _overlay(data, brokerage, associate):
    clients = data.get("client_names") or []
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    canvas.setFillColorRGB(0, 0, 0)

    broker_name = brokerage.get("legal_name") or brokerage.get("name") or brokerage.get("dba_name") or ""
    broker_license = brokerage.get("license_number") or ""
    associate_name = associate.get("name") or ""
    associate_license = associate.get("license_number") or ""

    # Page 1: party/contact block, market area, and term. These coordinates are
    # deliberately isolated from purchase-packet and TXR-1507 coordinates.
    _draw(canvas, ", ".join(clients), 110, 612)
    _draw(canvas, data.get("client_address"), 145, 594)
    _draw(canvas, data.get("client_city_state_zip"), 190, 578)
    _draw(canvas, data.get("client_phone"), 155, 562)
    _draw(canvas, data.get("client_email"), 155, 546)
    _draw(canvas, broker_name, 145, 531)
    _draw(canvas, brokerage.get("address"), 145, 510)
    _draw(canvas, brokerage.get("city_state_zip"), 220, 494)
    _draw(canvas, brokerage.get("phone"), 155, 478)
    _draw(canvas, brokerage.get("email"), 155, 462)
    _draw_wrapped(canvas, data.get("market_area"), 145, 302, width_chars=86)
    _draw(canvas, data.get("term_start"), 320, 176)
    _draw(canvas, data.get("term_end"), 472, 176)
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
        _check(canvas, 284, 398)
    elif data.get("retainer_treatment") == "not_apply":
        _check(canvas, 321, 398)
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
    _draw(canvas, broker_name, 58, 400, size=7)
    _draw(canvas, broker_license, 240, 400, size=7)
    _draw(canvas, clients[0] if clients else "", 338, 400, size=7)
    _draw(canvas, associate_name, 58, 309, size=7)
    _draw(canvas, associate_license, 240, 309, size=7)
    if len(clients) > 1:
        _draw(canvas, clients[1], 338, 309, size=7)
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
        page.merge_page(overlay.pages[index])
        writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1501(data, *, client_count=1):
    """Return explicit page-6 signer fields for a deliberate signer plan."""
    signer_plan = data.get("signer_plan")
    if signer_plan not in {"clients_and_associate", "clients_and_broker"}:
        raise ValueError("Choose an authorized broker or broker-associate signer for the TXR-1501 agreement.")
    fields = [
        {"api_id": "txr1501_client1_signature_p6", "type": "signature", "page": 6, "x": 533, "y": 587, "recipient_id": "1", "required": True, "width": 120, "height": 26},
        {"api_id": "txr1501_client1_date_p6", "type": "date", "page": 6, "x": 660, "y": 587, "recipient_id": "1", "required": True, "width": 50, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1501_client2_signature_p6", "type": "signature", "page": 6, "x": 533, "y": 702, "recipient_id": "2", "required": True, "width": 120, "height": 26},
            {"api_id": "txr1501_client2_date_p6", "type": "date", "page": 6, "x": 660, "y": 702, "recipient_id": "2", "required": True, "width": 50, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    if signer_plan == "clients_and_associate":
        fields.extend([
            {"api_id": "txr1501_associate_signature_p6", "type": "signature", "page": 6, "x": 200, "y": 605, "recipient_id": "associate", "required": True, "width": 100, "height": 26},
            {"api_id": "txr1501_associate_date_p6", "type": "date", "page": 6, "x": 300, "y": 605, "recipient_id": "associate", "required": True, "width": 40, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    if signer_plan == "clients_and_broker":
        fields.extend([
            {"api_id": "txr1501_broker_signature_p6", "type": "signature", "page": 6, "x": 200, "y": 587, "recipient_id": "broker", "required": True, "width": 100, "height": 26},
            {"api_id": "txr1501_broker_date_p6", "type": "date", "page": 6, "x": 300, "y": 587, "recipient_id": "broker", "required": True, "width": 40, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    return [fields]
