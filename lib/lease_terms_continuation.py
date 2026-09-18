"""Preserve entered temporary-lease Paragraph 11 terms without summarizing."""
from io import BytesIO

from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from lib.repair_continuation import render_text_continuation


BLANKS = {
    "buyer": [(182, 263, 384)] + [(49, y, 518) for y in (252, 241, 230, 219, 208, 197, 186)],
    "seller": [(183, 305, 386)] + [(51, y, 518) for y in (294, 283, 272, 261, 250, 239, 228, 217, 206, 195, 184)],
}
REFERENCE = "See attached temporary lease Paragraph 11 continuation."


def terms(offer, kind):
    for key in (kind + "TemporaryLeaseSpecialProvisions", kind + "TempLeaseSpecialProvisions",
                "temporaryLeaseSpecialProvisions"):
        value = offer.get(key)
        if value is not None and value != "":
            return str(value)
    return ""


def inline_entries(text, kind):
    words = str(text or "").split()
    entries = []
    for x, y, width in BLANKS[kind]:
        line = []
        while words and stringWidth(" ".join(line + [words[0]]), "Helvetica", 8) <= width:
            line.append(words.pop(0))
        if line:
            entries.append((x, y, " ".join(line), 8))
        if not words:
            return entries
    return None


def text_entries(text, kind):
    entries = inline_entries(text, kind)
    x, y, _ = BLANKS[kind][0]
    return entries if entries is not None else [(x, y, REFERENCE, 8)]


def render_continuation(offer, kind):
    if not kind:
        return None
    text = terms(offer, kind)
    if inline_entries(text, kind) is not None:
        return None
    title = kind.capitalize() + "'s Temporary Residential Lease - Paragraph 11 Continuation"
    return render_text_continuation(offer, title, text)


def page_count(offer, kind):
    pdf = render_continuation(offer, kind)
    return len(PdfReader(BytesIO(pdf)).pages) if pdf else 0
