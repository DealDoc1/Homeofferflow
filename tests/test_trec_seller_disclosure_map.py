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
                ("defect_other_structural_components", 255, 405),
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
