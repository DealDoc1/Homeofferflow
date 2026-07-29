import importlib.util
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "ai-offer-review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ai_offer_review_rate_limit", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ai_review = load_module()


class AiOfferReviewRateLimitTests(unittest.TestCase):
    def setUp(self):
        ai_review.GEMINI_API_KEY = "gemini-test-key"
        ai_review.SUPABASE_URL = "https://example.supabase.co"
        ai_review.SUPABASE_SERVICE_ROLE_KEY = "service-test-key"
        ai_review.AI_OFFER_REVIEW_HOURLY_LIMIT = 12

    def _request(self, offer=None, headers=None):
        raw = json.dumps({"offer": offer or {"address": "1438 Whitaker Road"}}).encode("utf-8")
        request = ai_review.handler.__new__(ai_review.handler)
        request.headers = {"Content-Length": str(len(raw)), "x-forwarded-for": "203.0.113.9"}
        request.headers.update(headers or {})
        request.rfile = io.BytesIO(raw)
        return request

    def test_rate_key_is_hashed_and_not_raw_client_address(self):
        key = ai_review._client_rate_limit_key({"x-forwarded-for": "203.0.113.9, 10.0.0.1"})
        self.assertEqual(len(key), 64)
        self.assertNotIn("203.0.113.9", key)
        self.assertRegex(key, r"^[a-f0-9]{64}$")

    def test_rate_limited_request_does_not_start_paid_ai_calls(self):
        request = self._request()
        captured = {}
        with patch.object(ai_review, "_json_response", lambda _request, status, body: captured.update(status=status, body=body)), \
             patch.object(ai_review, "_consume_ai_offer_review_rate_limit", return_value=(False, "ok")), \
             patch.object(ai_review, "_grounded_property_context") as grounding:
            request.do_POST()
        self.assertEqual(captured["status"], 429)
        self.assertEqual(captured["body"]["code"], "ai_review_rate_limited")
        grounding.assert_not_called()

    def test_unavailable_limiter_fails_closed_before_paid_ai_calls(self):
        request = self._request()
        captured = {}
        with patch.object(ai_review, "_json_response", lambda _request, status, body: captured.update(status=status, body=body)), \
             patch.object(ai_review, "_consume_ai_offer_review_rate_limit", return_value=(False, "rate_limit_unavailable")), \
             patch.object(ai_review, "_grounded_property_context") as grounding:
            request.do_POST()
        self.assertEqual(captured["status"], 503)
        self.assertEqual(captured["body"]["code"], "ai_review_unavailable")
        grounding.assert_not_called()

    def test_rules_fallback_stays_available_without_a_gemini_key(self):
        ai_review.GEMINI_API_KEY = ""
        request = self._request()
        captured = {}
        with patch.object(ai_review, "_json_response", lambda _request, status, body: captured.update(status=status, body=body)), \
             patch.object(ai_review, "_consume_ai_offer_review_rate_limit") as limiter, \
             patch.object(ai_review, "_grounded_property_context", return_value={"found": False}):
            request.do_POST()
        self.assertEqual(captured["status"], 200)
        self.assertEqual(captured["body"]["source"], "rules_fallback_no_api_key")
        limiter.assert_not_called()

    def test_rate_limit_schema_is_private_to_service_role(self):
        sql = (ROOT / "supabase" / "homeofferflow_ai_offer_review_rate_limit.sql").read_text(encoding="utf-8")
        self.assertIn("enable row level security", sql.lower())
        self.assertIn("revoke all on table public.hof_ai_offer_review_rate_limits from public, anon, authenticated", sql.lower())
        self.assertIn("create policy hof_ai_offer_review_rate_limits_deny_browser", sql.lower())
        self.assertIn("grant execute on function public.hof_consume_ai_offer_review_rate_limit(text, integer) to service_role", sql.lower())
        self.assertNotIn("client_ip", sql.lower())


if __name__ == "__main__":
    unittest.main()
