import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class SellerDisclosureAgentUiTests(unittest.TestCase):
    def test_agent_draft_card_has_source_gate_save_and_private_preview(self):
        html = (ROOT / "index.html").read_text()
        self.assertIn('hof-seller-disclosure-draft-ui-v1', html)
        self.assertIn("approved_brokerage_sources", html)
        self.assertIn("create_seller_disclosure_draft", html)
        self.assertIn("preview_seller_disclosure", html)
        self.assertIn("seller_review_attested", html)
        self.assertIn("does not send or sign", html)

    def test_response_controls_cover_all_mapped_groups(self):
        html = (ROOT / "index.html").read_text()
        for key in (
            "range", "smoke_detector", "defect_interior_walls",
            "active_termites", "present_flood_insurance",
            "unpermitted_modifications", "large_aboveground_storage_tanks",
            "property_needs_repair", "working_smoke_detectors",
            "filed_flood_claim", "received_fema_or_sba_assistance",
        ):
            self.assertIn("['" + key + "'", html)

    def test_water_rights_controls_are_saved_and_renderer_aliases_exist(self):
        html = (ROOT / "index.html").read_text()
        renderer = (ROOT / "lib" / "trec_seller_disclosure.py").read_text()
        for key in (
            "in_groundwater_district", "water_wells_known",
            "water_well_on_another_property",
            "water_well_relies_on_outside_rights",
            "groundwater_rights_severed_sold_leased",
            "surface_water_right", "pond_lake_or_water_tank",
        ):
            self.assertIn("['" + key + "'", html)
        self.assertIn("data-water-response", html)
        self.assertIn("waterRightsData", html)
        self.assertIn("semantic_water", renderer)
        self.assertIn("property_needs_repair", renderer)
        self.assertIn("filed_flood_claim", renderer)


if __name__ == "__main__":
    unittest.main()
