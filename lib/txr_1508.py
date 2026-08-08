"""Private-source renderer and signer map for TXR-1508.

TXR-1508 is strictly an unrepresented-customer showing acknowledgement. It
must never be used to imply representation, compensation, advice, or other
brokerage services.
"""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, *, size=8):
    value = _clean(value)
    if not value:
        return
    canvas.setFont("Helvetica", size)
    canvas.drawString(x, y, value)


def _check(canvas, x, y):
    canvas.setLineWidth(1.3)
    canvas.line(x, y, x + 7, y + 7)
    canvas.line(x + 7, y + 7, x + 15, y - 4)


def _overlay(data, brokerage, associate):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    broker_name = brokerage.get("legal_name") or brokerage.get("name") or brokerage.get("dba_name") or ""
    broker_license = brokerage.get("license_number") or ""
    associate_name = associate.get("name") or ""
    associate_license = associate.get("license_number") or ""
    clients = data.get("client_names") or []
    other_broker = data.get("other_broker_agreement") or []

    # Coordinates are specific to the approved one-page TXR-1508 source.
    _draw(canvas, data.get("property_address"), 110, 650)
    _draw(canvas, broker_name, 190, 316)
    _draw(canvas, broker_license, 482, 316)
    _draw(canvas, associate_name, 195, 297)
    _draw(canvas, associate_license, 482, 297)
    _draw(canvas, clients[0] if clients else "", 140, 231)
    if len(clients) > 1:
        _draw(canvas, clients[1], 140, 188)
    if other_broker and other_broker[0] == "yes":
        _check(canvas, 299, 218)
    if len(other_broker) > 1 and other_broker[1] == "yes":
        _check(canvas, 299, 175)
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1508(source_pdf_bytes, data, brokerage, associate):
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1508 source must contain exactly one page.")
    overlay = PdfReader(BytesIO(_overlay(data, brokerage, associate)))
    writer = PdfWriter()
    source.pages[0].merge_page(overlay.pages[0])
    writer.add_page(source.pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1508(data, *, client_count=1):
    """Return explicit acknowledgement initials/date fields.

    The signer role is deliberate: the form may be acknowledged by the broker
    or the broker's associate, plus each unrepresented customer.
    """
    signer_plan = data.get("signer_plan")
    if signer_plan not in {"associate_and_clients", "broker_and_clients"}:
        raise ValueError("Choose whether the broker or associate will acknowledge TXR-1508.")
    fields = [
        {"api_id": "txr1508_agent_initials_p1", "type": "initials", "page": 1, "x": 520, "y": 672, "recipient_id": "associate" if signer_plan == "associate_and_clients" else "broker", "required": True, "width": 72, "height": 18},
        {"api_id": "txr1508_agent_date_p1", "type": "date", "page": 1, "x": 625, "y": 672, "recipient_id": "associate" if signer_plan == "associate_and_clients" else "broker", "required": True, "width": 88, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        {"api_id": "txr1508_client1_initials_p1", "type": "initials", "page": 1, "x": 520, "y": 728, "recipient_id": "1", "required": True, "width": 72, "height": 18},
        {"api_id": "txr1508_client1_date_p1", "type": "date", "page": 1, "x": 625, "y": 728, "recipient_id": "1", "required": True, "width": 88, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1508_client2_initials_p1", "type": "initials", "page": 1, "x": 520, "y": 785, "recipient_id": "2", "required": True, "width": 72, "height": 18},
            {"api_id": "txr1508_client2_date_p1", "type": "date", "page": 1, "x": 625, "y": 785, "recipient_id": "2", "required": True, "width": 88, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    return [fields]
