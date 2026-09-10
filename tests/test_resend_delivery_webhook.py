import base64
import hashlib
import hmac
import importlib.util
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("resend_delivery_webhook", ROOT / "api" / "fsbo-lead.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
MIGRATION = (ROOT / "supabase" / "migrations" / "20260910104500_resend_delivery_event_ledger.sql").read_text(encoding="utf-8")


class _Response:
    def __init__(self, status_code=201, payload=None, text='[]'):
        self.status_code = status_code
        self._payload = payload if payload is not None else [{"svix_id": "msg_1"}]
        self.text = text

    def json(self):
        return self._payload


class _Client:
    last_request = None
    response = _Response()

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, **kwargs):
        self.__class__.last_request = (url, kwargs)
        return self.__class__.response


class ResendDeliveryWebhookTests(unittest.TestCase):
    def setUp(self):
        MODULE.SUPABASE_URL = "https://example.supabase.co"
        MODULE.SUPABASE_SERVICE_ROLE_KEY = "service-role"
        MODULE.RESEND_WEBHOOK_SECRET = "whsec_c2lnbmluZy1rZXk"
        _Client.last_request = None
        _Client.response = _Response()

    def _signature(self, body, message_id="msg_1", timestamp="1700000000"):
        key = b"signing-key"
        digest = hmac.new(key, f"{message_id}.{timestamp}.".encode() + body, hashlib.sha256).digest()
        return "v1," + base64.b64encode(digest).decode()

    def test_verifies_raw_svix_signature_and_rejects_tampering(self):
        body = b'{"type":"email.delivered","data":{"email_id":"email_1"}}'
        timestamp = str(int(time.time()))
        signature = self._signature(body, timestamp=timestamp)
        self.assertTrue(MODULE._verify_resend_svix_signature(body, "msg_1", timestamp, signature, MODULE.RESEND_WEBHOOK_SECRET))
        self.assertFalse(MODULE._verify_resend_svix_signature(body + b" ", "msg_1", timestamp, signature, MODULE.RESEND_WEBHOOK_SECRET))
        self.assertFalse(MODULE._verify_resend_svix_signature(body, "msg_1", "1", signature, MODULE.RESEND_WEBHOOK_SECRET, now=1700000000))

    def test_event_row_keeps_only_safe_operational_fields(self):
        event = {
            "type": "email.bounced",
            "created_at": "2026-09-10T12:00:00Z",
            "data": {
                "email_id": "email_1",
                "to": ["private@example.test"],
                "subject": "Private property details",
                "tags": {"email_type": "seller_plan_receipt", "seller_package": "free_intake", "customer_email": "private@example.test"},
            },
        }
        row = MODULE._resend_event_row(event, "msg_1")
        self.assertEqual(row["delivery_status"], "bounced")
        self.assertEqual(row["tags"], {"email_type": "seller_plan_receipt", "seller_package": "free_intake"})
        self.assertNotIn("private@example.test", json.dumps(row))
        self.assertNotIn("subject", row)

    def test_unknown_events_are_safely_recorded_as_ignored(self):
        row = MODULE._resend_event_row({"type": "email.received", "data": {}}, "msg_1")
        self.assertEqual(row["event_type"], "other")
        self.assertEqual(row["delivery_status"], "other")
        self.assertEqual(row["processing_state"], "ignored")

    def test_claim_uses_conflict_ignore_for_at_least_once_delivery(self):
        row = MODULE._resend_event_row({"type": "email.delivered", "data": {}}, "msg_1")
        with patch.object(MODULE.httpx, "Client", _Client):
            self.assertTrue(MODULE._claim_resend_webhook_event(row))
        url, kwargs = _Client.last_request
        self.assertIn("on_conflict=svix_id", url)
        self.assertIn("resolution=ignore-duplicates", kwargs["headers"]["Prefer"])
        self.assertNotIn("raw_body", kwargs["json"])

    def test_migration_is_server_only_and_has_idempotency_index(self):
        self.assertIn("hof_resend_webhook_events", MIGRATION)
        self.assertIn("svix_id text not null unique", MIGRATION)
        self.assertIn("enable row level security", MIGRATION)
        self.assertIn("revoke all on table public.hof_resend_webhook_events from anon, authenticated", MIGRATION)
        self.assertIn("grant all on table public.hof_resend_webhook_events to service_role", MIGRATION)
        self.assertIn("using (false)", MIGRATION)

    def test_public_webhook_path_reuses_existing_function_and_is_not_a_cached_page(self):
        config = (ROOT / "vercel.json").read_text(encoding="utf-8")
        self.assertIn('"source": "/api/resend-webhook"', config)
        self.assertIn('"destination": "/api/fsbo-lead?resend_webhook=1"', config)
        self.assertNotIn('"api/resend-webhook.py"', config)


if __name__ == "__main__":
    unittest.main()
