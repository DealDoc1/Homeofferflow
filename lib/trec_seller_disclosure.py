"""QA-only field map for supplied TREC-55-1 and TREC-61-0 PDFs.

The source PDFs are non-fillable. This module records source-specific points and
can render an unsigned local preview for visual QA. It deliberately has no
SignWell integration and refuses production activation until the map is marked
verified.
"""
from __future__ import annotations

from io import BytesIO
import hashlib
from typing import Any

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib.pdf_text import draw_text, text_width

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
TREC_55_1_PAGE_COUNT = 4
TREC_61_0_PAGE_COUNT = 2
TREC_55_1_SOURCE_SHA256 = "65a52e167c290814930624ba230e232c152573359f1388cdb5e1237a62e4239a"
TREC_61_0_SOURCE_SHA256 = "91056ab6520af8cbef319986e03490f1bf6947817c3d3f563348f80f957f871f"

# Coordinates are PDF points with origin at bottom-left. These are initial
# source-specific anchors from the supplied 05-04-2026 PDFs. They are not
# production-approved until the rendered preview is reviewed page by page.
TREC_55_1_MAP = {
    "property_address": {"page": 1, "x": 185, "y": 674, "width": 390},
    "seller_occupancy_yes": {"page": 1, "x": 78.13, "y": 609.17},
    "seller_occupancy_no": {"page": 1, "x": 102.30, "y": 609.17},
    "seller_occupancy_duration": {"page": 1, "x": 515, "y": 606, "width": 61},
    "item_responses_page_1": {"page": 1, "y_start": 570, "row_height": 18},
    "roof_type": {"page": 1, "x": 112, "y": 140, "width": 236},
    "roof_age": {"page": 1, "x": 375, "y": 140, "width": 117},
    "water_heater_gas": {"page": 1, "x": 182, "y": 184.5},
    "water_heater_electric": {"page": 1, "x": 301, "y": 184.5},
    "water_supply_city": {"page": 1, "x": 183, "y": 166},
    "water_supply_well": {"page": 1, "x": 301, "y": 166.8},
    "water_supply_mud": {"page": 1, "x": 415, "y": 165.6},
    "water_supply_coop": {"page": 1, "x": 522, "y": 165.9},
    "liquid_propane_lp_community": {"page": 1, "x": 189, "y": 257.5},
    "liquid_propane_on_property": {"page": 1, "x": 323, "y": 257.5},
    "fuel_gas_black_iron": {"page": 1, "x": 171, "y": 239},
    "fuel_gas_corrugated_stainless": {"page": 1, "x": 265, "y": 239},
    "fuel_gas_copper": {"page": 1, "x": 436, "y": 238.5},
    "garage_attached": {"page": 1, "x": 111, "y": 222},
    "garage_not_attached": {"page": 1, "x": 227, "y": 221},
    "garage_carport": {"page": 1, "x": 352, "y": 221},
    "garage_door_electronic": {"page": 1, "x": 182, "y": 203.2},
    "garage_door_controls": {"page": 1, "x": 301, "y": 203.2},
    # Canonical schema names retained alongside earlier QA aliases.
    "lp_community": {"page": 1, "x": 189, "y": 257.5},
    "lp_on_property": {"page": 1, "x": 323, "y": 257.5},
    "fuel_gas_corrugated_steel": {"page": 1, "x": 265, "y": 239},
    "carport": {"page": 1, "x": 352, "y": 221},
    "garage_opener_electronic": {"page": 1, "x": 182, "y": 203.2},
    "garage_opener_controls": {"page": 1, "x": 301, "y": 203.2},
    "hot_tub": {"page": 1, "x": 488, "y": 335},
    "repair_awareness_yes": {"page": 1, "x": 132.13, "y": 104.34},
    "repair_awareness_no": {"page": 1, "x": 168.13, "y": 104.34},
    "repair_awareness_unknown": {"page": 1, "x": 204.13, "y": 104.34},
    "smoke_detectors_yes": {"page": 2, "x": 195.13, "y": 725.66},
    "smoke_detectors_no": {"page": 2, "x": 231.13, "y": 725.66},
    "smoke_detectors_unknown": {"page": 2, "x": 267.13, "y": 725.66},
    "condition_responses_page_2": {"page": 2, "y_start": 500, "row_height": 27},
    "condition_responses_page_2b": {"page": 2, "y_start": 360, "row_height": 27},
    "repair_condition_yes": {"page": 3, "x": 484.93, "y": 736.46},
    "repair_condition_no": {"page": 3, "x": 60.13, "y": 725.66},
    "flood_responses": {"page": 3, "y_start": 650, "row_height": 27},
    "flood_claim_yes": {"page": 3, "x": 204.14, "y": 168.48},
    "flood_claim_no": {"page": 3, "x": 240.14, "y": 168.48},
    "fema_yes": {"page": 3, "x": 105.14, "y": 60.48},
    "fema_no": {"page": 3, "x": 141.14, "y": 60.48},
    "other_disclosures_page_4": {"page": 4, "y_start": 690, "row_height": 28},
    # Keep typed preview values clear of the printed "Signature" and "Date"
    # captions below each execution line.
    "seller_signature_1": {"page": 4, "x": 45, "y": 212, "width": 235},
    "seller_date_1": {"page": 4, "x": 255, "y": 212, "width": 70},
    "seller_signature_2": {"page": 4, "x": 345, "y": 212, "width": 235},
    "seller_date_2": {"page": 4, "x": 550, "y": 212, "width": 45},
    "purchaser_signature_1": {"page": 4, "x": 45, "y": 122, "width": 235},
    "purchaser_date_1": {"page": 4, "x": 255, "y": 122, "width": 70},
    "purchaser_signature_2": {"page": 4, "x": 345, "y": 122, "width": 235},
    "purchaser_date_2": {"page": 4, "x": 550, "y": 122, "width": 45},
}

TREC_61_0_MAP = {
    "property_address_page_1": {"page": 1, "x": 220, "y": 649, "width": 335},
    "groundwater_district_yes": {"page": 1, "x": 397.4, "y": 289.7},
    "groundwater_district_no": {"page": 1, "x": 442.5, "y": 289.7},
    "groundwater_district_unknown": {"page": 1, "x": 482.6, "y": 289.7},
    "water_well_yes": {"page": 1, "x": 380.8, "y": 253.8},
    "water_well_no": {"page": 1, "x": 422.0, "y": 253.8},
    "well_owned_seller": {"page": 1, "x": 51.0, "y": 143.0},
    "well_other_party": {"page": 1, "x": 51.0, "y": 117.9},
    "water_other_property_yes": {"page": 2, "x": 281.3, "y": 693.0},
    "water_other_property_no": {"page": 2, "x": 325.5, "y": 693.0},
    "outside_groundwater_rights_yes": {"page": 2, "x": 410.9, "y": 624.8},
    "outside_groundwater_rights_no": {"page": 2, "x": 452.9, "y": 624.8},
    "rights_severed_yes": {"page": 2, "x": 70.1, "y": 546.1},
    "rights_severed_no": {"page": 2, "x": 112.9, "y": 546.1},
    "surface_water_right_yes": {"page": 2, "x": 424.1, "y": 480.8},
    "surface_water_right_no": {"page": 2, "x": 468.5, "y": 480.8},
    "pond_lake_tank_yes": {"page": 2, "x": 70.7, "y": 391.6},
    "pond_lake_tank_no": {"page": 2, "x": 112.9, "y": 391.6},
    "seller_signature_1": {"page": 2, "x": 42, "y": 185, "width": 235},
    "seller_date_1": {"page": 2, "x": 255, "y": 185, "width": 70},
    "seller_signature_2": {"page": 2, "x": 345, "y": 185, "width": 235},
    "seller_date_2": {"page": 2, "x": 550, "y": 185, "width": 45},
    "buyer_signature_1": {"page": 2, "x": 42, "y": 129, "width": 235},
    "buyer_date_1": {"page": 2, "x": 255, "y": 129, "width": 70},
    "buyer_signature_2": {"page": 2, "x": 345, "y": 129, "width": 235},
    "buyer_date_2": {"page": 2, "x": 550, "y": 129, "width": 45},
}

TREC_55_1_CONDITION_ROWS = (
    ("defect_interior_walls", 65, 496.7), ("defect_ceilings", 245, 496.7), ("defect_floors", 416, 496.7),
    ("defect_exterior_walls", 65, 478.7), ("defect_doors", 245, 478.7), ("defect_windows", 416, 478.7),
    ("defect_roof", 65, 460.7), ("defect_foundation_slabs", 245, 460.7), ("defect_sidewalks", 416, 460.7),
    ("defect_walls_fences", 65, 442.7), ("defect_driveways", 245, 442.7), ("defect_intercom", 416, 442.7),
    ("defect_plumbing_sewers_septics", 65, 424.7), ("defect_electrical_systems", 245, 424.7),
    ("defect_lighting_fixtures", 416, 424.7), ("defect_other_structural_components", 65, 406.7),
)

TREC_55_1_ADDITIONAL_ROWS = (
    ("unpermitted_modifications", 65, 707.7), ("hoa_assessments", 65, 690.5),
    ("common_area", 65, 667.5), ("deed_or_ordinance_violations", 65, 644.7),
    ("property_lawsuits", 65, 626.3), ("health_or_safety_condition", 65, 608.3),
    ("large_rainwater_system", 65, 585.3), ("groundwater_or_subsidence_district", 65, 567.5),
    ("conservation_easements", 65, 549.5), ("covered_by_insurance", 65, 517.1),
    ("covered_by_windstorm_insurance", 65, 499.1), ("unable_to_insure", 65, 480.5),
    ("private_road_maintenance", 65, 462.4), ("storage_tanks", 65, 439.4),
    ("large_aboveground_storage_tanks", 65, 416.3),
)

TREC_55_1_FLOOD_ROWS = (
    ("present_flood_insurance", 65, 649.7), ("previous_reservoir_release_flooding", 65, 631.7),
    ("previous_natural_flood_water_penetration", 65, 613.7),
    ("in_100_year_floodplain", 65, 577.7), ("in_500_year_floodplain", 65, 559.7),
    ("in_floodway", 65, 541.7), ("in_flood_pool", 65, 523.7), ("in_reservoir", 65, 505.7),
)

TREC_55_1_CONDITION4_ROWS = (
    ("active_termites", 58, 281),
    ("previous_structural_or_roof_repair", 318, 281),
    ("termite_or_wood_rot_needing_repair", 58, 263),
    ("hazardous_toxic_waste", 318, 263),
    ("previous_termite_damage", 58, 245),
    ("asbestos_components", 318, 245),
    ("previous_termite_treatment", 58, 227),
    ("urea_formaldehyde_insulation", 318, 227),
    ("improper_drainage", 58, 209),
    ("radon_gas", 318, 209),
    ("water_damage_not_flood", 58, 191),
    ("lead_based_paint", 318, 191),
    ("landfill_settling_soil_movement_fault_lines", 58, 173),
    ("aluminum_wiring", 318, 173),
    ("single_blockable_main_drain", 58, 155),
    ("previous_fires", 318, 155),
    ("unplatted_easements", 318, 137),
    ("subsurface_structure_or_pits", 318, 119),
    ("previous_methamphetamine_use", 318, 95.7),
)

TREC_55_1_ITEM_ROWS = (
    ("range", 74, 569.2), ("oven", 227, 569.2), ("microwave", 407, 569.2),
    ("dishwasher", 74, 551.2), ("trash_compactor", 227, 551.2), ("disposal", 407, 551.2),
    ("washer_dryer_hookups", 74, 533.2), ("window_screens", 227, 533.2), ("rain_gutters", 407, 533.2),
    ("security_system", 74, 515.2), ("fire_detection_equipment", 227, 515.2), ("intercom_system", 407, 515.2),
    ("smoke_detector", 227, 497.2), ("smoke_detector_hearing_impaired", 227, 479.2),
    ("carbon_monoxide_alarm", 227, 461.2), ("emergency_escape_ladders", 227, 443.2),
    ("tv_antenna", 74, 425.2), ("cable_tv_wiring", 227, 425.2), ("satellite_dish", 407, 425.2),
    ("ceiling_fans", 74, 407.2), ("attic_fans", 227, 407.2), ("exhaust_fans", 407, 407.2),
    ("central_ac", 74, 389.2), ("central_heating", 227, 389.2), ("wall_window_ac", 407, 389.2),
    ("plumbing_system", 74, 371.2), ("septic_system", 227, 371.2), ("public_sewer_system", 407, 371.2),
    ("patio_decking", 74, 353.2), ("outdoor_grill", 227, 353.2), ("fences", 407, 353.2),
    ("pool", 74, 335.2), ("sauna", 227, 335.2), ("spa", 407, 335.2),
    ("pool_equipment", 74, 317.2), ("pool_heater", 227, 317.2), ("automatic_lawn_sprinkler_system", 407, 317.2),
    ("fireplace_wood_burning", 74, 294.2), ("fireplace_mock", 407, 294.2),
    ("natural_gas_lines", 74, 276.2), ("gas_fixtures", 407, 276.2),
    ("liquid_propane_gas", 74, 258.2), ("fuel_gas_piping", 74, 239.2),
)

# These are response lines under the same "Write Yes (Y), No (N), or
# Unknown (U)" instruction as the item rows, not affirmative-only checkboxes.
TREC_55_1_FEATURE_RESPONSES = (
    "water_heater_gas", "water_heater_electric",
    "water_supply_city", "water_supply_well", "water_supply_mud", "water_supply_coop",
    "lp_community", "lp_on_property", "fuel_gas_black_iron",
    "fuel_gas_corrugated_steel", "fuel_gas_copper", "garage_attached",
    "garage_not_attached", "carport", "garage_opener_electronic",
    "garage_opener_controls", "hot_tub",
)
TREC_55_1_FEATURE_ALIASES = {
    "lp_community": "liquid_propane_lp_community",
    "lp_on_property": "liquid_propane_on_property",
    "fuel_gas_corrugated_steel": "fuel_gas_corrugated_stainless",
    "carport": "garage_carport",
    "garage_opener_electronic": "garage_door_electronic",
    "garage_opener_controls": "garage_door_controls",
}

def source_contract(form_code: str) -> dict[str, Any]:
    if form_code == "TREC-55-1":
        return {"form_code": form_code, "page_count": TREC_55_1_PAGE_COUNT, "field_map": TREC_55_1_MAP, "source_sha256": TREC_55_1_SOURCE_SHA256, "activation_status": "pending_visual_qa"}
    if form_code == "TREC-61-0":
        return {"form_code": form_code, "page_count": TREC_61_0_PAGE_COUNT, "field_map": TREC_61_0_MAP, "source_sha256": TREC_61_0_SOURCE_SHA256, "activation_status": "pending_visual_qa"}
    raise ValueError("Unsupported seller disclosure form.")


def build_signwell_fields(
    form_code: str, data: dict[str, Any], *, page_offset: int = 0
) -> list[list[dict[str, Any]]]:
    """Return execution widgets calibrated to the supplied disclosure PDFs.

    The seller disclosure is sometimes prepared before a purchaser is known,
    so one or two Sellers are required while Buyer acknowledgements are added
    only for the zero-to-two Buyers named in the saved disclosure.  SignWell
    uses a 96-DPI, top-origin US Letter page; these rectangles were measured
    against the supplied source rules and stop above the printed captions.
    """
    if form_code not in {"TREC-55-1", "TREC-61-0"}:
        raise ValueError("Unsupported seller disclosure form.")
    if not isinstance(page_offset, int) or page_offset < 0:
        raise ValueError("Seller disclosure signing page offset must be a non-negative integer.")
    sellers = data.get("seller_names") or []
    buyers = data.get("buyer_names") or []
    if not (1 <= len(sellers) <= 2 and 0 <= len(buyers) <= 2):
        raise ValueError("Seller disclosure signing requires one or two Sellers and up to two Buyers.")

    if form_code == "TREC-55-1":
        page = 4 + page_offset
        seller_y, buyer_y = 749, 877
        left_x, right_x, signature_width = 80, 432, 250
        left_date_x, right_date_x, date_width = 350, 720, 60
        prefix = "trec551"
    else:
        page = 2 + page_offset
        # The water-rights source places its execution rules lower than the
        # older draft map. Keep the widgets immediately above those rules,
        # clear of the notice text above and the Seller/Buyer captions below.
        seller_y, buyer_y = 799, 862
        left_x, right_x, signature_width = 80, 432, 253
        left_date_x, right_date_x, date_width = 360, 720, 36
        prefix = "trec610"

    fields: list[dict[str, Any]] = []
    party_rows = (
        ("seller", sellers, seller_y, 0),
        ("buyer", buyers, buyer_y, len(sellers)),
    )
    for party, names, row_y, recipient_offset in party_rows:
        for index, _name in enumerate(names, start=1):
            is_second = index == 2
            signature_x = right_x if is_second else left_x
            date_x = right_date_x if is_second else left_date_x
            recipient_id = str(recipient_offset + index)
            fields.extend((
                {
                    "api_id": f"{prefix}_{party}{index}_signature_p{page}",
                    "type": "signature",
                    "page": page,
                    "x": signature_x,
                    "y": row_y,
                    "recipient_id": recipient_id,
                    "required": True,
                    "width": signature_width,
                    "height": 26,
                },
                {
                    "api_id": f"{prefix}_{party}{index}_date_p{page}",
                    "type": "date",
                    "page": page,
                    "x": date_x,
                    "y": row_y,
                    "recipient_id": recipient_id,
                    "required": True,
                    "width": date_width,
                    "height": 26,
                },
            ))
    if form_code == "TREC-61-0":
        # The printed Buyer/Seller identification blanks sit below the page-one
        # border. These compact boxes stay entirely between that border and rule.
        for role, names, offset, slots in (
            ("seller", sellers, 0, ((314, 27), (352, 25))),
            ("buyer", buyers, len(sellers), ((194, 21), (226, 25))),
        ):
            for i, _ in enumerate(names):
                x, width = slots[i]
                fields.append({"api_id": f"trec610_{role}{i + 1}_initials_p{1 + page_offset}",
                               "type": "initials", "page": 1 + page_offset, "recipient_id": str(offset + i + 1),
                               "required": True, "x": x * 4 / 3, "y": 760 * 4 / 3,
                               "width": width * 4 / 3, "height": 12})
    return [fields]

def validate_source_bytes(form_code: str, source_pdf_bytes: bytes) -> None:
    """Reject a private source unless its fingerprint matches the approved PDF."""
    expected = source_contract(form_code)["source_sha256"]
    actual = hashlib.sha256(source_pdf_bytes).hexdigest()
    if actual != expected:
        raise ValueError(f"{form_code} source fingerprint does not match the approved revision.")


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())

def _draw(c: Canvas, value: Any, x: float, y: float, *, size: float = 8) -> None:
    value = _clean(value)
    if value:
        draw_text(c, value, x, y, size)

def _answer(value):
    return "Y" if value is True else "N" if value is False else _clean(value).upper()

def _response(c: Canvas, value: Any, x: float, y: float) -> None:
    # Earlier drafts may carry real booleans. Do not mistake False for blank
    # or a nonempty "N"/"U" response for an affirmative selection.
    value = _answer(value)
    if value in {"Y", "N", "U"}:
        _draw(c, value, x, y, size=8)

def _check(c: Canvas, x: float, y: float) -> None:
    """A six-point X wholly inside its source square/circle."""
    c.setLineWidth(.8)
    c.line(x, y, x + 6, y + 6)
    c.line(x, y + 6, x + 6, y)

def _choice(c, values, canonical, options, field_map):
    if canonical in values:
        response = _answer(values[canonical])
        keys = [options[response]] if response in options else []
    else:
        keys = [key for key in options.values() if _answer(values.get(key)) in {"Y", "YES", "TRUE", "1"}]
        if len(keys) > 1:
            raise ValueError("Choose one answer for each disclosure question.")
    for key in keys:
        anchor = field_map[key]; _check(c, anchor["x"], anchor["y"])

def _address(c, value, x, y, width, form_code, overflow):
    value = _clean(value)
    if not value:
        return
    if text_width(value, "Helvetica", 8) <= width:
        draw_text(c, value, x, y, 8)
    else:
        draw_text(c, "See attached property address.", x, y, 8)
        record = {"form": form_code, "label": "Property address", "text": value}
        if record not in overflow:
            overflow.append(record)

def render_unsigned_preview(source_pdf_bytes: bytes, form_code: str, values: dict[str, Any], *, qa_mode: bool = False,
                            continuation_sink=None, parties=None) -> bytes:
    """Render a local unsigned preview only; never creates a sendable packet."""
    if not qa_mode:
        raise ValueError("Unsigned seller-disclosure preview requires explicit qa_mode=True.")
    contract = source_contract(form_code)
    validate_source_bytes(form_code, source_pdf_bytes)
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != contract["page_count"]:
        raise ValueError(f"{form_code} source must contain exactly {contract['page_count']} pages.")
    field_map = contract["field_map"]
    from lib.seller_disclosure_explanations import draw_explanations, append_explanations
    overflow = []
    overlays = []
    for page_number in range(1, contract["page_count"] + 1):
        overlay_stream = BytesIO()
        canvas = Canvas(overlay_stream, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
        draw_explanations(canvas, form_code, values, page_number, overflow)
        if form_code == "TREC-55-1":
            _address(canvas, values.get("propertyAddress"), 185 if page_number == 1 else 273,
                     675 if page_number == 1 else 758, 391 if page_number == 1 else 240, form_code, overflow)
        if form_code == "TREC-55-1" and page_number == 1:
            _choice(canvas, values, "seller_occupancy", {"Y": "seller_occupancy_yes", "N": "seller_occupancy_no"}, field_map)
            _choice(canvas, values, "property_items_condition_issue", {"Y": "repair_awareness_yes", "N": "repair_awareness_no", "U": "repair_awareness_unknown"}, field_map)
            for key in TREC_55_1_FEATURE_RESPONSES:
                value = values.get(key) if key in values else values.get(TREC_55_1_FEATURE_ALIASES.get(key))
                _response(canvas, value, field_map[key]["x"], field_map[key]["y"])
            for key, x, y in TREC_55_1_ITEM_ROWS:
                _response(canvas, values.get(key), x, y)
        if form_code == "TREC-55-1" and page_number == 3:
            _choice(canvas, values, "property_needs_repair", {"Y": "repair_condition_yes", "N": "repair_condition_no"}, field_map)
            # Older local QA used this alias; never overprint a new answer.
            if values.get("repairDescription") and not values.get("repair_explanation"):
                draw_explanations(canvas, form_code,
                                  {"repair_explanation": values["repairDescription"]}, page_number, overflow)
            for key, x, y in TREC_55_1_FLOOD_ROWS:
                _response(canvas, values.get(key), x, y)
            for i, key in enumerate(("in_100_year_floodplain", "in_500_year_floodplain", "in_floodway", "in_flood_pool", "in_reservoir")):
                extent = values.get(key + "_extent")
                if _answer(values.get(key)) == "Y" and extent in {"wholly", "partly"}:
                    _check(canvas, 123.13 if extent == "wholly" else 168.13, 581.16 - 18 * i)
        if form_code == "TREC-55-1" and page_number == 2:
            _choice(canvas, values, "working_smoke_detectors", {"Y": "smoke_detectors_yes", "N": "smoke_detectors_no", "U": "smoke_detectors_unknown"}, field_map)
            for key, x, y in TREC_55_1_CONDITION_ROWS:
                _response(canvas, values.get(key), x, y)
            for key, x, y in TREC_55_1_CONDITION4_ROWS:
                _response(canvas, values.get(key), x, y)
        if form_code == "TREC-55-1" and page_number == 3:
            _choice(canvas, values, "filed_flood_claim", {"Y": "flood_claim_yes", "N": "flood_claim_no"}, field_map)
            _choice(canvas, values, "received_fema_or_sba_assistance", {"Y": "fema_yes", "N": "fema_no"}, field_map)
        if form_code == "TREC-55-1" and page_number == 4:
            for key, x, y in TREC_55_1_ADDITIONAL_ROWS:
                _response(canvas, values.get(key), x, y)
            for value_key, map_key in (
                ("sellerSignature1", "seller_signature_1"),
                ("sellerDate1", "seller_date_1"),
                ("sellerSignature2", "seller_signature_2"),
                ("sellerDate2", "seller_date_2"),
                ("purchaserSignature1", "purchaser_signature_1"),
                ("purchaserDate1", "purchaser_date_1"),
                ("purchaserSignature2", "purchaser_signature_2"),
                ("purchaserDate2", "purchaser_date_2"),
            ):
                if values.get(value_key):
                    anchor = field_map[map_key]
                    _draw(canvas, values[value_key], anchor["x"], anchor["y"], size=8)
        if form_code == "TREC-61-0" and page_number == 1:
            _address(canvas, values.get("propertyAddress"), 220, 649, 335, form_code, overflow)
            _choice(canvas, values, "in_groundwater_district", {"Y": "groundwater_district_yes", "N": "groundwater_district_no", "U": "groundwater_district_unknown"}, field_map)
            _choice(canvas, values, "water_wells_known", {"Y": "water_well_yes", "N": "water_well_no"}, field_map)
            ownership = {"seller_only": "well_owned_seller", "other": "well_other_party"}
            if "well_ownership" in values:
                key = ownership.get(values["well_ownership"])
                if key:
                    _check(canvas, field_map[key]["x"], field_map[key]["y"])
            else:
                for key, canonical in (("well_owned_seller", "wells_seller_only"), ("well_other_party", "wells_other_ownership")):
                    if _answer(values.get(canonical, values.get(key))) == "Y":
                        _check(canvas, field_map[key]["x"], field_map[key]["y"])
        if form_code == "TREC-61-0" and page_number == 2:
            _address(canvas, values.get("propertyAddress"), 32, 748, 545, form_code, overflow)
            semantic_water = (
                ("water_well_on_another_property", "water_other_property_yes", "water_other_property_no"),
                ("water_well_relies_on_outside_rights", "outside_groundwater_rights_yes", "outside_groundwater_rights_no"),
                ("groundwater_rights_severed_sold_leased", "rights_severed_yes", "rights_severed_no"),
                ("surface_water_right", "surface_water_right_yes", "surface_water_right_no"),
                ("pond_lake_or_water_tank", "pond_lake_tank_yes", "pond_lake_tank_no"),
            )
            for response_key, yes_key, no_key in semantic_water:
                _choice(canvas, values, response_key, {"Y": yes_key, "N": no_key}, field_map)
            for value_key, map_key in (
                ("sellerSignature1", "seller_signature_1"),
                ("sellerDate1", "seller_date_1"),
                ("sellerSignature2", "seller_signature_2"),
                ("sellerDate2", "seller_date_2"),
                ("buyerSignature1", "buyer_signature_1"),
                ("buyerDate1", "buyer_date_1"),
                ("buyerSignature2", "buyer_signature_2"),
                ("buyerDate2", "buyer_date_2"),
            ):
                if values.get(value_key):
                    anchor = field_map[map_key]
                    _draw(canvas, values[value_key], anchor["x"], anchor["y"], size=8)
        canvas.showPage()
        canvas.save()
        overlay_stream.seek(0)
        overlays.append(PdfReader(overlay_stream).pages[0])
    writer = PdfWriter()
    for index, page in enumerate(source.pages):
        writer.add_page(page)
        writer.pages[index].merge_page(overlays[index])
    output = BytesIO()
    writer.write(output)
    if continuation_sink is not None:
        continuation_sink.extend(overflow)
        return output.getvalue()
    return append_explanations(output.getvalue(), overflow,
                               property_address=str(values.get("propertyAddress") or ""),
                               parties=parties)[0]
