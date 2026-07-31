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
    c.setLineWidth(1.4)
    c.line(x, y, x + 7, y + 7)
    c.line(x + 7, y + 7, x + 15, y - 4)


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
        _draw_check(canvas, 57, 455)
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
        # TXR-1507's first intermediary box is near x=177 on the source page;
        # x=211 lands between the two printed boxes.
        _draw_check(canvas, 177, 628)
    else:
        _draw_check(canvas, 345, 628)

    broker_name = brokerage.get("legal_name") or brokerage.get("name") or brokerage.get("dba_name")
    broker_license = brokerage.get("license_number") or ""
    associate_name = associate.get("name") or ""
    associate_license = associate.get("license_number") or ""
    _draw(canvas, broker_name, 56, 296, size=8)
    _draw(canvas, broker_license, 238, 296, size=8)
    _draw(canvas, ", ".join(clients[:1]), 338, 296, size=8)
    _draw(canvas, associate_name, 56, 226, size=8)
    _draw(canvas, associate_license, 238, 226, size=8)
    if len(clients) > 1:
        _draw(canvas, clients[1], 338, 226, size=8)
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
        page.merge_page(overlay.pages[index])
        writer.add_page(page)
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
    fields = [
        {"api_id": "txr1507_client1_initials_p1", "type": "initials", "page": 1, "x": 444, "y": 1003, "recipient_id": "1", "required": True, "width": 32, "height": 14},
        {"api_id": "txr1507_client1_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 666, "recipient_id": "1", "required": True, "width": 190, "height": 26},
        {"api_id": "txr1507_client1_date_p2", "type": "date", "page": 2, "x": 660, "y": 666, "recipient_id": "1", "required": True, "width": 88, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
    ]
    if client_count == 2:
        fields.extend([
            {"api_id": "txr1507_client2_initials_p1", "type": "initials", "page": 1, "x": 494, "y": 1003, "recipient_id": "2", "required": True, "width": 32, "height": 14},
            {"api_id": "txr1507_client2_signature_p2", "type": "signature", "page": 2, "x": 432, "y": 784, "recipient_id": "2", "required": True, "width": 190, "height": 26},
            {"api_id": "txr1507_client2_date_p2", "type": "date", "page": 2, "x": 660, "y": 784, "recipient_id": "2", "required": True, "width": 88, "height": 20, "date_format": "MM/DD/YYYY", "lock_sign_date": True},
        ])
    return [fields]
