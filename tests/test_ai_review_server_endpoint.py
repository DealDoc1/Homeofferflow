import importlib.util
from io import BytesIO
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "ai-offer-review.py"
SPEC = importlib.util.spec_from_file_location("save_ai_review", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AiReviewServerEndpointTests(unittest.TestCase):
    class _Response:
        status_code = 200
        text = "1"

        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    def test_model_selection_moves_the_legacy_flash_alias_and_retains_other_overrides(self):
        for value in (None, "", "gemini-2.5-flash", " gemini-2.5-flash "):
            with self.subTest(value=value):
                self.assertEqual(MODULE._offer_review_model(value), "gemini-3.1-flash-lite")
        self.assertEqual(MODULE._offer_review_model("gemini-3.5-flash-lite"), "gemini-3.5-flash-lite")
        self.assertEqual(MODULE._offer_review_model(None, "fixture-model"), "fixture-model")

    def run_live_review(self, provider):
        body = b'{"offer":{"offerPrice":350000}}'
        request = SimpleNamespace(rfile=BytesIO(body), headers={
            "Content-Length": str(len(body)), "Authorization": "Bearer fixture",
        })
        with patch.object(MODULE, "_verified_user", return_value={"id": "agent"}), \
             patch.object(MODULE, "GEMINI_API_KEY", "private-fixture-key"), \
             patch.object(MODULE, "_post_gemini", side_effect=provider) as post, \
             patch.object(MODULE, "_json_response") as send:
            MODULE.handler.do_POST(request)
        return send.call_args.args[1:], post

    def test_live_review_uses_complete_answer_parts_and_retains_the_response_contract(self):
        response = self._Response({"candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"thought": True, "text": "internal analysis"},
            {"text": '{"score": 70,'},
            {"text": '"summary":"Review the entered terms."}'},
        ]}}]})
        (status, result), post = self.run_live_review([response])
        self.assertEqual(status, 200)
        self.assertEqual(result["source"], "gemini")
        self.assertEqual(result["model"], MODULE.GEMINI_MODEL)
        self.assertIn("components", result)
        self.assertNotIn("internal analysis", json.dumps(result))
        post.assert_called_once()
        config = post.call_args.args[1]["generationConfig"]
        self.assertEqual(config["maxOutputTokens"], 1200)
        self.assertEqual(config["responseMimeType"], "application/json")
        self.assertTrue({"temperature", "topP", "topK"}.isdisjoint(config))

    def test_incomplete_or_rejected_review_uses_rules_without_provider_detail(self):
        stopped = self._Response({"candidates": [{"finishReason": "MAX_TOKENS", "content": {
            "parts": [{"text": '{"score":100}'}],
        }}]})
        rejected = self._Response({})
        rejected.status_code = 400
        rejected.text = "private provider response"
        for provider, source in ((stopped, "rules_fallback_parse_error"),
                                 (rejected, "rules_fallback_gemini_error"),
                                 (httpx.ConnectError("private transport detail"), "rules_fallback_gemini_error")):
            with self.subTest(source=source):
                (status, result), post = self.run_live_review([provider])
                self.assertEqual(status, 200)
                self.assertEqual(result["source"], source)
                self.assertNotIn("private", json.dumps(result))
                post.assert_called_once()

    def test_provider_key_is_only_in_a_request_header(self):
        client = Mock()
        context = Mock()
        context.__enter__ = Mock(return_value=client)
        context.__exit__ = Mock(return_value=False)
        with patch.object(MODULE, "GEMINI_API_KEY", "private-fixture-key"), \
             patch.object(MODULE.httpx, "Client", return_value=context):
            MODULE._post_gemini(MODULE.DEFAULT_GEMINI_MODEL, {"contents": []}, timeout=18)
        self.assertNotIn("private-fixture-key", client.post.call_args.args[0])
        self.assertEqual(client.post.call_args.kwargs["headers"], {"x-goog-api-key": "private-fixture-key"})

    def test_optional_search_keeps_both_controls_and_uses_the_compatible_request(self):
        response = self._Response({"candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"thought": True, "text": "ignored"},
            {"text": '{"found": true, "confidence": "medium"}'},
        ]}}]})
        with patch.object(MODULE, "ENABLE_PROPERTY_CONTEXT", True), \
             patch.object(MODULE, "GEMINI_API_KEY", "fixture-key"), \
             patch.object(MODULE, "_post_gemini", return_value=response) as post:
            offer = {"propertyAddress": "1 Fictional Lane"}
            self.assertFalse(MODULE._grounded_property_context(offer)["found"])
            post.assert_not_called()
            self.assertTrue(MODULE._grounded_property_context(offer, True)["found"])
            post.assert_called_once()
            model, body = post.call_args.args
            self.assertEqual(model, MODULE.GEMINI_GROUNDING_MODEL)
            self.assertEqual(body["tools"], [{"google_search": {}}])
            self.assertEqual(body["generationConfig"], {"maxOutputTokens": 1200})

    def test_snapshot_parser_bounds_score_and_keeps_server_owned_fields_out(self):
        parsed = MODULE._parse_snapshot(
            b'{"offerId":"12345678-1234-1234-1234-123456789012","score":88,"summary":"Useful","risks":{"items":[]},"suggestions":{"items":[]},"user_id":"attacker"}'
        )
        self.assertEqual(parsed["score"], 88)
        self.assertNotIn("user_id", parsed)

    def test_snapshot_parser_rejects_invalid_score_and_offer_id(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 100"):
            MODULE._parse_snapshot(b'{"score":101}')
        with self.assertRaisesRegex(ValueError, "offer id is invalid"):
            MODULE._parse_snapshot(b'{"offerId":"not-a-real-id"}')

    def test_ui_uses_server_endpoint_with_session_token(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("action: 'save_snapshot'", html)
        self.assertIn("action:'list_snapshots'", html)
        self.assertIn("/api/ai-offer-review", html)
        self.assertIn("'Authorization': `Bearer ${token}`", html)
        self.assertNotIn("client.from('hof_ai_offer_reviews').insert", html)

    def test_paid_model_review_requires_a_server_verified_session(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        review_start = source.index('offer = payload.get("offer") or payload')
        model_start = source.index("if not GEMINI_API_KEY:", review_start)
        review_path = source[review_start:model_start]
        self.assertIn('user = _verified_user(self.headers.get("Authorization", ""))', review_path)
        self.assertIn('"source": "rules_fallback_sign_in_required"', review_path)
        self.assertIn('"aiAccess": "sign_in_required"', review_path)
        self.assertLess(
            source.index('user = _verified_user(self.headers.get("Authorization", ""))', review_start),
            source.index("property_context = _select_property_context(", review_start),
        )

    def test_ui_keeps_a_no_cost_terms_review_available_before_sign_in(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        start = html.index("async function runLiveAiOfferReview()")
        end = html.index("function openAiCalibrationFeedback", start)
        review = html[start:end]
        self.assertIn("const token = hofAuth?.session?.access_token;", review)
        self.assertIn("Sign in to unlock the expanded AI review.", review)
        self.assertLess(review.index("if (!token)"), review.index("fetch('/api/ai-offer-review'"))

    def test_server_only_migration_removes_browser_privileges(self):
        migration = (ROOT / "supabase" / "homeofferflow_ai_reviews_server_only.sql").read_text(encoding="utf-8")
        self.assertIn("revoke all on table public.hof_ai_offer_reviews from anon, authenticated", migration)
        self.assertIn("grant all on table public.hof_ai_offer_reviews to service_role", migration)

    def test_list_snapshots_is_scoped_and_compact(self):
        original_url = MODULE.SUPABASE_URL
        original_key = MODULE.SUPABASE_SERVICE_ROLE_KEY
        MODULE.SUPABASE_URL = "https://example.supabase.co"
        MODULE.SUPABASE_SERVICE_ROLE_KEY = "service-role"
        response = self._Response([
            {
                "id": "review-1",
                "offer_id": "offer-1",
                "created_at": "2026-08-08T12:00:00Z",
                "score": 82,
                "summary": "  Useful review  ",
                "risks": {"items": ["Check dates"]},
                "suggestions": ["ignored-shape"],
                "user_id": "other-user",
            }
        ])
        try:
            with patch.object(MODULE.httpx, "get", return_value=response) as get:
                rows = MODULE._list_snapshots({"id": "user-1"}, 100)
        finally:
            MODULE.SUPABASE_URL = original_url
            MODULE.SUPABASE_SERVICE_ROLE_KEY = original_key
        self.assertEqual(rows[0]["summary"], "Useful review")
        self.assertEqual(rows[0]["suggestions"], {})
        self.assertNotIn("user_id", rows[0])
        self.assertIn("user_id=eq.user-1", get.call_args.args[0])
        self.assertIn("limit=25", get.call_args.args[0])
        self.assertIn("review_mode", get.call_args.args[0])

    def test_snapshot_review_mode_is_normalized_to_live_or_rules_fallback(self):
        parsed = MODULE._parse_snapshot(b'{"reviewMode":"unexpected"}')
        self.assertEqual(parsed["review_mode"], "rules_fallback")
        parsed = MODULE._parse_snapshot(b'{"reviewMode":"live_ai"}')
        self.assertEqual(parsed["review_mode"], "live_ai")

    def test_public_property_grounding_is_off_by_default_and_requires_two_explicit_controls(self):
        self.assertFalse(MODULE.ENABLE_PROPERTY_CONTEXT)
        self.assertEqual(
            MODULE._grounded_property_context({"propertyAddress": "1 Main St"}, include_public_context=False)["reason"],
            "property_context_disabled_or_no_api_key",
        )
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn('payload.get("includePublicPropertyContext") is True', source)
        self.assertIn('ENABLE_PROPERTY_CONTEXT") or "false"', source)


if __name__ == "__main__":
    unittest.main()
