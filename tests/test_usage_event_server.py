import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


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

    def test_ui_reads_usage_but_cannot_create_charges(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("action: 'usage_summary'", html)
        self.assertIn("action: 'usage_preflight'", html)
        self.assertNotIn("action: 'usage_event'", html)
        self.assertNotIn("client\n        .from('hof_usage_events')", html)
        self.assertNotIn("client.from('hof_usage_events').insert", html)

    def test_legacy_usage_writer_never_mutates_storage(self):
        with patch.object(MODULE.httpx, 'get') as read, patch.object(MODULE.httpx, 'post') as write:
            with self.assertRaisesRegex(ValueError, 'automatically'):
                MODULE._save_usage_event({'id': 'user'}, {'quantity': 9999, 'billing_month': '2099-01'})
        read.assert_not_called()
        write.assert_not_called()

    def test_legacy_browser_action_returns_retired_without_mutating_storage(self):
        body = json.dumps({'action': 'usage_event', 'quantity': 500, 'billingMonth': '2099-01'}).encode()
        handler = object.__new__(MODULE.handler)
        handler.headers = {'Content-Length': str(len(body)), 'Authorization': 'Bearer fixture'}
        handler.rfile = io.BytesIO(body)
        with patch.object(MODULE, '_verified_user', return_value={'id':'user','email':'user@example.test'}), \
             patch.object(MODULE, '_json') as reply, patch.object(MODULE.httpx, 'post') as write:
            handler.do_POST()
        self.assertEqual(reply.call_args.args[1], 410)
        write.assert_not_called()

    def test_legacy_advisory_does_not_invent_missing_access_or_zero_allowance(self):
        for subscription in ([], [{'status': 'active', 'packet_limit': 0}]):
            with patch.object(MODULE, 'SUPABASE_URL', 'https://example.test'), \
                 patch.object(MODULE, 'SUPABASE_SERVICE_ROLE_KEY', 'test-only'), \
                 patch.object(MODULE, '_authoritative_role', return_value='agent'), \
                 patch.object(MODULE.httpx, 'get', return_value=self._Response(subscription)), \
                 patch.object(MODULE, '_usage_summary', return_value={'used': 0}) as summary:
                result = MODULE._usage_preflight({'id': 'user'}, '2099-01')
            self.assertFalse(result['allowed'])
            self.assertEqual(summary.call_args.args[1], MODULE.datetime.now(MODULE.timezone.utc).strftime('%Y-%m'))
            if subscription: self.assertEqual(result['limit'], 0)

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
            with patch.object(MODULE.httpx, "get", side_effect=responses), \
                 patch.object(MODULE, '_usage_summary', return_value={'used': 1, 'reserved': 0}):
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
            with patch.object(MODULE.httpx, "get", side_effect=responses), \
                 patch.object(MODULE, '_usage_summary', return_value={'used': 1, 'reserved': 0}):
                result = MODULE._usage_preflight(
                    {"id": "user-1", "email": "agent@example.com"}, "2026-08", 1
                )
        finally:
            MODULE.SUPABASE_URL = original_url
            MODULE.SUPABASE_SERVICE_ROLE_KEY = original_key
        self.assertFalse(result["allowed"])
        self.assertEqual(result["status"], "past_due")

    def test_summary_uses_one_private_snapshot_and_never_caller_totals_or_month(self):
        response = self._Response({'billingMonth':'2026-09','used':2,'reserved':1,'limit':3})
        with patch.object(MODULE.httpx, 'post', return_value=response) as request:
            result = MODULE._usage_summary({'id':'user'}, '2099-01')
        self.assertEqual(request.call_args.kwargs['json'], {'p_user':'user'})
        self.assertTrue(request.call_args.args[0].endswith('/rpc/hof_packet_usage_summary'))
        self.assertEqual(result, response.json())
        response._payload['used'] = None
        with patch.object(MODULE.httpx, 'post', return_value=response):
            with self.assertRaises(RuntimeError): MODULE._usage_summary({'id':'user'}, '2026-09')


if __name__ == "__main__":
    unittest.main()
