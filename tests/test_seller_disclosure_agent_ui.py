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
        ):
            self.assertIn("['" + key + "'", html)


if __name__ == "__main__":
    unittest.main()
