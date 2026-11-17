"""Authenticated compare-and-swap saves for listing workspace status."""
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

SPEC = importlib.util.spec_from_file_location(
    "listing_workspace_status_admin", Path(__file__).resolve().parents[1] / "api/admin-dashboard.py"
)
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
WORKSPACE = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
REQUEST = {
    "action": "update_listing_workspace_status",
    "workspaceId": WORKSPACE,
    "status": "ready_for_review",
    "expectedUpdatedAt": "2026-11-16T18:00:00.123456Z",
}
SAVED = {"id": WORKSPACE, "status": REQUEST["status"], "updated_at": "2026-11-17T12:00:00.234567+00:00"}


class ListingWorkspaceStatusTests(unittest.TestCase):
    def exercise(self, rows, *, body=REQUEST, user=None, signed_in=True):
        encoded = json.dumps(body).encode()
        request = SimpleNamespace(
            path="/api/admin-dashboard",
            headers={"authorization": "Bearer fixture", "Content-Length": str(len(encoded))},
            rfile=io.BytesIO(encoded),
        )
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.patch.return_value = SimpleNamespace(status_code=200, json=lambda: rows)
        with patch.object(API, "SUPABASE_URL", "https://storage.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "fictional-service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=(user or {"id": OWNER}) if signed_in else None)), \
             patch.object(API.httpx, "AsyncClient", return_value=client), \
             patch.object(API, "_json") as respond:
            API.handler.do_POST(request)
        return respond.call_args.args[1:], client.patch

    def test_verified_owner_and_timestamp_are_atomic_filters(self):
        result, storage = self.exercise([SAVED])
        self.assertEqual(result, (200, {"ok": True, "workspace": SAVED}))
        storage.assert_awaited_once()
        url = urlsplit(storage.await_args.args[0])
        self.assertEqual(url.path, "/rest/v1/hof_listing_workspaces")
        self.assertEqual(parse_qs(url.query), {
            "agent_user_id": ["eq." + OWNER],
            "id": ["eq." + WORKSPACE],
            "updated_at": ["eq.2026-11-16T18:00:00.123456+00:00"],
            "select": ["id,status,updated_at"],
        })
        self.assertEqual(storage.await_args.kwargs["json"], {"status": "ready_for_review"})

    def test_a_stale_or_unowned_row_cannot_be_overwritten(self):
        (status, result), storage = self.exercise([])
        self.assertEqual(status, 409)
        self.assertIn("Refresh Workspaces", result["error"])
        storage.assert_awaited_once()

    def test_invalid_input_does_not_reach_storage(self):
        for changes in ({"status": []}, {"status": "sent"}, {"expectedUpdatedAt": "2026-11-16"},
                        {"expectedUpdatedAt": None}, {"workspaceId": "invalid"}, {"agent_user_id": OWNER}):
            with self.subTest(changes=changes):
                (status, _), storage = self.exercise([], body={**REQUEST, **changes})
                self.assertEqual(status, 400)
                storage.assert_not_awaited()

    def test_a_signed_out_request_does_not_reach_storage(self):
        (status, _), storage = self.exercise([], signed_in=False)
        self.assertEqual(status, 401)
        storage.assert_not_awaited()

    def test_an_unconfirmed_result_returns_recovery_instead_of_success(self):
        for rows in (None, [{}], [{**SAVED, "id": OWNER}], [{**SAVED, "status": "draft"}]):
            with self.subTest(rows=rows):
                (status, result), _ = self.exercise(rows)
                self.assertEqual(status, 503)
                self.assertIn("Refresh Workspaces", result["error"])
