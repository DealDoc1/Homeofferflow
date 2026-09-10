from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AiCalibrationStructuredReviewTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for calibration reviewer runtime tests')
    def test_calibration_launcher_reveals_the_reviewer_form_in_a_real_dom_fixture(self):
        result = subprocess.run(
            ['node', '--test', str(ROOT / 'tests' / 'ai_calibration_feedback_launcher.runtime.cjs')],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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

    def test_calibration_launcher_refreshes_the_reviewer_form_and_uses_reviewer_language(self):
        launcher = HTML[HTML.index("function openAiCalibrationFeedback()"):HTML.index("async function saveAiReviewResultToSupabase", HTML.index("function openAiCalibrationFeedback()"))]
        self.assertIn("syncFeedbackFields();", launcher)
        fields = HTML[HTML.index("function syncFeedbackFields()"):HTML.index("function closeBetaFeedback()", HTML.index("function syncFeedbackFields()"))]
        self.assertIn("const isCalibration", fields)
        self.assertIn("Reviewer summary", fields)
        self.assertIn("Summarize your independent review.", fields)
        self.assertIn("Do not include client names, exact addresses, MLS numbers", fields)

    def test_saved_review_history_exposes_trend_details_and_reopen_action(self):
        self.assertIn("const trend = scored.length > 1", HTML)
        self.assertIn("Show risks and next moves", HTML)
        self.assertIn("Open linked offer", HTML)
        self.assertIn("resumeOffer('${escapeAttr(review.offer_id)}')", HTML)


if __name__ == "__main__":
    unittest.main()
