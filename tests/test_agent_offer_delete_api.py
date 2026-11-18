"""Authenticated soft-delete API for saved agent offers."""
import asyncio
import importlib.util
import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "agent_offer_delete_admin", ROOT / "api" / "admin-dashboard.py"
)
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OFFER = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


class AgentOfferDeleteAPITests(unittest.TestCase):
    def test_delete_is_owner_scoped_soft_delete_and_server_timestamps(self):
        response = SimpleNamespace(status_code=200, json=lambda: [{
            "id": OFFER, "status": "Deleted", "deleted_at": "now", "last_updated": "now"
        }])
        patch_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            patch = patch_call

        payload = {"action": "delete_agent_offer", "offerId": OFFER}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "_headers", return_value={"Authorization": "service-role"}), \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._delete_agent_offer({"id": OWNER}, payload))
        url = patch_call.await_args.args[0]
        self.assertIn("id=eq." + OFFER, url)
        self.assertIn("user_id=eq." + OWNER, url)
        self.assertIn("deleted_at=is.null", url)
        body = patch_call.await_args.kwargs["json"]
        self.assertEqual((body["status"], body["deleted_at"]), ("Deleted", body["last_updated"]))
        self.assertEqual(result["id"], OFFER)
        self.assertFalse(result["alreadyRemoved"])

    def test_rejects_extra_fields_before_mutation(self):
        with patch.object(API.httpx, "AsyncClient") as client:
            with self.assertRaisesRegex(ValueError, "only the offer"):
                asyncio.run(API._delete_agent_offer(
                    {"id": OWNER}, {"action": "delete_agent_offer", "offerId": OFFER, "user_id": OWNER}
                ))
        client.assert_not_called()

    def test_deleted_owned_offer_is_recovered_but_missing_or_foreign_offer_conflicts(self):
        response = SimpleNamespace(status_code=200, json=lambda: [])

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            patch = AsyncMock(return_value=response)

        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "_headers", return_value={}), \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            data = {"action": "delete_agent_offer", "offerId": OFFER}
            tombstone = {"id": OFFER, "status": "Deleted", "deleted_at": "original", "last_updated": "original"}
            with patch.object(API, "_get", AsyncMock(return_value=[tombstone])) as read:
                recovered = asyncio.run(API._delete_agent_offer({"id": OWNER}, data))
            self.assertEqual(recovered, {**tombstone, "alreadyRemoved": True})
            self.assertIn(f"id=eq.{OFFER}&user_id=eq.{OWNER}&deleted_at=not.is.null", read.await_args.args[0])
            with patch.object(API, "_get", AsyncMock(return_value=[])), self.assertRaisesRegex(PermissionError, "unavailable"):
                asyncio.run(API._delete_agent_offer({"id": OWNER}, data))

    def test_authenticated_route_returns_soft_deleted_offer(self):
        payload = {"action": "delete_agent_offer", "offerId": OFFER}
        raw = json.dumps(payload).encode()
        handler = SimpleNamespace(
            path="/api/admin-dashboard",
            headers={"authorization": "Bearer token", "Content-Length": str(len(raw))},
            rfile=BytesIO(raw),
        )
        offer = {"id": OFFER, "status": "Deleted"}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_delete_agent_offer", AsyncMock(return_value=offer)) as delete, \
             patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        delete.assert_awaited_once_with({"id": OWNER}, payload)
        self.assertEqual(respond.call_args.args[1:], (200, {"ok": True, "offer": offer}))

    def test_unauthenticated_route_does_not_delete(self):
        payload = {"action": "delete_agent_offer", "offerId": OFFER}
        raw = json.dumps(payload).encode()
        handler = SimpleNamespace(
            path="/api/admin-dashboard",
            headers={"authorization": "Bearer expired", "Content-Length": str(len(raw))},
            rfile=BytesIO(raw),
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
             patch.object(API, "_delete_agent_offer", AsyncMock()) as delete, \
             patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        delete.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)

    def test_route_reports_missing_or_foreign_offer_as_conflict(self):
        payload = {"action": "delete_agent_offer", "offerId": OFFER}
        raw = json.dumps(payload).encode()
        handler = SimpleNamespace(
            path="/api/admin-dashboard",
            headers={"authorization": "Bearer token", "Content-Length": str(len(raw))},
            rfile=BytesIO(raw),
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_delete_agent_offer", AsyncMock(side_effect=PermissionError("already removed"))), \
             patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        self.assertEqual(respond.call_args.args[1], 409)


if __name__ == "__main__":
    unittest.main()
