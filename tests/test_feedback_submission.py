import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "submit-feedback" / "index.py"
SPEC = importlib.util.spec_from_file_location("submit_feedback", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FeedbackSubmissionTests(unittest.TestCase):
    def test_ai_calibration_requires_anonymization(self):
        payload = b'{"issueType":"ai_review","message":"Needs review","role":"agent"}'
        with self.assertRaisesRegex(ValueError, "must be anonymized"):
            MODULE._parse_payload(payload)

    def test_payload_normalizes_context_and_rejects_unknown_issue_type(self):
        payload = b'{"issueType":"ai_review","message":"  anonymous note  ","role":"agent","anonymized":true,"pageUrl":"https://example.com/test","userAgent":"test"}'
        parsed = MODULE._parse_payload(payload)
        self.assertEqual(parsed["message"], "anonymous note")
        self.assertEqual(parsed["issue_type"], "ai_review")
        with self.assertRaisesRegex(ValueError, "valid feedback issue type"):
            MODULE._parse_payload(b'{"issueType":"nope","message":"x"}')

    def test_ui_uses_authenticated_feedback_endpoint(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("/api/submit-feedback", html)
        self.assertIn("'Authorization': `Bearer ${feedbackToken}`", html)
        self.assertNotIn("client.from('hof_feedback').insert(payload)", html)


if __name__ == "__main__":
    unittest.main()
