import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads(
    (ROOT / "docs" / "AI_OFFER_REVIEW_CALIBRATION_FIXTURES.json").read_text(
        encoding="utf-8"
    )
)


class AiCalibrationFixtureTests(unittest.TestCase):
    def test_fixture_pack_contains_exactly_five_distinct_documented_cases(self):
        scenarios = FIXTURES["scenarios"]
        self.assertEqual([item["id"] for item in scenarios], [
            "AI-CAL-01", "AI-CAL-02", "AI-CAL-03", "AI-CAL-04", "AI-CAL-05"
        ])
        self.assertEqual(len({item["id"] for item in scenarios}), 5)
        self.assertIn("Five completed expert reviews", FIXTURES["release_gate"])

    def test_fixture_pack_is_anonymized_and_has_review_prompts(self):
        serialized = json.dumps(FIXTURES).lower()
        for forbidden in ("@", "mls", "street", "drive", "avenue", "client_name"):
            self.assertNotIn(forbidden, serialized)
        for scenario in FIXTURES["scenarios"]:
            self.assertTrue(scenario["property_context"].startswith("City/county only"))
            self.assertTrue(scenario["review_question"])
            self.assertIn("market_context", scenario)

    def test_fixture_values_are_bounded_and_typed(self):
        for scenario in FIXTURES["scenarios"]:
            self.assertRegex(scenario["id"], r"^AI-CAL-0[1-5]$")
            self.assertIsInstance(scenario["option_days"], int)
            self.assertGreaterEqual(scenario["option_days"], 0)
            self.assertIsInstance(scenario["sale_contingency"], bool)
            self.assertIsInstance(scenario["seller_concessions"], int)
            self.assertGreaterEqual(scenario["seller_concessions"], 0)


if __name__ == "__main__":
    unittest.main()
