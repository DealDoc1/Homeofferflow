"""Validation and owner-scoped creation for listing workspaces."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from lib import listing_workspace_creation as creation

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("listing_workspace_creation_admin", ROOT / "api" / "admin-dashboard.py")
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)

OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BROKERAGE = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
LEAD = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
WORKSPACE = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
REQUEST = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"


def payload(**updates):
    data = {
        "action": "create_listing_workspace", "listingKind": "sale",
        "propertyAddress": "  123 Main Street, Dallas, TX  ",
        "sellerNames": [" Seller One ", "Seller Two"],
        "requestedWorkflows": ["listing_agreement", "seller_disclosure"],
        "confidentialNotes": "  Private note  ", "sellerLeadId": LEAD,
    }
    data.update(updates)
    return data


class ListingWorkspaceCreationValidationTests(unittest.TestCase):
    def test_normalizes_customer_details_and_optional_values(self):
        record = creation.validate_listing_workspace_creation(payload())
        self.assertEqual(record["property_address"], "123 Main Street, Dallas, TX")
        self.assertEqual(record["seller_names"], ["Seller One", "Seller Two"])
        self.assertEqual(record["confidential_notes"], "Private note")
        self.assertEqual(record["seller_lead_id"], LEAD)
        self.assertEqual(record["requested_workflows"], ["listing_agreement", "seller_disclosure"])
        self.assertIsNone(record["client_request_id"])

    def test_optional_create_request_id_is_canonicalized_and_validated(self):
        record = creation.validate_listing_workspace_creation(payload(clientRequestId=REQUEST.upper()))
        self.assertEqual(record["client_request_id"], REQUEST)
        with self.assertRaisesRegex(ValueError, "save attempt"):
            creation.validate_listing_workspace_creation(payload(clientRequestId="not-a-uuid"))

    def test_rejects_forged_owner_status_brokerage_and_unrecognized_fields(self):
        for key, value in (("agent_user_id", OWNER), ("brokerage_id", BROKERAGE), ("status", "active"), ("admin", True)):
            data = payload()
            data[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "only"):
                creation.validate_listing_workspace_creation(data)

    def test_rejects_invalid_kind_address_sellers_workflows_notes_and_lead_id(self):
        cases = (
            {"listingKind": "purchase"}, {"propertyAddress": "x"},
            {"sellerNames": []}, {"sellerNames": ["x" * 181]},
            {"requestedWorkflows": ["seller_disclosure", "seller_disclosure"]},
            {"requestedWorkflows": ["send_signature_request"]},
            {"confidentialNotes": "x" * 4001}, {"sellerLeadId": "not-a-uuid"},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                creation.validate_listing_workspace_creation(payload(**changes))


class ListingWorkspaceCreationAPITests(unittest.TestCase):
    def test_server_derives_owner_status_and_active_brokerage_and_returns_record(self):
        saved = {"id": WORKSPACE, "agent_user_id": OWNER, "brokerage_id": BROKERAGE,
                 "status": "intake", "listing_kind": "sale", "property_address": "123 Main Street, Dallas, TX"}
        response = SimpleNamespace(status_code=201, json=lambda: [saved])
        post_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            post = post_call

        with patch.object(API, "_get", AsyncMock(side_effect=[
                [{"id": LEAD}], [{"brokerage_id": BROKERAGE}], [{"user_id": OWNER}]])) as get, \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._create_listing_workspace({"id": OWNER}, payload()))

        self.assertEqual(result, saved)
        self.assertIn("user_id=eq." + OWNER, get.await_args_list[0].args[0])
        self.assertIn("status=eq.active", get.await_args_list[2].args[0])
        self.assertEqual(post_call.await_args.kwargs["json"]["agent_user_id"], OWNER)
        self.assertEqual(post_call.await_args.kwargs["json"]["brokerage_id"], BROKERAGE)
        self.assertEqual(post_call.await_args.kwargs["json"]["status"], "intake")
        self.assertNotIn("client_request_id", post_call.await_args.kwargs["json"])

    def test_foreign_seller_lead_is_rejected_before_insert(self):
        with patch.object(API, "_get", AsyncMock(return_value=[])) as get, \
             patch.object(API.httpx, "AsyncClient") as client:
            with self.assertRaisesRegex(PermissionError, "Refresh your seller leads"):
                asyncio.run(API._create_listing_workspace({"id": OWNER}, payload()))
        self.assertIn("user_id=eq." + OWNER, get.await_args.args[0])
        client.assert_not_called()

    def test_authenticated_route_returns_created_workspace(self):
        from io import BytesIO
        import json

        body = payload()
        raw = json.dumps(body).encode()
        handler = SimpleNamespace(path="/api/admin-dashboard", headers={
            "authorization": "Bearer session", "Content-Length": str(len(raw))
        }, rfile=BytesIO(raw))
        created = {"id": WORKSPACE, "agent_user_id": OWNER, "status": "intake"}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_create_listing_workspace", AsyncMock(return_value=created)) as create, \
             patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        create.assert_awaited_once_with({"id": OWNER}, body)
        self.assertEqual(respond.call_args.args[1], 201)
        self.assertEqual(respond.call_args.args[2], {"ok": True, "workspace": created})

    def test_no_active_brokerage_membership_creates_personal_workspace(self):
        saved = {"id": WORKSPACE, "agent_user_id": OWNER, "brokerage_id": None, "status": "intake"}
        response = SimpleNamespace(status_code=201, json=lambda: [saved])
        post_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            post = post_call

        with patch.object(API, "_get", AsyncMock(side_effect=[[{"brokerage_id": BROKERAGE}], []])), \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._create_listing_workspace({"id": OWNER}, payload(sellerLeadId=None)))
        self.assertIsNone(post_call.await_args.kwargs["json"]["brokerage_id"])
        self.assertEqual(result, saved)

    def test_conflicting_request_key_recovers_same_owner_workspace(self):
        existing = {
            "id": WORKSPACE, "agent_user_id": OWNER, "brokerage_id": None,
            "seller_lead_id": LEAD, "listing_kind": "sale",
            "property_address": "123 Main Street, Dallas, TX",
            "seller_names": ["Seller One", "Seller Two"],
            "status": "intake", "requested_workflows": ["listing_agreement", "seller_disclosure"],
            "confidential_notes": "Private note", "created_at": "2026-10-29T12:00:00Z",
            "updated_at": "2026-10-29T12:00:00Z",
        }
        response = SimpleNamespace(status_code=409)
        post_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            post = post_call

        with patch.object(API, "_get", AsyncMock(side_effect=[
                [{"id": LEAD}], [], [existing]])) as get, \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._create_listing_workspace(
                {"id": OWNER}, payload(clientRequestId=REQUEST)))

        self.assertEqual(result, existing)
        self.assertEqual(post_call.await_args.kwargs["json"]["client_request_id"], REQUEST)
        recovery_path = get.await_args_list[-1].args[0]
        self.assertIn("agent_user_id=eq." + OWNER, recovery_path)
        self.assertIn("client_request_id=eq." + REQUEST, recovery_path)

    def test_conflicting_request_key_rejects_a_different_payload(self):
        existing = {
            "id": WORKSPACE, "seller_lead_id": LEAD, "listing_kind": "sale",
            "property_address": "456 Other Street, Dallas, TX",
            "seller_names": ["Seller One", "Seller Two"],
            "requested_workflows": ["listing_agreement", "seller_disclosure"],
            "confidential_notes": "Private note",
        }
        response = SimpleNamespace(status_code=409)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            async def post(self, *args, **kwargs): return response

        with patch.object(API, "_get", AsyncMock(side_effect=[
                [{"id": LEAD}], [], [existing]])), \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            with self.assertRaisesRegex(PermissionError, "different listing details"):
                asyncio.run(API._create_listing_workspace(
                    {"id": OWNER}, payload(clientRequestId=REQUEST)))


if __name__ == "__main__":
    unittest.main()
