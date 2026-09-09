"""Private-source renderer for TXR-1953 residential-lease review drafts."""

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


def _continuation_pdf(property_address, entries):
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(48, 744, "TXR-1953 CONTINUATION EXHIBIT")
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
    canvas.drawString(48, 36, "This exhibit is part of the attached TXR-1953 addendum.")
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    return packet.getvalue()


def _mark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(x, y, "X")


def render_txr_1953(source_pdf_bytes, data):
    """Overlay an unsigned TXR-1953 private review draft on its source PDF."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1953 source must contain exactly one page.")
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    continuation_entries = []
    _draw(canvas, data.get("property_address"), 246, 686, 8)
    status = data.get("lease_status")
    if status == "termination":
        _mark(canvas, 33, 613)
    elif status == "assignment":
        _mark(canvas, 33, 558)
        delivery = data.get("delivery_choice")
        if delivery == "received":
            _mark(canvas, 75, 520)
        elif delivery == "not_received":
            _mark(canvas, 75, 509)
            _draw(canvas, data.get("delivery_days"), 169, 491, 8)
        elif delivery == "oral_notice":
            _mark(canvas, 75, 470)
            oral_notice = _clean(data.get("oral_lease_notice"))
            if pdfmetrics.stringWidth(oral_notice, "Helvetica", 7) <= 468:
                _draw(canvas, oral_notice, 103, 447, 7)
            elif oral_notice:
                _draw(canvas, "See attached continuation exhibit.", 103, 447, 7)
                continuation_entries.append(("Oral Residential Lease Notice", oral_notice))
    explanation = data.get("explanation")
    if explanation:
        explanation_lines = _wrapped_lines(explanation, 480, 6)
        if len(explanation_lines) <= 3:
            for index, line in enumerate(explanation_lines):
                _draw(canvas, line, 84, 279 - (index * 11), 6)
        else:
            _draw(canvas, "See attached continuation exhibit.", 84, 279, 6)
            continuation_entries.append(("Residential Lease Explanation", explanation))
    if not data.get("_for_signing"):
        buyers = data.get("buyer_names") or []
        sellers = data.get("seller_names") or []
        _draw(canvas, buyers[0] if buyers else "", 55, 178, 8)
        _draw(canvas, sellers[0] if sellers else "", 329, 178, 8)
        if len(buyers) > 1:
            _draw(canvas, buyers[1], 55, 122, 8)
        if len(sellers) > 1:
            _draw(canvas, sellers[1], 329, 122, 8)
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    writer = PdfWriter()
    writer.add_page(source.pages[0])
    writer.pages[0].merge_page(overlay.pages[0])
    if continuation_entries:
        exhibit = PdfReader(BytesIO(_continuation_pdf(data.get("property_address"), continuation_entries)))
        for page in exhibit.pages:
            writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1953(data, *, client_count=None):
    """Return source-specific Buyer and Seller signature fields.

    TXR-1953 is a contract addendum signed by the named Buyers and Sellers;
    it does not add an agent or broker signer. SignWell uses a 96-DPI,
    top-origin letter-page coordinate space in the HomeOfferFlow integration.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1953 requires one or two Buyers and one or two Sellers.")

    fields = [
        {"api_id": "txr1953_buyer1_signature_p1", "type": "signature", "page": 1, "x": 70, "y": 802, "recipient_id": "1", "required": True, "width": 190, "height": 26},
        {"api_id": "txr1953_seller1_signature_p1", "type": "signature", "page": 1, "x": 440, "y": 802, "recipient_id": str(len(buyers) + 1), "required": True, "width": 190, "height": 26},
    ]
    if len(buyers) == 2:
        fields.append(
            {"api_id": "txr1953_buyer2_signature_p1", "type": "signature", "page": 1, "x": 70, "y": 875, "recipient_id": "2", "required": True, "width": 190, "height": 26}
        )
    if len(sellers) == 2:
        fields.append(
            {"api_id": "txr1953_seller2_signature_p1", "type": "signature", "page": 1, "x": 440, "y": 875, "recipient_id": str(len(buyers) + 2), "required": True, "width": 190, "height": 26}
        )
    return [fields]
