"""The authenticated timeline API owns validation and writes protected offers."""
import asyncio
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from lib import agent_contract_timeline as timeline

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("timeline_admin", ROOT / "api" / "admin-dashboard.py")
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)


class TimelineValidationTests(unittest.TestCase):
    def test_server_derives_option_date_and_normalizes_confirmed_milestones(self):
        result = timeline.build_tracking({
            "effectiveDate": "2026-02-28", "closingDate": "2026-03-31",
            "milestones": [{"label": "Survey delivery", "date": "2026-03-10"}],
        }, 7, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(result["optionDeadline"], "2026-03-07")
        self.assertEqual(result["milestones"], [{"label": "Survey delivery", "date": "2026-03-10"}])
        self.assertEqual(result["updatedAt"], "2026-01-01T00:00:00+00:00")

    def test_dates_and_milestones_are_bounded_and_calendar_valid(self):
        for payload in (
            {"effectiveDate": "2026-02-29", "milestones": []},
            {"effectiveDate": "2026-01-01", "milestones": [{"label": "x", "date": "2026-01-02"}]},
            {"effectiveDate": "2026-01-01", "milestones": [{"label": "Okay", "date": "2026-02-30"}]},
            {"effectiveDate": "2026-01-01", "milestones": [{"label": "Okay", "date": "2026-01-02", "extra": True}]},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                timeline.build_tracking(payload, 7)
        with self.assertRaisesRegex(ValueError, "12"):
            timeline.normalize_milestones([{"label": "Date", "date": "2026-01-01"}] * 13)

    def test_duplicate_confirmed_milestones_are_rejected_for_saving(self):
        duplicates = [
            {"label": "Survey delivery", "date": "2026-02-01"},
            {"label": "  SURVEY   DELIVERY ", "date": "2026-02-01"},
        ]
        with self.assertRaisesRegex(ValueError, "Enter each confirmed date once"):
            timeline.build_tracking({"effectiveDate": "2026-01-01", "milestones": duplicates}, 0)

        changed_by_amendment = [
            {"label": "Survey delivery", "date": "2026-02-01"},
            {"label": "Survey delivery - amended", "date": "2026-02-03"},
        ]
        self.assertEqual(len(timeline.build_tracking({"effectiveDate": "2026-01-01", "milestones": changed_by_amendment}, 0)["milestones"]), 2)

    def test_legacy_duplicate_milestones_remain_readable(self):
        milestones = [{"label": "Survey delivery", "date": "2026-02-01"}] * 2
        self.assertEqual(timeline.normalize_milestones(milestones), milestones)


class TimelineAPITests(unittest.TestCase):
    offer_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    old_time = "2026-10-29T10:00:00+00:00"

    def call_save(self, row, expected=None):
        payload = {
            "action": "save_agent_contract_timeline", "offerId": self.offer_id,
            "effectiveDate": "2026-10-20", "closingDate": "2026-11-20",
            "milestones": [{"label": "Survey delivery", "date": "2026-11-01"}],
            "expectedUpdatedAt": expected,
        }
        return asyncio.run(API._save_agent_contract_timeline({"id": "user-1"}, payload))

    def test_owner_scoped_compare_and_swap_submits_only_timeline_data(self):
        row = {"id": self.offer_id, "status": "Signed", "option_days": 7,
               "signwell_document_id": "provider-doc", "offer_data": {
                   "optionDays": 7, "packetKey": "preserved",
                   "transactionTracking": {"updatedAt": self.old_time, "oldKey": "replaced"}}}
        async def persist(url, **kwargs):
            return SimpleNamespace(status_code=200, json=lambda: kwargs["json"]["p_tracking"])

        post_call = AsyncMock(side_effect=persist)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            post = post_call

        with patch.object(API, "_get", AsyncMock(return_value=[row])) as get, \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = self.call_save(row, self.old_time)
        self.assertIn("user_id=eq.user-1", get.await_args.args[0])
        self.assertIn("deleted_at=is.null", get.await_args.args[0])
        self.assertTrue(post_call.await_args.args[0].endswith("/rpc/hof_save_agent_contract_timeline"))
        body = post_call.await_args.kwargs["json"]
        self.assertEqual(body, {
            "p_offer_id": self.offer_id, "p_owner_id": "user-1",
            "p_expected_status": "Signed", "p_expected_updated_at": self.old_time,
            "p_expected_option_days": 7, "p_tracking": result["tracking"],
        })
        self.assertEqual(result["tracking"]["optionDeadline"], "2026-10-27")
        self.assertEqual(result["tracking"]["milestones"][0]["label"], "Survey delivery")

    def test_database_conflict_and_unconfirmed_write_are_distinguished(self):
        row = {"status": "Accepted", "offer_data": {"optionDays": None}, "option_days": 7}
        client = AsyncMock()
        client.__aenter__.return_value = client
        for payload, error in ((None, PermissionError), ({"effectiveDate": "1999-01-01"}, RuntimeError)):
            client.post.return_value = SimpleNamespace(status_code=200, json=lambda: payload)
            with self.subTest(payload=payload), patch.object(API, "_get", AsyncMock(return_value=[row])), \
                 patch.object(API.httpx, "AsyncClient", return_value=client), self.assertRaises(error):
                self.call_save(row)
            self.assertIsNone(client.post.await_args.kwargs["json"]["p_expected_option_days"])

    def test_stale_timeline_is_conflict_and_does_not_write(self):
        row = {"status": "Accepted", "option_days": 0, "offer_data": {
            "transactionTracking": {"updatedAt": self.old_time}}}
        with patch.object(API, "_get", AsyncMock(return_value=[row])), \
             patch.object(API.httpx, "AsyncClient") as client:
            with self.assertRaisesRegex(PermissionError, "changed in another session"):
                self.call_save(row, "2026-10-28T00:00:00+00:00")
        client.assert_not_called()

    def test_unowned_offer_is_not_disclosed_or_modified(self):
        with patch.object(API, "_get", AsyncMock(return_value=[])), \
             patch.object(API.httpx, "AsyncClient") as client:
            with self.assertRaisesRegex(PermissionError, "unavailable"):
                self.call_save({}, None)
        client.assert_not_called()

    def test_api_route_requires_session_and_rejects_client_authored_fields(self):
        def request(payload, user):
            import json
            from io import BytesIO
            raw = json.dumps(payload).encode()
            handler = SimpleNamespace(path="/api/admin-dashboard", headers={
                "authorization": "Bearer token", "Content-Length": str(len(raw))}, rfile=BytesIO(raw))
            with patch.object(API, "SUPABASE_URL", "https://private.example"), \
                 patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "secret"), \
                 patch.object(API, "_verified_user", AsyncMock(return_value=user)), \
                 patch.object(API, "_json") as respond:
                API.handler.do_POST(handler)
                return respond.call_args.args[1:]
        payload = {"action": "save_agent_contract_timeline", "offerId": self.offer_id,
                   "effectiveDate": "2026-10-20", "closingDate": "", "milestones": [],
                   "expectedUpdatedAt": None, "offer_data": {"forged": True}}
        self.assertEqual(request(payload, None)[0], 401)
        code, body = request(payload, {"id": "user-1"})
        self.assertEqual(code, 400)
        self.assertIn("only", body["error"])


if __name__ == "__main__":
    unittest.main()
