"""Owner-scoped API contract and validation for listing offer comparisons."""
import asyncio
import importlib.util
import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from lib import listing_workspace_offer_comparison as offers

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("offer_comparison_admin", ROOT / "api" / "admin-dashboard.py")
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)


class OfferComparisonValidationTests(unittest.TestCase):
    def payload(self):
        return {
            "offerLabel": " Offer A ", "offerPrice": "550000.00", "financingType": "Conventional",
            "sellerConcessions": "2500", "closingDate": "2026-11-20", "optionDays": "7",
            "contingencyNotes": "Inspection", "status": "received", "privateNotes": "Call agent",
        }

    def test_normalizes_bounded_fields_and_money(self):
        record = offers.validate_offer_fields(self.payload())
        self.assertEqual(record["offer_label"], "Offer A")
        self.assertEqual(record["offer_price"], "550000.00")
        self.assertEqual(record["seller_concessions"], "2500.00")
        self.assertEqual(record["option_days"], 7)

    def test_rejects_invalid_or_client_authored_values(self):
        for key, value in (("offerPrice", "-1"), ("sellerConcessions", "1.001"),
                           ("closingDate", "2026-02-30"), ("optionDays", "366"),
                           ("status", "accepted"), ("privateNotes", "x" * 4001)):
            data = self.payload()
            data[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                offers.validate_offer_fields(data)
        data = self.payload()
        data["agent_user_id"] = "forged-owner"
        with self.assertRaises(ValueError):
            offers.validate_offer_fields(data)


class OfferComparisonAPITests(unittest.TestCase):
    workspace_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    offer_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    timestamp = "2026-10-29T10:00:00+00:00"

    def test_save_is_owner_scoped_and_server_assigns_owner(self):
        body = OfferComparisonValidationTests().payload()
        body.update(action="save_listing_workspace_offer_comparison", workspaceId=self.workspace_id)
        response = SimpleNamespace(status_code=201, json=lambda: [{"id": self.offer_id}])

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            async def post(self, *args, **kwargs): return response

        with patch.object(API, "_get", AsyncMock(return_value=[{"id": self.workspace_id}])) as get, \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._save_listing_workspace_offer_comparison({"id": "user-1"}, body))
        self.assertIn("agent_user_id=eq.user-1", get.await_args.args[0])
        self.assertEqual(result["id"], self.offer_id)

    def test_status_update_uses_owner_scope_and_compare_and_swap(self):
        body = {"action": "update_listing_workspace_offer_status", "offerId": self.offer_id,
                "workspaceId": self.workspace_id, "status": "preferred", "expectedUpdatedAt": self.timestamp}
        response = SimpleNamespace(status_code=200, json=lambda: [{"id": self.offer_id, "status": "preferred"}])
        patch_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            patch = patch_call

        with patch.object(API, "_get", AsyncMock(side_effect=[[{"id": self.workspace_id}],
                [{"id": self.offer_id, "updated_at": self.timestamp}]])) as get, \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            asyncio.run(API._update_listing_workspace_offer_status({"id": "user-1"}, body))
        url = patch_call.await_args.args[0]
        self.assertIn("agent_user_id=eq.user-1", url)
        self.assertIn("updated_at=eq.", url)
        self.assertEqual(get.await_count, 2)

    def test_stale_status_update_does_not_write(self):
        body = {"action": "update_listing_workspace_offer_status", "offerId": self.offer_id,
                "workspaceId": self.workspace_id, "status": "preferred", "expectedUpdatedAt": self.timestamp}
        with patch.object(API, "_get", AsyncMock(side_effect=[[{"id": self.workspace_id}],
                [{"id": self.offer_id, "updated_at": "2026-10-29T10:01:00+00:00"}]])), \
             patch.object(API.httpx, "AsyncClient") as client:
            with self.assertRaisesRegex(PermissionError, "changed in another session"):
                asyncio.run(API._update_listing_workspace_offer_status({"id": "user-1"}, body))
        client.assert_not_called()

    def test_delete_uses_workspace_and_owner_scope(self):
        body = {"action": "delete_listing_workspace_offer_comparison", "offerId": self.offer_id,
                "workspaceId": self.workspace_id, "expectedUpdatedAt": self.timestamp}
        response = SimpleNamespace(status_code=204, json=lambda: [{"id": self.offer_id}])
        delete_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            delete = delete_call

        with patch.object(API, "_get", AsyncMock(return_value=[{"id": self.workspace_id}])), \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._delete_listing_workspace_offer_comparison({"id": "user-1"}, body))
        url = delete_call.await_args.args[0]
        self.assertIn("agent_user_id=eq.user-1", url)
        self.assertIn(f"workspace_id=eq.{self.workspace_id}", url)
        self.assertIn("updated_at=eq.2026-10-29T10%3A00%3A00%2B00%3A00", url)
        self.assertTrue(result["removed"])

    def test_a_stale_removal_changes_no_rows(self):
        body = {"action": "delete_listing_workspace_offer_comparison", "offerId": self.offer_id,
                "workspaceId": self.workspace_id, "expectedUpdatedAt": self.timestamp}
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.delete.return_value = SimpleNamespace(status_code=200, json=lambda: [])
        with patch.object(API, "_get", AsyncMock(return_value=[{"id": self.workspace_id}])), \
             patch.object(API.httpx, "AsyncClient", return_value=client):
            with self.assertRaisesRegex(PermissionError, "Refresh the workspace"):
                asyncio.run(API._delete_listing_workspace_offer_comparison({"id": "user-1"}, body))
        client.delete.assert_awaited_once()

    def test_read_is_owner_scoped_and_returns_the_existing_smallest_list_projection(self):
        rows = [{"id": self.offer_id, "workspace_id": self.workspace_id,
                 "offer_label": "Offer A", "private_notes": "Seller notes"}]
        with patch.object(API, "_get", AsyncMock(side_effect=[
            [{"id": self.workspace_id}], rows
        ])) as get:
            result = asyncio.run(API._agent_listing_workspace_offer_comparisons(
                {"id": "user-1"}, self.workspace_id
            ))
        self.assertEqual(result, rows)
        self.assertIn("agent_user_id=eq.user-1", get.await_args_list[0].args[0])
        query = get.await_args_list[1].args[0]
        self.assertIn(f"workspace_id=eq.{self.workspace_id}", query)
        self.assertIn("agent_user_id=eq.user-1", query)
        self.assertIn("order=updated_at.desc&limit=20", query)
        self.assertIn("private_notes", query)

    def test_read_rejects_a_workspace_not_owned_by_the_agent(self):
        with patch.object(API, "_get", AsyncMock(return_value=[])) as get:
            with self.assertRaisesRegex(PermissionError, "workspace is unavailable"):
                asyncio.run(API._agent_listing_workspace_offer_comparisons(
                    {"id": "user-1"}, self.workspace_id
                ))
        self.assertEqual(get.await_count, 1)

    def test_read_route_requires_sign_in_and_returns_comparison_rows(self):
        handler = SimpleNamespace(
            path=f"/api/admin-dashboard?scope=agent_listing_workspace_offers&workspace_id={self.workspace_id}",
            headers={"authorization": "Bearer token"},
        )
        rows = [{"id": self.offer_id, "workspace_id": self.workspace_id}]
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": "user-1"})), \
             patch.object(API, "_agent_listing_workspace_offer_comparisons", AsyncMock(return_value=rows)) as load, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        self.assertEqual(load.await_args.args, ({"id": "user-1"}, self.workspace_id))
        self.assertEqual(respond.call_args.args[1:], (200, {"offers": rows}))

    def test_route_requires_sign_in_and_rejects_extra_fields(self):
        def request(payload, user):
            raw = json.dumps(payload).encode()
            handler = SimpleNamespace(path="/api/admin-dashboard", headers={
                "authorization": "Bearer token", "Content-Length": str(len(raw))}, rfile=BytesIO(raw))
            with patch.object(API, "SUPABASE_URL", "https://private.example"), \
                 patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "secret"), \
                 patch.object(API, "_verified_user", AsyncMock(return_value=user)), \
                 patch.object(API, "_json") as respond:
                API.handler.do_POST(handler)
                return respond.call_args.args[1:]
        payload = {"action": "save_listing_workspace_offer_comparison", "workspaceId": self.workspace_id,
                   **OfferComparisonValidationTests().payload(), "agent_user_id": "forged"}
        self.assertEqual(request(payload, None)[0], 401)
        code, body = request(payload, {"id": "user-1"})
        self.assertEqual(code, 400)
        self.assertIn("only", body["error"])


if __name__ == "__main__":
    unittest.main()
