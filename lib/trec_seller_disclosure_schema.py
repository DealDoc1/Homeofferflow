"""Declarative seller/purchaser schema for supplied TREC disclosure sources.

This is intake metadata only. It does not decide a response, sign for a seller,
or enable packet generation. The signer roles are explicit because seller
disclosures and purchaser acknowledgments are different legal acts.
"""
from __future__ import annotations

TREC_55_1_SCHEMA = {
    "form_code": "TREC-55-1",
    "source_revision": "05-04-2026",
    "pages": 4,
    "sections": [
        {"id": "property_and_occupancy", "page": 1, "respondent": "seller", "fields": [
            "property_address", "seller_occupancy", "seller_occupancy_duration",
        ]},
        {"id": "property_items", "page": 1, "respondent": "seller", "response_type": "yes_no_unknown", "fields": [
            "range", "oven", "microwave", "dishwasher", "trash_compactor", "disposal",
            "washer_dryer_hookups", "window_screens", "rain_gutters", "security_system",
            "fire_detection_equipment", "intercom_system", "smoke_detector",
            "smoke_detector_hearing_impaired", "carbon_monoxide_alarm",
            "emergency_escape_ladders", "tv_antenna", "cable_tv_wiring", "satellite_dish",
            "ceiling_fans", "attic_fans", "exhaust_fans", "central_ac", "central_heating",
            "wall_window_ac", "plumbing_system", "septic_system", "public_sewer_system",
            "patio_decking", "outdoor_grill", "fences", "pool", "sauna", "spa", "hot_tub",
            "pool_equipment", "pool_heater", "automatic_lawn_sprinkler_system",
            "fireplace_wood_burning", "fireplace_mock", "natural_gas_lines", "gas_fixtures",
            "liquid_propane_gas", "lp_community", "lp_on_property", "fuel_gas_black_iron",
            "fuel_gas_corrugated_steel", "fuel_gas_copper", "garage_attached",
            "garage_not_attached", "carport", "garage_opener_electronic",
            "garage_opener_controls", "water_heater_gas", "water_heater_electric",
            "water_supply_city", "water_supply_well", "water_supply_mud", "water_supply_coop",
            "roof_type", "roof_age",
        ], "notes_field": "property_item_condition_description"},
        {"id": "smoke_detectors", "page": 2, "respondent": "seller", "response_type": "yes_no_unknown", "fields": ["working_smoke_detectors"], "notes_field": "smoke_detector_explanation"},
        {"id": "known_defects", "page": 2, "respondent": "seller", "response_type": "yes_no_unknown", "fields": [
            "defect_interior_walls", "defect_ceilings", "defect_floors", "defect_exterior_walls",
            "defect_doors", "defect_windows", "defect_roof", "defect_foundation_slabs",
            "defect_sidewalks", "defect_walls_fences", "defect_driveways", "defect_intercom",
            "defect_plumbing_sewers_septics", "defect_electrical_systems", "defect_lighting_fixtures",
            "defect_other_structural_components",
        ], "notes_field": "known_defects_explanation"},
        {"id": "conditions", "page": 2, "respondent": "seller", "response_type": "yes_no_unknown", "fields": [
            "active_termites", "termite_or_wood_rot_needing_repair", "previous_termite_damage",
            "previous_termite_treatment", "improper_drainage", "water_damage_not_flood",
            "landfill_settling_soil_movement_fault_lines", "single_blockable_main_drain",
            "previous_structural_or_roof_repair", "hazardous_toxic_waste", "asbestos_components",
            "urea_formaldehyde_insulation", "radon_gas", "lead_based_paint", "aluminum_wiring",
            "previous_fires", "unplatted_easements", "subsurface_structure_or_pits",
            "previous_methamphetamine_use",
        ], "notes_field": "conditions_explanation"},
        {"id": "repairs_and_flood", "page": 3, "respondent": "seller", "response_type": "yes_no_unknown", "fields": [
            "property_needs_repair", "present_flood_insurance", "previous_reservoir_release_flooding",
            "previous_natural_flood_water_penetration", "in_100_year_floodplain",
            "in_500_year_floodplain", "in_floodway", "in_flood_pool", "in_reservoir",
            "filed_flood_claim", "received_fema_or_sba_assistance",
        ], "notes_field": "repairs_flood_explanation"},
        {"id": "additional_disclosures", "page": 4, "respondent": "seller", "response_type": "yes_no_unknown", "fields": [
            "unpermitted_modifications", "hoa_assessments", "common_area", "deed_or_ordinance_violations",
            "property_lawsuits", "health_or_safety_condition", "large_rainwater_system",
            "groundwater_or_subsidence_district", "conservation_easements", "covered_by_insurance",
            "covered_by_windstorm_insurance", "unable_to_insure", "private_road_maintenance",
            "storage_tanks", "large_aboveground_storage_tanks",
        ], "notes_field": "additional_disclosures_explanation"},
    ],
    "signers": [
        {"role": "seller", "page": 4, "purpose": "seller_disclosure_signature", "required": True, "max_signers": 2},
        {"role": "purchaser", "page": 4, "purpose": "receipt_acknowledgment", "required": False, "max_signers": 2},
    ],
}

TREC_61_0_SCHEMA = {
    "form_code": "TREC-61-0",
    "source_revision": "05-04-2026",
    "pages": 2,
    "sections": [
        {"id": "groundwater_and_wells", "page": 1, "respondent": "seller", "response_type": "yes_no_unknown", "fields": [
            "in_groundwater_district", "groundwater_district", "groundwater_district_name", "groundwater_district_website",
            "water_wells_known", "water_well_count_total", "water_well_count_in_use",
            "water_well_count_capped", "water_well_permits", "wells_seller_only",
            "wells_other_ownership", "well_description", "well_owners_operators",
            "well_beneficiary", "well_agreement",
        ]},
        {"id": "other_water_well_rights", "page": 2, "respondent": "seller", "response_type": "yes_no_unknown", "fields": [
            "water_well_on_another_property", "water_well_relies_on_outside_rights",
            "groundwater_rights_severed_sold_leased",
        ], "notes_field": "other_water_well_rights_explanation"},
        {"id": "surface_water", "page": 2, "respondent": "seller", "response_type": "yes_no_unknown", "fields": [
            "surface_water_right", "surface_water_right_number", "surface_water_ownership",
            "pond_lake_or_water_tank",
        ]},
    ],
    "signers": [
        {"role": "seller", "page": 2, "purpose": "seller_disclosure_signature", "required": True, "max_signers": 2},
        {"role": "buyer", "page": 2, "purpose": "buyer_initials_and_acknowledgment", "required": False, "max_signers": 2},
    ],
}

def schema_for(form_code: str) -> dict:
    if form_code == "TREC-55-1":
        return TREC_55_1_SCHEMA
    if form_code == "TREC-61-0":
        return TREC_61_0_SCHEMA
    raise ValueError("Unsupported seller disclosure form.")

def validate_response_keys(form_code: str, response: dict) -> None:
    schema = schema_for(form_code)
    allowed = {"property_address"}
    for section in schema["sections"]:
        allowed.update(section.get("fields", []))
        if section.get("notes_field"):
            allowed.add(section["notes_field"])
    unknown = sorted(key for key in set(response) - allowed if not key.startswith(("item_", "question_", "notes_")))
    if unknown:
        raise ValueError(f"Unsupported {form_code} response fields: {', '.join(unknown)}")
