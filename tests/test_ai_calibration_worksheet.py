import unittest
from pathlib import Path


WORKSHEET = (Path(__file__).resolve().parents[1] / "docs" / "AI_OFFER_REVIEW_CALIBRATION_WORKSHEET.md").read_text(encoding="utf-8")
PAYLOADS = (Path(__file__).resolve().parents[1] / "docs" / "AI_OFFER_REVIEW_CALIBRATION_PAYLOADS.md").read_text(encoding="utf-8")


class AiCalibrationWorksheetTests(unittest.TestCase):
    def test_worksheet_requires_five_anonymized_expert_reviews(self):
        for scenario in ("AI-CAL-01", "AI-CAL-02", "AI-CAL-03", "AI-CAL-04", "AI-CAL-05"):
            self.assertIn(scenario, WORKSHEET)
        self.assertIn("Do not change scoring", WORKSHEET)
        self.assertIn("client names, exact property addresses, MLS numbers", WORKSHEET)
        self.assertIn("Reviewer disposition", WORKSHEET)

    def test_payload_pack_matches_the_five_review_cases_and_keeps_them_anonymous(self):
        for scenario in ("AI-CAL-01", "AI-CAL-02", "AI-CAL-03", "AI-CAL-04", "AI-CAL-05"):
            self.assertIn(scenario, PAYLOADS)
        self.assertIn("Do not use exact addresses, names, MLS numbers", PAYLOADS)
        self.assertIn("as a prediction of acceptance", PAYLOADS)
        self.assertIn("Do not change scoring", PAYLOADS)


if __name__ == "__main__":
    unittest.main()
