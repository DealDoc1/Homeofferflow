import asyncio
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("signwell_webhook_privacy", ROOT / "api" / "signwell-webhook.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _Response:
    status_code = 201


class _Client:
    last_json = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, _url, **kwargs):
        self.__class__.last_json = kwargs["json"]
        return _Response()


class SignWellWebhookPrivacyTests(unittest.TestCase):
    def setUp(self):
        MODULE.SUPABASE_URL = "https://example.supabase.co"
        MODULE.SUPABASE_SERVICE_ROLE_KEY = "service-role"
        _Client.last_json = None

    def test_webhook_telemetry_excludes_raw_provider_payload_and_signer_data(self):
        provider_payload = {
            "event": {"type": "document_signed", "time": 123},
            "related_signer": {"name": "Sensitive Signer", "email": "sensitive@example.test"},
            "recipients": [{"name": "Other Signer", "email": "other@example.test", "status": "signed"}],
        }
        with patch.object(MODULE.httpx, "AsyncClient", _Client):
            asyncio.run(MODULE._insert_event("doc-sensitive", "document_signed", provider_payload, "Buyer Signed", "Buyer Signatures Complete"))

        payload = _Client.last_json
        self.assertIsNotNone(payload)
        self.assertEqual(payload["message"], "SignWell webhook lifecycle event recorded.")
        self.assertNotIn("signwell_document_id", payload)
        self.assertNotIn("payload", payload["metadata"])
        self.assertNotIn("related_signer", payload["metadata"])
        self.assertNotIn("sensitive@example.test", str(payload))
        self.assertNotIn("Sensitive Signer", str(payload))
        self.assertEqual(payload["metadata"]["recipient_count"], 1)

    def test_undecodable_payload_marker_is_aggregate_only(self):
        metadata = MODULE._telemetry_metadata({"_parse_error": True}, "signwell_event", "Sent for Signature", "Pending")
        self.assertEqual(metadata["payload_parse_error"], True)
        self.assertEqual(metadata["recipient_count"], 0)
