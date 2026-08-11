import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


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


if __name__ == "__main__":
    unittest.main()
