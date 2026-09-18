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
    # Notice-address rules measured on page two of the current 16-7/15-7
    # sources. Later lines use their full width, not the first-line indent.
    "landlord_mail": {
        "buyer": [(137, 329, 161), (54, 309.5, 244), (54, 290, 244)],
        "seller": [(130, 329, 174), (55, 310, 249), (55, 291, 249)],
    },
    "tenant_mail": {
        "buyer": [(385, 329, 188), (310, 309.5, 263), (310, 290, 263)],
        "seller": [(394, 329, 179), (327, 310, 246), (327, 291, 246)],
    },
}
LABELS = {"utilities": "Paragraph 6 - Utilities", "pets": "Paragraph 8 - Pets",
          "special": "Paragraph 11 - Special Provisions",
          "landlord_mail": "Paragraph 24 - Notices to Landlord: Mailing Address",
          "tenant_mail": "Paragraph 24 - Notices to Tenant: Mailing Address"}
REFERENCE = "See attached temporary lease terms continuation."
SHORT_REFERENCE = "See continuation."


def terms(offer, kind, section="special"):
    if section in {"landlord_mail", "tenant_mail"}:
        landlord = section == "landlord_mail"
        party = "seller" if (kind == "buyer") == landlord else "buyer"
        keys = (party + "MailAddr", ("landlord" if landlord else "tenant") + "MailAddr")
    elif section == "utilities":
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
    size = 7.5 if section.endswith("_mail") else 8
    for x, y, width in section_blanks(kind, section):
        line = []
        while words and stringWidth(" ".join(line + [words[0]]), "Helvetica", size) <= width:
            line.append(words.pop(0))
        if line:
            entries.append((x, y, " ".join(line), size))
        if not words:
            return entries
    return None


def text_entries(text, kind, section="special"):
    entries = inline_entries(text, kind, section)
    x, y, _ = section_blanks(kind, section)[0]
    reference = REFERENCE if section == "special" else SHORT_REFERENCE
    size = 7.5 if section.endswith("_mail") else 8
    return entries if entries is not None else [(x, y, reference, size)]


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
