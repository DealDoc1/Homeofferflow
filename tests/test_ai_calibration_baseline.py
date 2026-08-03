import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "AI_OFFER_REVIEW_CALIBRATION_BASELINE.json"


class AiCalibrationBaselineTests(unittest.TestCase):
    def test_baseline_is_explicitly_not_human_evidence(self):
        report = json.loads(BASELINE.read_text(encoding="utf-8"))
        self.assertFalse(report["calibration_evidence"])
        self.assertIn("Five completed independent expert reviews", report["release_gate"])

    def test_baseline_contains_all_five_documented_scenarios(self):
        report = json.loads(BASELINE.read_text(encoding="utf-8"))
        self.assertEqual(
            set(report["scenarios"]),
            {"AI-CAL-01", "AI-CAL-02", "AI-CAL-03", "AI-CAL-04", "AI-CAL-05"},
        )
        for scenario in report["scenarios"].values():
            self.assertIn("review_question", scenario)
            self.assertIsInstance(scenario["review_flags"], list)
            self.assertIn("technical_baseline", scenario)
            self.assertIn("disclaimer", scenario["technical_baseline"])

    def test_baseline_surfaces_calibration_watch_flags_without_changing_scoring(self):
        report = json.loads(BASELINE.read_text(encoding="utf-8"))
        self.assertIn("summary_market_mode_conflict", report["scenarios"]["AI-CAL-02"]["review_flags"])
        self.assertIn("seller_advantage_score_low", report["scenarios"]["AI-CAL-01"]["review_flags"])


if __name__ == "__main__":
    unittest.main()
