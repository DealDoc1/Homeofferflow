import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "api" / "feedback-alert" / "index.py"
SPEC = importlib.util.spec_from_file_location("feedback_alert", MODULE_PATH)
feedback_alert = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(feedback_alert)


class FeedbackAlertTests(unittest.TestCase):
    def test_product_feedback_email_uses_finished_product_language(self):
        subject, text, html = feedback_alert._build_email({"issueType": "form", "message": "Please review."})
        self.assertEqual(subject, "HomeOfferFlow product feedback: form")
        self.assertIn("New HomeOfferFlow product feedback", text)
        self.assertIn("New HomeOfferFlow product feedback", html)
        self.assertNotIn("beta", subject.lower() + text.lower() + html.lower())

    def test_verified_transactional_sender_is_used_without_double_wrapping(self):
        old_from = feedback_alert.FROM_EMAIL
        try:
            feedback_alert.FROM_EMAIL = "HomeOfferFlow Offers <offers@offers.homeofferflow.com>"
            self.assertEqual(
                feedback_alert._feedback_from_header(),
                "HomeOfferFlow Offers <offers@offers.homeofferflow.com>",
            )
            feedback_alert.FROM_EMAIL = "offers@offers.homeofferflow.com"
            self.assertEqual(
                feedback_alert._feedback_from_header(),
                "HomeOfferFlow Feedback <offers@offers.homeofferflow.com>",
            )
        finally:
            feedback_alert.FROM_EMAIL = old_from


if __name__ == "__main__":
    unittest.main()
