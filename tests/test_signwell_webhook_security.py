import hashlib
import hmac
import importlib.util
import io
import json
import asyncio
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
WEBHOOK_PATH = ROOT / "api" / "signwell-webhook.py"


def load_module():
    spec = importlib.util.spec_from_file_location("signwell_webhook_security", WEBHOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


webhook = load_module()


def signed_event(event_type="document_completed", event_time=1_785_325_200, webhook_id="hook_test"):
    signature = hmac.new(
        webhook_id.encode("utf-8"),
        f"{event_type}@{event_time}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "event": {"type": event_type, "time": event_time, "hash": signature},
        "data": {"object": {"id": "a692e1ce-9929-4541-adc7-61932bab39d3", "recipients": []}},
    }


class SignWellWebhookSecurityTests(unittest.TestCase):
    def setUp(self):
        webhook.SIGNWELL_WEBHOOK_ID = "hook_test"
        self.now = 1_785_325_200

    def test_official_event_shape_maps_type_and_document_id(self):
        payload = signed_event()
        self.assertEqual(webhook._event_type(payload), "document_completed")
        self.assertEqual(webhook._document_id(payload), "a692e1ce-9929-4541-adc7-61932bab39d3")

    def test_valid_current_event_hmac_is_accepted(self):
        self.assertTrue(webhook._verify_event(signed_event(), now=self.now))

    def test_tampered_or_stale_event_is_rejected(self):
        tampered = signed_event()
        tampered["event"]["type"] = "document_completed_but_tampered"
        self.assertFalse(webhook._verify_event(tampered, now=self.now))
        self.assertFalse(webhook._verify_event(signed_event(), now=self.now + 301))

    def test_unverified_event_never_reaches_offer_updates(self):
        payload = signed_event()
        payload["event"]["hash"] = "0" * 64
        raw = json.dumps(payload).encode("utf-8")
        request = webhook.handler.__new__(webhook.handler)
        request.headers = {"content-length": str(len(raw))}
        request.rfile = io.BytesIO(raw)
        captured = {}
        request.send_response = lambda code: captured.update(code=code)
        request.send_header = lambda *_args: None
        request.end_headers = lambda: None
        request.wfile = io.BytesIO()

        request.do_POST()

        self.assertEqual(captured["code"], 401)

    def test_verified_official_event_reaches_the_document_update_path(self):
        payload = signed_event()
        raw = json.dumps(payload).encode("utf-8")
        request = webhook.handler.__new__(webhook.handler)
        request.headers = {"content-length": str(len(raw))}
        request.rfile = io.BytesIO(raw)
        captured = {}
        request.send_response = lambda code: captured.update(code=code)
        request.send_header = lambda *_args: None
        request.end_headers = lambda: None
        request.wfile = io.BytesIO()

        async def found_offer(document_id):
            captured.update(lookup_document_id=document_id)
            return {"id": "offer-123", "user_id": "user-123"}

        async def inserted(document_id, event_type, *args):
            captured.update(
                insert_document_id=document_id,
                insert_event_type=event_type,
                event_offer=args[-1],
            )
            return type("Response", (), {"status_code": 201})()

        async def updated(document_id, *_args):
            captured.update(update_document_id=document_id)
            return type("Response", (), {"status_code": 200})()

        with patch.object(webhook.time, "time", return_value=self.now), patch.object(
            webhook, "_offer_for_document", found_offer
        ), patch.object(webhook, "_insert_event", inserted
        ), patch.object(webhook, "_update_offer", updated):
            request.do_POST()

        self.assertEqual(captured["code"], 200)
        self.assertEqual(captured["insert_event_type"], "document_completed")
        self.assertEqual(captured["insert_document_id"], "a692e1ce-9929-4541-adc7-61932bab39d3")
        self.assertEqual(captured["lookup_document_id"], "a692e1ce-9929-4541-adc7-61932bab39d3")
        self.assertEqual(captured["event_offer"], {"id": "offer-123", "user_id": "user-123"})
        self.assertEqual(captured["update_document_id"], "a692e1ce-9929-4541-adc7-61932bab39d3")

    def test_verified_event_is_persisted_with_its_offer_and_owner(self):
        captured = {}

        class Response:
            status_code = 201

        class Client:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def post(self, url, **kwargs):
                captured.update(url=url, payload=kwargs["json"])
                return Response()

        with patch.object(webhook.httpx, "AsyncClient", Client):
            asyncio.run(
                webhook._insert_event(
                    "doc-123",
                    "document_completed",
                    {"event": {"type": "document_completed"}},
                    "Buyer Signed",
                    "Buyer Signatures Complete",
                    {"id": "offer-123", "user_id": "user-123"},
                )
            )

        self.assertTrue(captured["url"].endswith("/rest/v1/hof_offer_events"))
        self.assertEqual(captured["payload"]["offer_id"], "offer-123")
        self.assertEqual(captured["payload"]["user_id"], "user-123")


if __name__ == "__main__":
    unittest.main()
