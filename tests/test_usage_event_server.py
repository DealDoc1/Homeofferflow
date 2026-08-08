import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "submit-feedback" / "index.py"
SPEC = importlib.util.spec_from_file_location("submit_feedback_usage", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class UsageEventServerTests(unittest.TestCase):
    class _Response:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code
            self.text = "1" if payload else ""

        def json(self):
            return self._payload

    def test_usage_event_normalizes_and_limits_payload(self):
        event = MODULE._parse_usage_event({
            "eventType": "signed_packet",
            "quantity": 1,
            "billingMonth": "2026-08",
            "offerId": "12345678-1234-1234-1234-123456789012",
            "metadata": {"source": "payment_success", "signwell": {"id": "secret"}},
        })
        self.assertEqual(event["event_type"], "signed_packet")
        self.assertEqual(event["billing_month"], "2026-08")
        self.assertEqual(event["metadata"], {"source": "payment_success"})

    def test_usage_event_rejects_unknown_type_and_bad_month(self):
        with self.assertRaisesRegex(ValueError, "valid usage event"):
            MODULE._parse_usage_event({"eventType": "admin_delete", "billingMonth": "2026-08"})
        with self.assertRaisesRegex(ValueError, "YYYY-MM"):
            MODULE._parse_usage_event({"eventType": "signed_packet", "billingMonth": "August 2026"})

    def test_usage_event_rejects_invalid_quantity_and_offer_id(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 10"):
            MODULE._parse_usage_event({"eventType": "signed_packet", "quantity": 0, "billingMonth": "2026-08"})
        with self.assertRaisesRegex(ValueError, "offer ID"):
            MODULE._parse_usage_event({"eventType": "signed_packet", "billingMonth": "2026-08", "offerId": "not-an-id"})

    def test_ui_routes_usage_reads_and_writes_through_server_action(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("action: 'usage_summary'", html)
        self.assertIn("action: 'usage_preflight'", html)
        self.assertIn("action: 'usage_event'", html)
        self.assertNotIn("client\n        .from('hof_usage_events')", html)
        self.assertNotIn("client.from('hof_usage_events').insert", html)

    def test_usage_preflight_uses_authoritative_subscription_and_usage(self):
        original_url = MODULE.SUPABASE_URL
        original_key = MODULE.SUPABASE_SERVICE_ROLE_KEY
        MODULE.SUPABASE_URL = "https://example.supabase.co"
        MODULE.SUPABASE_SERVICE_ROLE_KEY = "service-role"
        responses = [
            self._Response([{"role": "agent", "is_brokerage_admin": False}]),
            self._Response([{"status": "active", "packet_limit": 3}]),
            self._Response([{"quantity": 1}]),
        ]
        try:
            with patch.object(MODULE.httpx, "get", side_effect=responses):
                result = MODULE._usage_preflight(
                    {"id": "user-1", "email": "agent@example.com"}, "2026-08", 1
                )
        finally:
            MODULE.SUPABASE_URL = original_url
            MODULE.SUPABASE_SERVICE_ROLE_KEY = original_key
        self.assertTrue(result["allowed"])
        self.assertEqual(result["used"], 1)
        self.assertEqual(result["remaining"], 2)

    def test_usage_preflight_blocks_inactive_or_exhausted_accounts(self):
        original_url = MODULE.SUPABASE_URL
        original_key = MODULE.SUPABASE_SERVICE_ROLE_KEY
        MODULE.SUPABASE_URL = "https://example.supabase.co"
        MODULE.SUPABASE_SERVICE_ROLE_KEY = "service-role"
        responses = [
            self._Response([{"role": "agent", "is_brokerage_admin": False}]),
            self._Response([{"status": "past_due", "packet_limit": 3}]),
            self._Response([{"quantity": 1}]),
        ]
        try:
            with patch.object(MODULE.httpx, "get", side_effect=responses):
                result = MODULE._usage_preflight(
                    {"id": "user-1", "email": "agent@example.com"}, "2026-08", 1
                )
        finally:
            MODULE.SUPABASE_URL = original_url
            MODULE.SUPABASE_SERVICE_ROLE_KEY = original_key
        self.assertFalse(result["allowed"])
        self.assertEqual(result["status"], "past_due")


if __name__ == "__main__":
    unittest.main()
