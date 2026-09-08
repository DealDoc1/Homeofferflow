"""Private-source renderer for TXR-1954 fixture-lease review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
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


def _wrapped_lines(value, max_width, size):
    words = _clean(value).split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or pdfmetrics.stringWidth(candidate, "Helvetica", size) <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def _draw_or_continue(canvas, value, x, y, max_width, label, entries, size=7):
    value = _clean(value)
    if not value:
        return
    if pdfmetrics.stringWidth(value, "Helvetica", size) <= max_width:
        _draw(canvas, value, x, y, size)
        return
    _draw(canvas, "See attached exhibit.", x, y, 6)
    entries.append((label, value))


def _continuation_pdf(property_address, entries):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(48, 744, "TXR-1954 CONTINUATION EXHIBIT")
    canvas.setFont("Helvetica", 9)
    canvas.drawString(48, 724, f"Property: {_clean(property_address)}")
    y = 692
    for label, value in entries:
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(48, y, label)
        y -= 15
        canvas.setFont("Helvetica", 8)
        for line in _wrapped_lines(value, 516, 8):
            canvas.drawString(48, y, line)
            y -= 12
        y -= 12
    canvas.setFont("Helvetica-Oblique", 7)
    canvas.drawString(48, 36, "This exhibit is part of the attached TXR-1954 addendum.")
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    return packet.getvalue()


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
    continuation_entries = []
    _draw(canvas, data.get("property_address"), 248, 660, 8)

    leased = set(data.get("leased_fixture_types") or [])
    _marks(canvas, ["solar_panels" in leased, "propane_tanks" in leased, "water_softener" in leased, "security_system" in leased, "other" in leased],
           [(77, 597), (166, 597), (263, 597), (363, 597), (466, 597)])
    _draw_or_continue(canvas, data.get("leased_fixtures_other"), 480, 597, 96, "Other Leased Fixture", continuation_entries, 6)

    assumed = set(data.get("assumed_fixture_leases") or [])
    _marks(canvas, ["solar_panels" in assumed, "propane_tanks" in assumed, "water_softener" in assumed, "security_system" in assumed],
           [(88, 551), (201, 551), (319, 551), (456, 551)])
    if "other" in assumed:
        _mark(canvas, 85, 536)
        _draw_or_continue(canvas, data.get("assumed_fixture_leases_other"), 99, 537, 239, "Other Assumed Fixture Lease", continuation_entries, 7)
    _draw(canvas, data.get("buyer_first_cost"), 493, 536, 8)

    if data.get("removal_choice") == "will":
        _mark(canvas, 206, 479)
    elif data.get("removal_choice") == "will_not":
        _mark(canvas, 252, 479)

    delivery = data.get("delivery_choice")
    if delivery == "received":
        _mark(canvas, 49, 411)
    elif delivery == "not_received":
        _mark(canvas, 49, 396)
    elif delivery == "oral_notice":
        _mark(canvas, 49, 350)
        _draw_or_continue(canvas, data.get("oral_fixture_lease_notice"), 455, 326, 120, "Oral Fixture Lease Notice", continuation_entries, 7)

    if not data.get("_for_signing"):
        buyers = data.get("buyer_names") or []
        sellers = data.get("seller_names") or []
        _draw(canvas, buyers[0] if buyers else "", 80, 201, 8)
        _draw(canvas, sellers[0] if sellers else "", 320, 201, 8)
        if len(buyers) > 1:
            _draw(canvas, buyers[1], 80, 123, 8)
        if len(sellers) > 1:
            _draw(canvas, sellers[1], 320, 123, 8)
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    source.pages[0].merge_page(overlay.pages[0])
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    if continuation_entries:
        exhibit = PdfReader(BytesIO(_continuation_pdf(data.get("property_address"), continuation_entries)))
        for page in exhibit.pages:
            writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1954(data, *, client_count=None):
    """Return source-specific Buyer and Seller signature fields.

    TXR-1954 is signed by the transaction parties only. Recipient ids follow
    the stored Buyer-then-Seller name order used by the authenticated signing
    route, so no brokerage seat or agent signature is inferred.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1954 requires one or two Buyers and one or two Sellers.")

    fields = [
        {"api_id": "txr1954_buyer1_signature_p1", "type": "signature", "page": 1, "x": 64, "y": 774, "recipient_id": "1", "required": True, "width": 200, "height": 26},
        {"api_id": "txr1954_seller1_signature_p1", "type": "signature", "page": 1, "x": 418, "y": 774, "recipient_id": str(len(buyers) + 1), "required": True, "width": 200, "height": 26},
    ]
    if len(buyers) == 2:
        fields.append(
            {"api_id": "txr1954_buyer2_signature_p1", "type": "signature", "page": 1, "x": 64, "y": 845, "recipient_id": "2", "required": True, "width": 200, "height": 26}
        )
    if len(sellers) == 2:
        fields.append(
            {"api_id": "txr1954_seller2_signature_p1", "type": "signature", "page": 1, "x": 418, "y": 845, "recipient_id": str(len(buyers) + 2), "required": True, "width": 200, "height": 26}
        )
    return [fields]
