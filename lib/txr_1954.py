"""Private-source renderer for TXR-1954 fixture-lease review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, size=7):
    value = _clean(value)
    if value:
        canvas.setFont("Helvetica", size)
        canvas.drawString(x, y, value)


def _mark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(x, y, "X")


def _marks(canvas, values, positions):
    for value, position in zip(values, positions):
        if value:
            _mark(canvas, *position)


def render_txr_1954(source_pdf_bytes, data):
    """Overlay an unsigned TXR-1954 private review draft on its source PDF."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1954 source must contain exactly one page.")
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    _draw(canvas, data.get("property_address"), 248, 660, 8)

    leased = set(data.get("leased_fixture_types") or [])
    _marks(canvas, ["solar_panels" in leased, "propane_tanks" in leased, "water_softener" in leased, "security_system" in leased, "other" in leased],
           [(77, 597), (166, 597), (263, 597), (363, 597), (466, 597)])
    _draw(canvas, data.get("leased_fixtures_other"), 480, 597, 6)

    assumed = set(data.get("assumed_fixture_leases") or [])
    _marks(canvas, ["solar_panels" in assumed, "propane_tanks" in assumed, "water_softener" in assumed, "security_system" in assumed],
           [(88, 551), (201, 551), (319, 551), (456, 551)])
    if "other" in assumed:
        _mark(canvas, 148, 536)
        _draw(canvas, data.get("assumed_fixture_leases_other"), 165, 537, 7)
    _draw(canvas, data.get("buyer_first_cost"), 493, 536, 8)

    if data.get("removal_choice") == "will":
        _mark(canvas, 206, 492)
    elif data.get("removal_choice") == "will_not":
        _mark(canvas, 419, 492)

    delivery = data.get("delivery_choice")
    if delivery == "received":
        _mark(canvas, 80, 410)
    elif delivery == "not_received":
        _mark(canvas, 80, 395)
    elif delivery == "oral_notice":
        _mark(canvas, 80, 369)
        _draw(canvas, data.get("oral_fixture_lease_notice"), 392, 326, 7)

    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    _draw(canvas, buyers[0] if buyers else "", 80, 201, 8)
    _draw(canvas, sellers[0] if sellers else "", 320, 201, 8)
    if len(buyers) > 1:
        _draw(canvas, buyers[1], 80, 123, 8)
    if len(sellers) > 1:
        _draw(canvas, sellers[1], 320, 123, 8)
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    source.pages[0].merge_page(overlay.pages[0])
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
