from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class InterviewValidationFeedbackTests(unittest.TestCase):
    def test_guided_interview_has_live_validation_status(self):
        self.assertIn('id="validationStatus" role="status" aria-live="polite"', INDEX)
        self.assertIn("function setValidationStatus(message)", INDEX)
        self.assertIn("setValidationStatus('Please complete: '", INDEX)
        self.assertNotIn("alert('Please complete: '", INDEX)


if __name__ == "__main__":
    unittest.main()
