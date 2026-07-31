"""Private-source renderer and signer map for TXR-1506 consumer notice."""

from io import BytesIO
from textwrap import wrap

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


def _draw_wrapped(canvas, value, x, y, width_chars=96, line_height=10, size=8):
    value = _clean(value)
    if not value:
        return
    for index, line in enumerate(wrap(value, width_chars)):
        _draw(canvas, line, x, y - index * line_height, size=size)


def _overlay(data, brokerage):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    broker_name = brokerage.get("legal_name") or brokerage.get("name") or brokerage.get("dba_name") or ""
    clients = data.get("client_names") or []
    for page_index in range(5):
        # Each source page has two optional consumer initial blanks at the
        # footer. Initials are supplied by SignWell, not written into the PDF.
        canvas.showPage()

    # Page 6: optional Other text, provider printed name, and consumer names.
    _draw_wrapped(canvas, data.get("additional_notice"), 52, 318, width_chars=100, line_height=10)
    _draw(canvas, broker_name, 55, 210)
    _draw(canvas, clients[0] if clients else "", 55, 102)
    if len(clients) > 1:
        _draw(canvas, clients[1], 55, 66)
    canvas.save()
    packet.seek(0)
    return packet.read()


def render_txr_1506(source_pdf_bytes, data, brokerage):
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 6:
        raise ValueError("TXR-1506 source must contain exactly six pages.")
    overlay = PdfReader(BytesIO(_overlay(data, brokerage)))
    writer = PdfWriter()
    for index, page in enumerate(source.pages):
        page.merge_page(overlay.pages[index])
        writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1506(data, *, client_count=1):
    """Return explicit receipt-initial and signature/date fields."""
    signer_plan = data.get("signer_plan")
    if signer_plan not in {"consumers_and_associate", "consumers_and_broker"}:
        raise ValueError("Choose an authorized broker or broker-associate signer for the TXR-1506 notice.")
    fields = []
    for page in range(1, 6):
        fields.append({"api_id": f"txr1506_client1_initials_p{page}", "type": "initials", "page": page, "x": 520, "y": 1000, "recipient_id": "1", "required": True, "width": 44, "height": 16})
        if client_count == 2:
            fields.append({"api_id": f"txr1506_client2_initials_p{page}", "type": "initials", "page": page, "x": 620, "y": 1000, "recipient_id": "2", "required": True, "width": 44, "height": 16})
    fields.extend([
        {"api_id": "txr1506_client1_signature_p6", "type": "signature", "page": 6, "x": 60, "y": 830, "recipient_id": "1", "required": True, "width": 190, "height": 26},
        {"api_id": "txr1506_client1_date_p6", "type": "date", "page": 6, "x": 455, "y": 830, "recipient_id": "1", "required": True, "width": 88, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ])
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1506_client2_signature_p6", "type": "signature", "page": 6, "x": 60, "y": 895, "recipient_id": "2", "required": True, "width": 190, "height": 26},
            {"api_id": "txr1506_client2_date_p6", "type": "date", "page": 6, "x": 455, "y": 895, "recipient_id": "2", "required": True, "width": 88, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    role = "associate" if signer_plan == "consumers_and_associate" else "broker"
    fields.extend([
        {"api_id": f"txr1506_{role}_signature_p6", "type": "signature", "page": 6, "x": 60, "y": 760, "recipient_id": role, "required": True, "width": 190, "height": 26},
        {"api_id": f"txr1506_{role}_date_p6", "type": "date", "page": 6, "x": 330, "y": 760, "recipient_id": role, "required": True, "width": 88, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ])
    return [fields]
