import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "lib" / "trec_seller_disclosure.py"
SPEC = importlib.util.spec_from_file_location("trec_seller_disclosure", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TrecSellerDisclosureMapTests(unittest.TestCase):
    def test_source_contracts_are_explicit_and_gated(self):
        for code, pages in (("TREC-55-1", 4), ("TREC-61-0", 2)):
            contract = MODULE.source_contract(code)
            self.assertEqual(contract["page_count"], pages)
            self.assertEqual(contract["activation_status"], "pending_visual_qa")
            self.assertEqual(len(contract["source_sha256"]), 64)
            self.assertIn("property_address" if code == "TREC-55-1" else "property_address_page_1", contract["field_map"])

    def test_trec_55_occupancy_duration_anchor_is_explicit(self):
        self.assertEqual(
            MODULE.TREC_55_1_MAP["seller_occupancy_duration"],
            {"page": 1, "x": 492, "y": 596, "width": 100},
        )

    def test_signature_anchors_match_reviewed_lines(self):
        self.assertEqual(MODULE.TREC_55_1_MAP["seller_signature_1"]["y"], 205)
        self.assertEqual(MODULE.TREC_55_1_MAP["purchaser_signature_1"]["y"], 115)
        self.assertEqual(MODULE.TREC_61_0_MAP["seller_signature_1"]["y"], 178)
        self.assertEqual(MODULE.TREC_61_0_MAP["buyer_signature_1"]["y"], 122)

    def test_trec_55_repair_awareness_anchors_are_explicit(self):
        self.assertEqual(MODULE.TREC_55_1_MAP["repair_condition_yes"], {"page": 3, "x": 487, "y": 728})
        self.assertEqual(MODULE.TREC_55_1_MAP["repair_condition_no"], {"page": 3, "x": 58, "y": 713})

    def test_trec_55_smoke_detector_anchors_are_explicit(self):
        field_map = MODULE.TREC_55_1_MAP
        self.assertEqual(field_map["smoke_detectors_yes"], {"page": 2, "x": 219, "y": 728})
        self.assertEqual(field_map["smoke_detectors_no"], {"page": 2, "x": 248, "y": 728})
        self.assertEqual(field_map["smoke_detectors_unknown"], {"page": 2, "x": 283, "y": 728})

    def test_trec_55_reviewed_condition_rows_are_explicit(self):
        self.assertEqual(
            MODULE.TREC_55_1_CONDITION_ROWS,
            (
                ("defect_interior_walls", 58, 500),
                ("defect_ceilings", 238, 500),
                ("defect_floors", 408, 500),
                ("defect_other_structural_components", 58, 405),
                ("defect_exterior_walls", 58, 473),
                ("defect_doors", 238, 473),
                ("defect_windows", 408, 473),
                ("defect_roof", 58, 446),
                ("defect_foundation_slabs", 238, 446),
                ("defect_sidewalks", 408, 446),
                ("defect_walls_fences", 58, 419),
                ("defect_driveways", 238, 419),
                ("defect_intercom", 408, 419),
                ("defect_plumbing_sewers_septics", 58, 392),
                ("defect_electrical_systems", 238, 392),
                ("defect_lighting_fixtures", 408, 392),
            ),
        )


    def test_trec_55_water_utility_fields_are_explicit(self):
        expected = {
            "water_heater_gas": {"page": 1, "x": 172, "y": 185},
            "water_heater_electric": {"page": 1, "x": 292, "y": 185},
            "water_supply_city": {"page": 1, "x": 172, "y": 166},
            "water_supply_well": {"page": 1, "x": 292, "y": 166},
            "water_supply_mud": {"page": 1, "x": 404, "y": 166},
            "water_supply_coop": {"page": 1, "x": 512, "y": 166},
        }
        for key, anchor in expected.items():
            self.assertEqual(MODULE.TREC_55_1_MAP[key], anchor)

    def test_trec_55_roof_fields_are_explicit(self):
        self.assertEqual(
            MODULE.TREC_55_1_MAP["roof_type"],
            {"page": 1, "x": 120, "y": 140, "width": 230},
        )
        self.assertEqual(
            MODULE.TREC_55_1_MAP["roof_age"],
            {"page": 1, "x": 380, "y": 140, "width": 120},
        )

    def test_trec_55_section4_condition_rows_are_explicit(self):
        self.assertEqual(
            MODULE.TREC_55_1_CONDITION4_ROWS,
            (
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
                ("previous_methamphetamine_use", 318, 97),
            ),
        )

    def test_trec_55_first_item_response_rows_are_explicit(self):
        self.assertEqual(
            MODULE.TREC_55_1_ITEM_ROWS,
            (
                ("range", 58, 570),
                ("oven", 211, 570),
                ("microwave", 391, 570),
                ("dishwasher", 58, 552),
                ("trash_compactor", 211, 552),
                ("disposal", 391, 552),
                ("washer_dryer_hookups", 58, 534),
                ("window_screens", 211, 534),
                ("rain_gutters", 391, 534),
                ("security_system", 58, 516),
                ("fire_detection_equipment", 211, 516),
                ("intercom_system", 391, 516),
                ("tv_antenna", 58, 426),
                ("cable_tv_wiring", 211, 426),
                ("satellite_dish", 391, 426),
                ("ceiling_fans", 58, 408),
                ("attic_fans", 211, 408),
                ("exhaust_fans", 391, 408),
                ("central_ac", 58, 390),
                ("central_heating", 211, 390),
                ("wall_window_ac", 391, 390),
                ("plumbing_system", 58, 372),
                ("septic_system", 211, 372),
                ("public_sewer_system", 391, 372),
                ("patio_decking", 58, 354),
                ("outdoor_grill", 211, 354),
                ("fences", 391, 354),
                ("pool", 58, 336),
                ("sauna", 211, 336),
                ("spa", 391, 336),
                ("pool_equipment", 58, 318),
                ("pool_heater", 211, 318),
                ("automatic_lawn_sprinkler_system", 391, 318),
                ("fireplace_wood_burning", 58, 307),
                ("fireplace_mock", 391, 307),
                ("natural_gas_lines", 58, 277),
                ("gas_fixtures", 391, 277),
            ),
        )


    def test_trec_55_reviewed_item_response_rows_are_explicit(self):
        self.assertEqual(
            MODULE.TREC_55_1_ITEM_ROWS,
            (
                ("range", 58, 570),
                ("oven", 211, 570),
                ("microwave", 391, 570),
                ("dishwasher", 58, 552),
                ("trash_compactor", 211, 552),
                ("disposal", 391, 552),
                ("washer_dryer_hookups", 58, 534),
                ("window_screens", 211, 534),
                ("rain_gutters", 391, 534),
                ("security_system", 58, 516),
                ("fire_detection_equipment", 211, 516),
                ("intercom_system", 391, 516),
                ("tv_antenna", 58, 426),
                ("cable_tv_wiring", 211, 426),
                ("satellite_dish", 391, 426),
                ("ceiling_fans", 58, 408),
                ("attic_fans", 211, 408),
                ("exhaust_fans", 391, 408),
                ("central_ac", 58, 390),
                ("central_heating", 211, 390),
                ("wall_window_ac", 391, 390),
                ("plumbing_system", 58, 372),
                ("septic_system", 211, 372),
                ("public_sewer_system", 391, 372),
                ("patio_decking", 58, 354),
                ("outdoor_grill", 211, 354),
                ("fences", 391, 354),
                ("pool", 58, 336),
                ("sauna", 211, 336),
                ("spa", 391, 336),
                ("pool_equipment", 58, 318),
                ("pool_heater", 211, 318),
                ("automatic_lawn_sprinkler_system", 391, 318),
                ("fireplace_wood_burning", 58, 307),
                ("fireplace_mock", 391, 307),
                ("natural_gas_lines", 58, 277),
                ("gas_fixtures", 391, 277),
            ),
        )

    def test_trec_61_page2_response_anchors_are_explicit(self):
        field_map = MODULE.TREC_61_0_MAP
        expected = {
            "water_other_property_yes": {"page": 2, "x": 281, "y": 698},
            "water_other_property_no": {"page": 2, "x": 322, "y": 698},
            "outside_groundwater_rights_yes": {"page": 2, "x": 410, "y": 625},
            "outside_groundwater_rights_no": {"page": 2, "x": 451, "y": 625},
            "rights_severed_yes": {"page": 2, "x": 72, "y": 545},
            "rights_severed_no": {"page": 2, "x": 112, "y": 545},
            "surface_water_right_yes": {"page": 2, "x": 428, "y": 485},
            "surface_water_right_no": {"page": 2, "x": 468, "y": 485},
            "pond_lake_tank_yes": {"page": 2, "x": 72, "y": 390},
            "pond_lake_tank_no": {"page": 2, "x": 112, "y": 390},
        }
        for key, anchor in expected.items():
            self.assertEqual(field_map[key], anchor)

    def test_trec_61_water_well_anchors_match_reviewed_rows(self):
        field_map = MODULE.TREC_61_0_MAP
        self.assertEqual(field_map["water_well_yes"], {"page": 1, "x": 383, "y": 258})
        self.assertEqual(field_map["water_well_no"], {"page": 1, "x": 427, "y": 258})
        self.assertEqual(field_map["well_owned_seller"], {"page": 1, "x": 48, "y": 145})
        self.assertEqual(field_map["well_other_party"], {"page": 1, "x": 48, "y": 120})

    def test_preview_requires_explicit_qa_mode(self):
        with self.assertRaisesRegex(ValueError, "qa_mode"):
            MODULE.render_unsigned_preview(b"%PDF", "TREC-55-1", {}, qa_mode=False)

    def test_source_fingerprint_gate(self):
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            MODULE.validate_source_bytes("TREC-55-1", b"not-the-approved-source")

    def test_unknown_form_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.source_contract("TREC-56-0")


if __name__ == "__main__":
    unittest.main()


def test_trec_55_1_page1_gas_and_garage_anchors():
    mapping = source_contract("TREC-55-1")["field_map"]
    assert mapping["liquid_propane_lp_community"] == {"page": 1, "x": 172, "y": 249}
    assert mapping["liquid_propane_on_property"] == {"page": 1, "x": 314, "y": 249}
    assert mapping["fuel_gas_black_iron"] == {"page": 1, "x": 185, "y": 231}
    assert mapping["fuel_gas_corrugated_stainless"] == {"page": 1, "x": 315, "y": 231}
    assert mapping["fuel_gas_copper"] == {"page": 1, "x": 450, "y": 231}
    assert mapping["garage_attached"] == {"page": 1, "x": 110, "y": 214}
    assert mapping["garage_not_attached"] == {"page": 1, "x": 230, "y": 214}
    assert mapping["garage_carport"] == {"page": 1, "x": 370, "y": 214}
    assert mapping["garage_door_electronic"] == {"page": 1, "x": 190, "y": 198}
    assert mapping["garage_door_controls"] == {"page": 1, "x": 310, "y": 198}


def test_trec_55_1_page1_safety_item_anchors():
    rows = dict((key, (x, y)) for key, x, y in TREC_55_1_ITEM_ROWS)
    assert rows["smoke_detector"] == (211, 498)
    assert rows["smoke_detector_hearing_impaired"] == (211, 480)
    assert rows["carbon_monoxide_alarm"] == (211, 462)
    assert rows["emergency_escape_ladders"] == (211, 444)


def test_trec_55_1_canonical_item_aliases():
    mapping = source_contract("TREC-55-1")["field_map"]
    assert mapping["lp_community"] == {"page": 1, "x": 172, "y": 249}
    assert mapping["lp_on_property"] == {"page": 1, "x": 314, "y": 249}
    assert mapping["fuel_gas_corrugated_steel"] == {"page": 1, "x": 315, "y": 231}
    assert mapping["carport"] == {"page": 1, "x": 370, "y": 214}
    assert mapping["garage_opener_electronic"] == {"page": 1, "x": 190, "y": 198}
    assert mapping["garage_opener_controls"] == {"page": 1, "x": 310, "y": 198}
    assert mapping["hot_tub"] == {"page": 1, "x": 470, "y": 336}


def test_trec_55_1_flood_response_anchors():
    assert TREC_55_1_FLOOD_ROWS == (
        ("present_flood_insurance", 58, 650),
        ("previous_reservoir_release_flooding", 58, 632),
        ("previous_natural_flood_water_penetration", 58, 614),
        ("in_100_year_floodplain", 58, 596),
        ("in_500_year_floodplain", 58, 578),
        ("in_floodway", 58, 560),
        ("in_flood_pool", 58, 542),
        ("in_reservoir", 58, 524),
    )
