import unittest
from pathlib import Path


WORKSHEET = (Path(__file__).resolve().parents[1] / "docs" / "AI_OFFER_REVIEW_CALIBRATION_WORKSHEET.md").read_text(encoding="utf-8")


class AiCalibrationWorksheetTests(unittest.TestCase):
    def test_worksheet_requires_five_anonymized_expert_reviews(self):
        for scenario in ("AI-CAL-01", "AI-CAL-02", "AI-CAL-03", "AI-CAL-04", "AI-CAL-05"):
            self.assertIn(scenario, WORKSHEET)
        self.assertIn("Do not change scoring", WORKSHEET)
        self.assertIn("client names, exact property addresses, MLS numbers", WORKSHEET)
        self.assertIn("Reviewer disposition", WORKSHEET)


if __name__ == "__main__":
    unittest.main()
