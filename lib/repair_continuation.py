"""Lossless layout for user-entered Paragraph 7D(2) repair descriptions.

This copies the user's terms; it does not draft, summarize, or add obligations.
"""
from io import BytesIO

from pypdf import PdfReader
from reportlab.lib.styles import ParagraphStyle
from lib.pdf_text import text_width as stringWidth
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from lib.pdf_text import paragraph_markup


REFERENCE = "See attached Paragraph 7D(2) repair continuation."
TITLE = "Paragraph 7D(2) - Repair Continuation"
FONT = "Helvetica"
INITIAL_X = {"1": 110, "2": 242, "3": 374, "4": 506}


def active_repair_text(offer):
    choice = str(offer.get("asIs", "")).strip().lower()
    if choice in {"yes", "true", "1"}:
        return ""
    return str(offer.get("repairsText") or "").strip()


def inline_entries(text):
    """Return all text on the printed blanks, or None if any would be lost."""
    raw = " ".join(str(text or "").split())
    if not raw:
        return []
    for quarter in range(38, 24, -1):
        size = quarter / 4
        words = raw.split()
        first = []
        while words and stringWidth(" ".join(first + [words[0]]), FONT, size) <= 246:
            first.append(words.pop(0))
        second = " ".join(words)
        if stringWidth(second, FONT, size) <= 463:
            return [(305, 699, " ".join(first), size), (89, 686, second, size)]
    return None


def repair_text_entries(text):
    entries = inline_entries(text)
    return entries if entries is not None else [(305, 699, REFERENCE, 9.5)]


def _paragraph(text, style):
    # Treat user input as literal text, never ReportLab markup.
    return Paragraph(paragraph_markup(text, style.fontName), style)


def render_repair_continuation(offer):
    text = active_repair_text(offer)
    if inline_entries(text) is not None:
        return None
    return render_text_continuation(offer, TITLE, text)


def render_text_continuation(offer, title, text):
    """Shared layout that copies entered terms without adding obligations."""
    output = BytesIO()
    heading = ParagraphStyle("repair_heading", fontName="Helvetica-Bold", fontSize=14,
                             leading=18, spaceAfter=14)
    detail = ParagraphStyle("repair_detail", fontName=FONT, fontSize=9, leading=12,
                            spaceAfter=5)
    body = ParagraphStyle("repair_body", fontName=FONT, fontSize=10.5, leading=14,
                          splitLongWords=True, allowWidows=0, allowOrphans=0)
    address = str(offer.get('property_address') or '').strip() or ", ".join(str(part).strip() for part in (
        offer.get("address"), offer.get("city"), offer.get("state") or "TX", offer.get("zip")
    ) if str(part or "").strip())
    heading_paragraph = _paragraph(title, heading)
    address_paragraph = _paragraph("Property: " + address, detail)
    _, heading_height = heading_paragraph.wrap(516, 792)
    _, address_height = address_paragraph.wrap(516, 792)
    header_height = heading_height + 14 + address_height + 16
    document = SimpleDocTemplate(output, pagesize=(612, 792), leftMargin=48,
                                 rightMargin=48, topMargin=48 + header_height, bottomMargin=110)
    buyers = " and ".join(str(offer.get(key) or "").strip() for key in
                          ("buyer1", "buyer2") if offer.get(key))
    story = [
        _paragraph("Buyer: " + buyers, detail),
        _paragraph("Seller: " + str(offer.get("seller") or ""), detail),
        Spacer(1, 12),
        _paragraph(text, body),
    ]

    def footer(canvas, doc):
        canvas.saveState()
        # Identify every continuation page even when it is viewed separately.
        heading_paragraph.drawOn(canvas, 48, 744 - heading_height)
        address_paragraph.drawOn(canvas, 48, 744 - heading_height - 14 - address_height)
        canvas.setFont(FONT, 8)
        for recipient, x in INITIAL_X.items():
            label = {"1": "Buyer 1", "2": "Buyer 2", "3": "Seller 1", "4": "Seller 2"}[recipient]
            canvas.drawString(x - 62, 70, label + " initials")
            canvas.line(x, 68, x + 50, 68)
        canvas.drawString(48, 40, title)
        canvas.drawRightString(564, 40, "Page " + str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()


def continuation_field(recipient, page, continuation_index, prefix="repair"):
    """96-DPI SignWell field wholly above its 50-point printed initials line."""
    return {
        "api_id": f"{prefix}_continuation_{continuation_index}_recipient_{recipient}_initials",
        "type": "initials", "page": page, "recipient_id": str(recipient),
        "required": True, "x": INITIAL_X[str(recipient)] * 4 / 3,
        "y": 706 * 4 / 3, "width": 50 * 4 / 3, "height": 16 * 4 / 3,
    }


def continuation_page_count(offer):
    pdf = render_repair_continuation(offer)
    return len(PdfReader(BytesIO(pdf)).pages) if pdf else 0
