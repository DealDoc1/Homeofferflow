import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "submit-feedback" / "index.py"
SPEC = importlib.util.spec_from_file_location("submit_feedback", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FeedbackSubmissionTests(unittest.TestCase):
    class _ProfileResponse:
        status_code = 200

        def __init__(self, rows):
            self._rows = rows

        def json(self):
            return self._rows

    def test_ai_calibration_requires_anonymization(self):
        payload = b'{"issueType":"ai_review","message":"Needs review","role":"agent"}'
        with self.assertRaisesRegex(ValueError, "must be anonymized"):
            MODULE._parse_payload(payload)

    def test_payload_normalizes_context_and_rejects_unknown_issue_type(self):
        payload = b'{"issueType":"ai_review","message":"  anonymous note  ","role":"agent","anonymized":true,"calibrationScenario":"AI-CAL-01","pageUrl":"https://example.com/test","userAgent":"test"}'
        parsed = MODULE._parse_payload(payload)
        self.assertEqual(parsed["message"], "anonymous note")
        self.assertEqual(parsed["issue_type"], "ai_review")
        self.assertEqual(parsed["calibration_scenario"], "AI-CAL-01")
        with self.assertRaisesRegex(ValueError, "valid feedback issue type"):
            MODULE._parse_payload(b'{"issueType":"nope","message":"x"}')

    def test_brokerage_access_request_is_an_allowed_authenticated_feedback_type(self):
        parsed = MODULE._parse_payload(
            b'{"issueType":"brokerage_access","message":"Please activate my membership.","role":"agent"}'
        )
        self.assertEqual(parsed["issue_type"], "brokerage_access")

    def test_ui_uses_authenticated_feedback_endpoint(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("/api/submit-feedback", html)
        self.assertIn("'Authorization': `Bearer ${feedbackToken}`", html)
        self.assertNotIn("client.from('hof_feedback').insert(payload)", html)

    def test_authoritative_role_does_not_trust_browser_role(self):
        user = {"id": "agent-1", "email": "agent@example.com"}
        with patch.object(
            MODULE.httpx,
            "get",
            return_value=self._ProfileResponse([{"role": "agent", "is_brokerage_admin": False}]),
        ):
            with patch.object(MODULE, "SUPABASE_URL", "https://example.supabase.co"), patch.object(
                MODULE, "SUPABASE_SERVICE_ROLE_KEY", "service-key"
            ):
                self.assertEqual(MODULE._authoritative_role(user), "agent")

    def test_unknown_profile_role_fails_closed_for_calibration(self):
        user = {"id": "unknown-1", "email": "unknown@example.com"}
        with patch.object(
            MODULE.httpx,
            "get",
            return_value=self._ProfileResponse([]),
        ):
            with patch.object(MODULE, "SUPABASE_URL", "https://example.supabase.co"), patch.object(
                MODULE, "SUPABASE_SERVICE_ROLE_KEY", "service-key"
            ):
                self.assertIsNone(MODULE._authoritative_role(user))


if __name__ == "__main__":
    unittest.main()
