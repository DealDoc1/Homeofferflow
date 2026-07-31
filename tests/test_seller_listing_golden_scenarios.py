from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "SELLER_LISTING_GOLDEN_SCENARIOS.md").read_text(encoding="utf-8")


class SellerListingGoldenScenarioTests(unittest.TestCase):
    def test_catalog_contains_two_anonymized_intake_scenarios(self):
        for scenario in ("SL-CAL-01", "SL-CAL-02"):
            self.assertIn(scenario, DOC)
        self.assertIn("two sellers", DOC)
        self.assertIn("One landlord", DOC)

    def test_scenarios_keep_forms_source_gated(self):
        self.assertIn("do not create or send TXR-1101 or TXR-1406", DOC)
        self.assertIn("do not create or send TXR-1102", DOC)
        self.assertIn("do not authorize any seller/listing form release", DOC.lower())
        self.assertIn("aggregate counts only", DOC)


if __name__ == "__main__":
    unittest.main()
