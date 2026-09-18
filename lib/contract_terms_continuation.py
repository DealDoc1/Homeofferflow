"""Lossless placement of entered TREC 20-19 disclosure and informational text."""
from io import BytesIO

from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from lib.repair_continuation import render_text_continuation


TITLE = "Purchase Contract - Terms Continuation"
REFERENCE = "See continuation."
LABELS = {
    "broker": "Paragraph 8 - Broker or Sales Agent Disclosure",
    "special": "Paragraph 11 - Special Provisions",
}
# Measured on page 6 of the 05-04-2026 source. The first blank in each
# section begins after printed text; later blanks span the full paragraph.
BLANKS = {
    "broker": [(484, 719, 72), (63, 706.5, 492), (63, 694, 492)],
    "special": [(352, 240, 200), (62, 229, 490), (62, 218, 490)],
}


def terms(offer, section):
    keys = ("brokerDisclosure",) if section == "broker" else ("specialProvisions", "specialProvisionsText")
    for key in keys:
        value = offer.get(key)
        if value is not None and value != "":
            return str(value)
    return ""


def inline_entries(text, section):
    words = str(text or "").split()
    entries = []
    for x, y, width in BLANKS[section]:
        line = []
        while words and stringWidth(" ".join(line + [words[0]]), "Helvetica", 8) <= width:
            line.append(words.pop(0))
        if line:
            entries.append((x, y, " ".join(line), 8))
        if not words:
            return entries
    return None


def text_entries(text, section):
    entries = inline_entries(text, section)
    x, y, _ = BLANKS[section][0]
    return entries if entries is not None else [(x, y, REFERENCE, 8)]


def render_continuation(offer):
    sections = [label + "\n" + terms(offer, section)
                for section, label in LABELS.items()
                if inline_entries(terms(offer, section), section) is None]
    return render_text_continuation(offer, TITLE, "\n\n".join(sections)) if sections else None


def page_count(offer):
    pdf = render_continuation(offer)
    return len(PdfReader(BytesIO(pdf)).pages) if pdf else 0
