"""Authenticated, owner-scoped browser activity event writes."""
import asyncio
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "authenticated_offer_event_admin", ROOT / "api" / "admin-dashboard.py"
)
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "11111111-1111-4111-8111-111111111111"
OFFER = "22222222-2222-4222-8222-222222222222"
OTHER = "33333333-3333-4333-8333-333333333333"


class AuthenticatedOfferEventTests(unittest.TestCase):
    def test_event_owner_and_timestamp_are_server_derived(self):
        response = SimpleNamespace(status_code=201)
        post = AsyncMock(return_value=response)

        class Client:
            async def __aenter__(self): return self
            async def __aexit__(self, *_): return False
        Client.post = post

        body = {"action": "record_offer_event", "offerId": OFFER,
                "eventType": "resume_clicked", "status": " Draft ",
                "message": " Resumed offer ", "metadata": {"surface": "dashboard"}}
        with patch.object(API, "_get", AsyncMock(return_value=[{"id": OFFER}])) as get, \
                patch.object(API, "SUPABASE_URL", "https://db.example"), \
                patch.object(API, "_headers", return_value={"apikey": "service"}), \
                patch.object(API.httpx, "AsyncClient", return_value=Client()):
            result = asyncio.run(API._record_user_offer_event({"id": OWNER}, body))
        self.assertEqual(result, {"recorded": True})
        self.assertIn(f"user_id=eq.{OWNER}", get.await_args.args[0])
        payload = post.await_args.kwargs["json"]
        self.assertEqual(payload["user_id"], OWNER)
        self.assertEqual(payload["offer_id"], OFFER)
        self.assertEqual(payload["event_type"], "resume_clicked")
        self.assertEqual(payload["status"], "Draft")
        self.assertEqual(payload["message"], "Resumed offer")
        self.assertNotIn("user_id", body)
        self.assertNotIn("created_at", body)

    def test_rejects_foreign_offer_and_invalid_or_oversized_event_data(self):
        body = {"action": "record_offer_event", "offerId": OFFER,
                "eventType": "resume_clicked", "status": None,
                "message": None, "metadata": {}}
        with patch.object(API, "_get", AsyncMock(return_value=[])), \
                patch.object(API.httpx, "AsyncClient") as client:
            with self.assertRaisesRegex(PermissionError, "unavailable"):
                asyncio.run(API._record_user_offer_event({"id": OWNER}, body))
        client.assert_not_called()

        invalid = [
            {**body, "offerId": None, "eventType": "Bad Event"},
            {**body, "offerId": None, "status": "x" * 81},
            {**body, "offerId": None, "message": "x" * 241},
            {**body, "offerId": None, "metadata": {"oversized": "x" * 4096}},
            {**body, "offerId": None, "metadata": {"not_json": object()}},
            {**body, "offerId": None, "user_id": OTHER},
        ]
        for data in invalid:
            with self.subTest(data=list(data)):
                with self.assertRaises(ValueError):
                    asyncio.run(API._record_user_offer_event({"id": OWNER}, data))

    def test_post_route_requires_verified_user_and_returns_event_result(self):
        body = {"action": "record_offer_event", "offerId": None,
                "eventType": "billing_portal_opened", "status": None,
                "message": None, "metadata": {}}
        raw = json.dumps(body).encode()
        handler = SimpleNamespace(
            path="/api/admin-dashboard",
            headers={"authorization": "Bearer token", "Content-Length": str(len(raw))},
            rfile=io.BytesIO(raw),
        )
        with patch.object(API, "SUPABASE_URL", "https://db.example"), \
                patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
                patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
                patch.object(API, "_record_user_offer_event", AsyncMock(return_value={"recorded": True})) as record, \
                patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        record.assert_awaited_once_with({"id": OWNER}, body)
        self.assertEqual(respond.call_args.args[1:], (200, {"ok": True, "event": {"recorded": True}}))

        handler.rfile = io.BytesIO(raw)
        with patch.object(API, "SUPABASE_URL", "https://db.example"), \
                patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
                patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
                patch.object(API, "_record_user_offer_event", AsyncMock()) as record, \
                patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        record.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)

    def test_browser_event_helper_uses_authenticated_api_not_direct_table_write(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        start = source.index("async function logOfferEvent(")
        end = source.index("async function recordCurrentLegalAcceptance", start)
        helper = source[start:end]
        self.assertIn("action: 'record_offer_event'", helper)
        self.assertIn("Authorization: `Bearer ${accessToken}`", helper)
        self.assertIn("keepalive: true", helper)
        self.assertNotIn("from('hof_offer_events')", helper)


if __name__ == "__main__":
    unittest.main()
