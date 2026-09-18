"""Preserve the full user-entered TREC 57-0 Paragraph A item inventory."""
from io import BytesIO
from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from lib.repair_continuation import render_text_continuation


TITLE = "Non-Realty Items - Paragraph A Continuation"
REFERENCE = "See attached Non-Realty Items - Paragraph A Continuation."
# Top edges of the eleven original TREC 57-0 description rules, in PDF points.
RULE_TOPS = (248.72, 267.56, 286.41, 305.25, 324.09, 342.94,
             361.78, 380.63, 399.47, 418.31, 436.69)


def description(offer):
    for key in ("nonRealtyDescription", "nonRealtyItemsDescription",
                "nonRealtyItemsText", "personalPropertyDescription"):
        value = offer.get(key)
        if value is not None and value != "":
            return str(value)
    return ""


def inline_entries(text):
    """Use all eleven measured blanks, or request a complete continuation."""
    if not str(text or "").strip():
        return []
    lines = []
    for paragraph in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = ""
        for word in paragraph.split():
            if stringWidth(word, "Helvetica", 9) > 501:
                return None
            trial = (line + " " + word).strip()
            if stringWidth(trial, "Helvetica", 9) <= 501:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
        if len(lines) > len(RULE_TOPS):
            return None
    return [(65, round(792 - rule + 2.72, 2), line, 9)
            for rule, line in zip(RULE_TOPS, lines)]


def text_entries(text):
    entries = inline_entries(text)
    return entries if entries is not None else [(65, 546, REFERENCE, 9)]


def render_nonrealty_continuation(offer):
    selected = str(offer.get("nonRealtyItems") or "no").strip().lower() in {"yes", "true", "1", "on"}
    text = description(offer)
    if not selected or inline_entries(text) is not None:
        return None
    return render_text_continuation(offer, TITLE, text)


def continuation_page_count(offer):
    pdf = render_nonrealty_continuation(offer)
    return len(PdfReader(BytesIO(pdf)).pages) if pdf else 0
