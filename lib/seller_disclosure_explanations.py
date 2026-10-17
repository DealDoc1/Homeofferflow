"""Literal seller explanations, bounded source blanks and overflow pages.

This copies entered facts; it never chooses an answer or drafts legal terms.
"""
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from lib.pdf_text import display_text, draw_text, paragraph_markup, text_width

MAX_EXPLANATION = 3000
RENDER_REVISION = "seller-disclosure-date-fit-2026-10-16-v4"
REFERENCE = "See attached explanation."
COUNT_KEYS = {"water_well_count_total", "water_well_count_in_use", "water_well_count_capped"}
# Form, saved key, human label, source page, measured source blank rows.
# A row is (left, baseline, width); baselines are above the printed rules.
DETAILS = {
    "TREC-55-1": (
        ("seller_occupancy_duration", "Occupancy - Time since the Seller occupied the property", 1, ((515, 606, 61),)),
        ("roof_type", "Section 1 - Roof type", 1, ((112, 140, 236),)),
        ("roof_age", "Section 1 - Approximate roof age", 1, ((375, 140, 117),)),
        ("property_item_condition_description", "Section 1 - Property items", 1,
         ((67, 85, 507), (67, 67, 507), (67, 49, 507))),
        ("smoke_detector_explanation", "Section 2 - Smoke detectors", 2,
         ((220, 715, 354), (58, 697, 516), (58, 679, 516), (58, 661, 516))),
        ("known_defects_explanation", "Section 3 - Known defects", 2,
         ((58, 337, 516), (58, 319, 516))),
        ("other_structural_description", "Section 3 - Other structural components", 2,
         ((257, 409, 317), (86, 391, 488), (86, 373, 488))),
        ("conditions_explanation", "Section 4 - Known conditions", 2,
         ((58, 58, 516), (58, 40, 516))),
        ("repair_explanation", "Section 5 - Repairs", 3,
         ((58, 706, 516), (58, 688, 516))),
        ("flood_history_explanation", "Section 6 - Flood history", 3,
         ((58, 472, 516),)),
        ("flood_claim_explanation", "Section 7 - Flood insurance claims", 3,
         ((58, 149.5, 516),)),
        ("fema_assistance_explanation", "Section 8 - FEMA or SBA assistance", 3,
         ((58, 41.5, 516),)),
        ("additional_disclosures_explanation", "Section 9 - Additional disclosures", 4,
         ((59, 388.5, 516), (59, 370.5, 516))),
        # Earlier drafts used one combined answer. Keep its full context;
        # never pretend we know which of the four questions it answers.
        ("repairs_flood_explanation", "Sections 5-8 - Additional repairs and flood information", 3, ()),
    ),
    "TREC-61-0": (
        ("water_well_count_total", "Section 2B(1) - Total known wells", 1, ((346, 232, 42),)),
        ("water_well_count_in_use", "Section 2B(2) - Wells in use", 1, ((446, 221.5, 50),)),
        ("water_well_count_capped", "Section 2B(3) - Capped, covered, plugged or abandoned wells", 1, ((264, 201, 35),)),
        ("groundwater_district_name", "Section 2A - Groundwater district", 1,
         ((284, 278.5, 286),)),
        ("groundwater_district_website", "Section 2A - District website", 1,
         ((67, 268, 503),)),
        ("water_well_permits", "Section 2B - Well registrations and permits", 1,
         ((168, 178.5, 402), (85, 168, 485))),
        ("well_description", "Section 2C - Water well", 1, ((151, 85.5, 419),)),
        ("well_owners_operators", "Section 2C - Well owners or operators", 1, ((181, 75, 389),)),
        ("well_beneficiary", "Section 2C - Well beneficiary", 1, ((148, 64, 422),)),
        ("well_agreement", "Section 2C - Well agreement or understanding", 1,
         ((235, 53.5, 335), (85, 42.5, 485))),
        ("other_property_well_explanation", "Section 2D - Well on another property", 2,
         ((403, 682, 169), (68, 671, 504), (68, 660, 504))),
        ("outside_groundwater_explanation", "Section 2E - Groundwater rights outside the property", 2,
         ((256, 614, 316), (68, 603, 504), (68, 592, 504))),
        ("severed_groundwater_explanation", "Section 2F - Rights severed, sold or leased", 2,
         ((68, 535, 504), (68, 524, 504))),
        ("surface_water_right_number", "Section 3A - Surface-water right number", 2,
         ((132, 449, 368),)),
        ("surface_water_ownership", "Section 3A - Surface-water ownership interests", 2,
         ((356, 427.5, 216), (86, 417, 414))),
        ("other_water_well_rights_explanation", "Additional water-well rights information", 2, ()),
    ),
}


def validate_explanations(form_code, values):
    keys = {entry[0] for entry in DETAILS[form_code]}
    keys.update(key for key in values if key == "notes" or key.startswith("notes_"))
    for key in keys & values.keys():
        value = values[key]
        if key in COUNT_KEYS:
            if (isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9999):
                continue
            if not isinstance(value, str) or (value and (not value.isascii() or not value.isdigit() or len(value) > 4)):
                raise ValueError("Enter a whole number from 0 to 9,999 for each well count, or leave it blank.")
        if not isinstance(value, str) or len(value) > MAX_EXPLANATION:
            raise ValueError(f"Each disclosure explanation must be text of at most {MAX_EXPLANATION:,} characters.")
        if any(ord(char) < 32 and char not in "\t\r\n" for char in value):
            raise ValueError("Disclosure explanations contain an unsupported control character.")
    for key in ("in_100_year_floodplain", "in_500_year_floodplain", "in_floodway", "in_flood_pool", "in_reservoir"):
        if key + "_extent" in values and (not isinstance(values[key + "_extent"], str) or values[key + "_extent"] not in {"", "wholly", "partly"}):
            raise ValueError("Choose Wholly or Partly for the flood-area extent.")
    if "well_ownership" in values and (not isinstance(values["well_ownership"], str) or values["well_ownership"] not in {"", "seller_only", "other"}):
        raise ValueError("Choose the water-well ownership arrangement.")


def inline_lines(text, blanks):
    """Fit all words and paragraph breaks, or return None; never truncate."""
    paragraphs = display_text(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output = []
    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            if len(output) >= len(blanks):
                return None
            output.append("")
        while words:
            if len(output) >= len(blanks):
                return None
            width = blanks[len(output)][2]
            line = []
            while words and text_width(" ".join(line + [words[0]]), "Helvetica", 8) <= width:
                line.append(words.pop(0))
            if not line:
                return None
            output.append(" ".join(line))
    return output


def draw_explanations(canvas, form_code, values, page, overflow):
    validate_explanations(form_code, values)
    definitions = list(DETAILS[form_code])
    definitions += [(key, "Additional seller information", 1, ()) for key in sorted(values)
                    if key == "notes" or key.startswith("notes_")]
    for key, label, source_page, blanks in definitions:
        if source_page != page or key not in values or not str(values[key]).strip():
            continue
        text = str(values[key])
        lines = inline_lines(text, blanks) if blanks else None
        if lines is None:
            overflow.append({"form": form_code, "label": label, "text": text})
            if blanks:
                x, y, width = blanks[0]
                reference = REFERENCE if text_width(REFERENCE, "Helvetica", 8) <= width else "See attached."
                if text_width(reference, "Helvetica", 8) > width:
                    raise ValueError("The disclosure continuation reference does not fit.")
                draw_text(canvas, reference, x, y, 8)
        else:
            for line, (x, y, _) in zip(lines, blanks):
                draw_text(canvas, line, x, y, 8)


def _parties(data):
    sellers, buyers = data.get("seller_names") or [], data.get("buyer_names") or []
    if len(sellers) > 2 or len(buyers) > 2:
        raise ValueError("Disclosure continuations support up to two Sellers and two Buyers.")
    return [(str(i + 1), f"Seller {i + 1}") for i in range(len(sellers))] + [
        (str(len(sellers) + i + 1), f"Purchaser {i + 1}") for i in range(len(buyers))]


def append_explanations(packet, records, *, property_address="", parties=None):
    """Append after all official pages, keeping the water form at pages 5-6."""
    if not records:
        return packet, []
    output = BytesIO()
    style = ParagraphStyle("disclosure_note", fontName="Helvetica", fontSize=9, leading=12,
                           splitLongWords=True, allowWidows=0, allowOrphans=0)
    heading = ParagraphStyle("disclosure_label", parent=style, fontName="Helvetica-Bold", spaceAfter=7, keepWithNext=True)
    story = []
    for record in records:
        story.extend((Paragraph(paragraph_markup(record["form"] + " - " + record["label"], "Helvetica-Bold"), heading),
                      Paragraph(paragraph_markup(record["text"]), style), Spacer(1, 15)))
    party_rows = _parties(parties or {})
    def page_frame(canvas, document):
        canvas.saveState()
        draw_text(canvas, "Seller Disclosure - Additional Information", 48, 750, 12, "Helvetica-Bold")
        # Long addresses are wrapped, not cropped into the note area.
        address_style = ParagraphStyle("disclosure_address", parent=style, fontSize=8, leading=10)
        address = Paragraph(paragraph_markup("Property: " + property_address), address_style)
        _, height = address.wrap(516, 60)
        if height > 50:
            raise ValueError("The property address is too long for the disclosure continuation header.")
        address.drawOn(canvas, 48, 730 - height)
        for i, (_, label) in enumerate(party_rows):
            x = 65 + i * 130
            draw_text(canvas, label + " initials", x, 85, 8)
            canvas.line(x, 63, x + 60, 63)
        draw_text(canvas, "Additional seller information", 48, 35, 8)
        canvas.drawRightString(564, 35, "Page " + str(document.page))
        canvas.restoreState()
    SimpleDocTemplate(output, pagesize=(612, 792), leftMargin=48, rightMargin=48,
                      topMargin=120, bottomMargin=115).build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    writer = PdfWriter()
    base = PdfReader(BytesIO(packet))
    notes = PdfReader(BytesIO(output.getvalue()))
    for page in [*base.pages, *notes.pages]:
        writer.add_page(page)
    result = BytesIO(); writer.write(result)
    return result.getvalue(), list(range(len(base.pages) + 1, len(base.pages) + len(notes.pages) + 1))


def continuation_fields(data, pages):
    fields = []
    for page in pages:
        if not isinstance(page, int) or page < 1:
            raise ValueError("Invalid disclosure continuation page.")
        for i, (recipient, _) in enumerate(_parties(data)):
            fields.append({"api_id": f"disclosure_continuation_p{page}_recipient{recipient}_initials",
                           "type": "initials", "page": page, "recipient_id": recipient,
                           "required": True, "x": (65 + i * 130) * 4 / 3,
                           "y": 708 * 4 / 3, "width": 60 * 4 / 3, "height": 20 * 4 / 3})
    return fields
