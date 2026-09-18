"""Preserve entered temporary-lease terms without truncating or summarizing."""
from io import BytesIO

from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from lib.repair_continuation import render_text_continuation


BLANKS = {
    "buyer": [(182, 263, 384)] + [(49, y, 518) for y in (252, 241, 230, 219, 208, 197, 186)],
    "seller": [(183, 305, 386)] + [(51, y, 518) for y in (294, 283, 272, 261, 250, 239, 228, 217, 206, 195, 184)],
}
OTHER_BLANKS = {
    "utilities": {"buyer": [(462, 435, 105), (49, 424, 384)], "seller": [(331, 466, 238)]},
    "pets": {"buyer": [(340, 380, 225)], "seller": [(342, 406, 227)]},
}
LABELS = {"utilities": "Paragraph 6 - Utilities", "pets": "Paragraph 8 - Pets",
          "special": "Paragraph 11 - Special Provisions"}
REFERENCE = "See attached temporary lease terms continuation."
SHORT_REFERENCE = "See continuation."


def terms(offer, kind, section="special"):
    if section == "utilities":
        payer = "Seller" if kind == "buyer" else "Buyer"
        keys = (kind + "TemporaryLeaseUtilitiesPaidBy" + payer, kind + "TempLeaseUtilities", "temporaryLeaseUtilities")
    elif section == "pets":
        keys = (kind + "TemporaryLeasePetsAllowed", kind + "TempLeasePets", "temporaryLeasePets")
    else:
        keys = (kind + "TemporaryLeaseSpecialProvisions", kind + "TempLeaseSpecialProvisions", "temporaryLeaseSpecialProvisions")
    for key in keys:
        value = offer.get(key)
        if value is not None and value != "":
            return str(value)
    return ""


def section_blanks(kind, section):
    return BLANKS[kind] if section == "special" else OTHER_BLANKS[section][kind]


def inline_entries(text, kind, section="special"):
    words = str(text or "").split()
    entries = []
    for x, y, width in section_blanks(kind, section):
        line = []
        while words and stringWidth(" ".join(line + [words[0]]), "Helvetica", 8) <= width:
            line.append(words.pop(0))
        if line:
            entries.append((x, y, " ".join(line), 8))
        if not words:
            return entries
    return None


def text_entries(text, kind, section="special"):
    entries = inline_entries(text, kind, section)
    x, y, _ = section_blanks(kind, section)[0]
    reference = REFERENCE if section == "special" else SHORT_REFERENCE
    return entries if entries is not None else [(x, y, reference, 8)]


def render_continuation(offer, kind):
    if not kind:
        return None
    sections = []
    for section, label in LABELS.items():
        text = terms(offer, kind, section)
        if inline_entries(text, kind, section) is None:
            sections.append(label + "\n" + text)
    if not sections:
        return None
    title = kind.capitalize() + "'s Temporary Residential Lease - Terms Continuation"
    return render_text_continuation(offer, title, "\n\n".join(sections))


def page_count(offer, kind):
    pdf = render_continuation(offer, kind)
    return len(PdfReader(BytesIO(pdf)).pages) if pdf else 0
