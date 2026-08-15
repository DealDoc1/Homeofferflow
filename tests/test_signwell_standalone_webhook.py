import asyncio
import hashlib
import hmac
import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("signwell_webhook", ROOT / "api" / "signwell-webhook.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _Response:
    status_code = 200


class _Client:
    requests = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def patch(self, url, headers=None, json=None):
        self.requests.append({"url": url, "headers": headers, "json": json})
        return _Response()


class StandaloneWebhookTests(unittest.TestCase):
    def setUp(self):
        _Client.requests = []
        self.env = patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_SERVICE_ROLE_KEY": "service-key"},
        )
        self.env.start()
        MODULE.SUPABASE_URL = "https://example.supabase.co"
        MODULE.SUPABASE_SERVICE_ROLE_KEY = "service-key"
        MODULE.SIGNWELL_WEBHOOK_ID = "webhook-id-for-test"

    def tearDown(self):
        self.env.stop()

    def test_signed_standalone_agreement_is_marked_signed(self):
        with patch.object(MODULE.httpx, "AsyncClient", return_value=_Client()):
            response = asyncio.run(
                MODULE._update_standalone_agreement(
                    "doc-123", "Buyer Signed", "Buyer Signatures Complete", {"event": "completed"}
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(_Client.requests), 1)
        request = _Client.requests[0]
        self.assertIn("hof_standalone_agreements?", request["url"])
        self.assertIn("signwell_document_id=eq.doc-123", request["url"])
        self.assertEqual(request["json"]["status"], "signed")
        self.assertEqual(request["json"]["signwell_status"], "Buyer Signatures Complete")
        self.assertIn("signed_at", request["json"])

    def test_declined_standalone_agreement_is_void(self):
        with patch.object(MODULE.httpx, "AsyncClient", return_value=_Client()):
            asyncio.run(
                MODULE._update_standalone_agreement(
                    "doc-456", "Rejected", "Declined/Expired", {"event": "declined"}
                )
            )
        self.assertEqual(_Client.requests[0]["json"]["status"], "void")
        self.assertNotIn("signed_at", _Client.requests[0]["json"])

    def test_pending_standalone_agreement_remains_sent(self):
        self.assertEqual(MODULE._standalone_status_for("Sent for Signature"), "sent")
        self.assertEqual(MODULE._standalone_status_for("Buyer Viewed"), "sent")

    def test_event_hash_verification_accepts_only_provider_signed_payload(self):
        payload = {"event": {"type": "document_completed", "time": 1723712400}}
        signed_value = b"document_completed@1723712400"
        payload["event"]["hash"] = hmac.new(
            MODULE.SIGNWELL_WEBHOOK_ID.encode("utf-8"), signed_value, hashlib.sha256
        ).hexdigest()
        self.assertTrue(MODULE._is_verified_event(payload))

        payload["event"]["hash"] = "not-a-provider-signature"
        self.assertFalse(MODULE._is_verified_event(payload))

    def test_event_hash_verification_fails_closed_without_webhook_id(self):
        previous = MODULE.SIGNWELL_WEBHOOK_ID
        MODULE.SIGNWELL_WEBHOOK_ID = ""
        try:
            self.assertFalse(MODULE._is_verified_event({"event": {"type": "document_signed", "time": 1, "hash": "x"}}))
        finally:
            MODULE.SIGNWELL_WEBHOOK_ID = previous
        self.assertEqual(MODULE._standalone_status_for("Partially Buyer Signed"), "sent")


if __name__ == "__main__":
    unittest.main()
