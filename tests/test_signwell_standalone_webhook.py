import asyncio
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
        self.assertEqual(MODULE._standalone_status_for("Partially Buyer Signed"), "sent")


if __name__ == "__main__":
    unittest.main()
