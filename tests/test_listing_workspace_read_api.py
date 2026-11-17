"""Authenticated owner-scoped listing workspace reads."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("listing_workspace_read_admin", ROOT / "api" / "admin-dashboard.py")
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class ListingWorkspaceReadAPITests(unittest.TestCase):
    def test_agent_workspace_read_is_owner_scoped_bounded_and_minimal(self):
        rows = [{"id": "workspace-id", "listing_kind": "sale", "property_address": "123 Main Street",
                 "seller_names": ["Seller"], "status": "intake", "requested_workflows": [],
                 "updated_at": "2026-10-29T10:00:00+00:00"}]
        with patch.object(API, "_get", AsyncMock(return_value=rows)) as get:
            result = asyncio.run(API._agent_listing_workspaces({"id": OWNER}))
        self.assertEqual(result, rows)
        query = get.await_args.args[0]
        self.assertIn("agent_user_id=eq." + OWNER, query)
        self.assertIn("limit=20", query)
        self.assertIn("order=updated_at.desc", query)
        self.assertNotIn("confidential_notes", query)
        self.assertNotIn("brokerage_id", query)

    def test_specific_workspace_read_keeps_owner_scope_and_caps_client_limit(self):
        workspace_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        with patch.object(API, "_get", AsyncMock(return_value=[])) as get:
            asyncio.run(API._agent_listing_workspaces(
                {"id": OWNER}, workspace_id=workspace_id, limit=500
            ))
        query = get.await_args.args[0]
        self.assertIn("agent_user_id=eq." + OWNER, query)
        self.assertIn("id=eq." + workspace_id, query)
        self.assertIn("limit=50", query)

    def test_authenticated_route_returns_listing_workspaces(self):
        handler = SimpleNamespace(path="/api/admin-dashboard?scope=agent_listing_workspaces&agent_user_id=someone-else",
                                  headers={"authorization": "Bearer token"})
        rows = [{"id": "workspace-id", "property_address": "123 Main Street"}]
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_get", AsyncMock(return_value=rows)) as get, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        self.assertIn("agent_user_id=eq." + OWNER, get.await_args.args[0])
        self.assertNotIn("someone-else", get.await_args.args[0])
        self.assertEqual(respond.call_args.args[1], 200)
        self.assertEqual(respond.call_args.args[2], {"workspaces": rows})

    def test_invalid_workspace_id_does_not_reach_storage(self):
        with patch.object(API, "_get", AsyncMock()) as get:
            with self.assertRaisesRegex(ValueError, "Choose a valid listing workspace"):
                asyncio.run(API._agent_listing_workspaces({"id": OWNER}, workspace_id="invalid"))
        get.assert_not_awaited()

    def test_storage_failure_returns_recoverable_error(self):
        handler = SimpleNamespace(path="/api/admin-dashboard?scope=agent_listing_workspaces",
                                  headers={"authorization": "Bearer token"})
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_get", AsyncMock(side_effect=RuntimeError("Internal query details"))), \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        self.assertEqual(respond.call_args.args[1], 503)
        self.assertNotIn("Internal query details", respond.call_args.args[2]["error"])

    def test_unauthenticated_route_does_not_read_workspaces(self):
        handler = SimpleNamespace(path="/api/admin-dashboard?scope=agent_listing_workspaces",
                                  headers={"authorization": "Bearer expired"})
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
             patch.object(API, "_get", AsyncMock()) as get, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        get.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)


if __name__ == "__main__":
    unittest.main()
