import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "feedback-alert" / "index.py"
SPEC = importlib.util.spec_from_file_location("feedback_alert", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FeedbackAlertPrivacyTests(unittest.TestCase):
    def test_ai_calibration_alert_redacts_identity_and_browser_context(self):
        subject, text, html = MODULE._build_email({
            "issueType": "ai_review",
            "calibrationScenario": "AI-CAL-01",
            "accountEmail": "reviewer@example.com",
            "pageUrl": "https://homeofferflow.com/?buyerEmail=secret@example.com",
            "userAgent": "private-browser-details",
            "message": "Anonymized calibration note.",
        })

        self.assertIn("redacted for calibration", text)
        self.assertIn("redacted for calibration", html)
        self.assertNotIn("reviewer@example.com", text)
        self.assertNotIn("secret@example.com", text)
        self.assertNotIn("private-browser-details", text)
        self.assertNotIn("reviewer@example.com", html)
        self.assertNotIn("secret@example.com", html)
        self.assertNotIn("private-browser-details", html)

    def test_non_calibration_alert_keeps_operational_context(self):
        _subject, text, _html = MODULE._build_email({
            "issueType": "bug",
            "accountEmail": "agent@example.com",
            "pageUrl": "https://homeofferflow.com/",
            "userAgent": "browser-details",
            "message": "The submit button is not responding.",
        })

        self.assertIn("agent@example.com", text)
        self.assertIn("https://homeofferflow.com/", text)
        self.assertIn("browser-details", text)


if __name__ == "__main__":
    unittest.main()
