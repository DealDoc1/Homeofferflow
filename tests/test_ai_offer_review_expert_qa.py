from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
QA = (ROOT / "docs" / "AI_OFFER_REVIEW_EXPERT_QA.md").read_text(encoding="utf-8")


class AiOfferReviewExpertQaTests(unittest.TestCase):
    def test_calibration_worksheet_requires_anonymization_and_release_threshold(self):
        for phrase in (
            "Remove names, exact addresses",
            "HomeOfferFlow output",
            "Missing issue",
            "educational disclaimer",
            "at least five anonymized scenarios",
            "A Texas broker or experienced Texas",
        ):
            self.assertIn(phrase, QA)


if __name__ == "__main__":
    unittest.main()
