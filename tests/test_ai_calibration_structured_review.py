from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AiCalibrationStructuredReviewTests(unittest.TestCase):
    def test_calibration_form_captures_review_dimensions(self):
        expected_ids = [
            "aiFeedbackStructuredFields",
            "aiFeedbackUseful",
            "aiFeedbackConcern",
            "aiFeedbackMissing",
            "aiFeedbackDisclaimer",
            "aiFeedbackOverclaiming",
            "aiFeedbackDisposition",
        ]
        for field_id in expected_ids:
            self.assertIn(f'id="{field_id}"', HTML)

    def test_calibration_submission_requires_structured_evidence(self):
        self.assertIn("Complete every calibration review field before submitting.", HTML)
        self.assertIn("const missingStructured = Object.entries(aiReviewFields)", HTML)
        self.assertIn("Reviewer disposition:", HTML)
        self.assertIn("Misleading or unsafe:", HTML)
        self.assertIn("Insufficient or missing:", HTML)

    def test_structured_fields_only_show_for_ai_review(self):
        self.assertIn("if (structured) structured.style.display = isCalibration ? 'block' : 'none';", HTML)
        self.assertIn("message: submittedMessage", HTML)

    def test_saved_review_history_exposes_trend_details_and_reopen_action(self):
        self.assertIn("const trend = scored.length > 1", HTML)
        self.assertIn("Show risks and next moves", HTML)
        self.assertIn("Open linked offer", HTML)
        self.assertIn("resumeOffer('${escapeAttr(review.offer_id)}')", HTML)


if __name__ == "__main__":
    unittest.main()
