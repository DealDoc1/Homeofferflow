"""Owner-scoped, minimal offer activity timeline API."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "agent_offer_activity_timeline_admin", ROOT / "api" / "admin-dashboard.py"
)
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OFFER = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


class AgentOfferActivityTimelineAPITests(unittest.TestCase):
    def test_timeline_checks_offer_owner_and_projects_only_display_fields(self):
        event = {
            "id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "event_type": "signwell_status_refresh",
            "status": "awaiting_signature",
            "message": "top-level internal message is not returned",
            "created_at": "2026-10-29T10:00:00+00:00",
            "metadata": {
                "signwell_status": "awaiting signature",
                "message": "Buyer signing is pending.",
                "signwell_document_id": "doc_123",
                "recipient_statuses": [{"email": "buyer@example.test"}],
                "refreshed_by": "agent@example.test",
            },
        }
        with patch.object(API, "_get", AsyncMock(side_effect=[
            [{"id": OFFER}], [event]
        ])) as get:
            result = asyncio.run(API._agent_offer_activity_timeline({"id": OWNER}, OFFER))
        offer_query, event_query = [call.args[0] for call in get.await_args_list]
        self.assertIn("id=eq." + OFFER, offer_query)
        self.assertIn("user_id=eq." + OWNER, offer_query)
        self.assertIn("deleted_at=is.null", offer_query)
        self.assertIn("offer_id=eq." + OFFER, event_query)
        self.assertIn("user_id=eq." + OWNER, event_query)
        self.assertIn("order=created_at.desc,id.desc&limit=20", event_query)
        self.assertNotIn("signwell_document_id=", event_query)
        self.assertEqual(result["offerId"], OFFER)
        self.assertEqual(result["events"][0]["status"], "awaiting_signature")
        self.assertEqual(result["events"][0]["metadata"], {
            "signwell_status": "awaiting signature",
            "message": "Buyer signing is pending.",
            "signwell_document_id": "doc_123",
        })

    def test_missing_or_foreign_offer_does_not_query_events(self):
        with patch.object(API, "_get", AsyncMock(return_value=[])) as get:
            result = asyncio.run(API._agent_offer_activity_timeline({"id": OWNER}, OFFER))
        self.assertIsNone(result)
        get.assert_awaited_once()

    def test_route_returns_timeline_for_verified_user(self):
        handler = SimpleNamespace(
            path=f"/api/admin-dashboard?scope=agent_offer_activity_timeline&offer_id={OFFER}",
            headers={"authorization": "Bearer token"},
        )
        timeline = {"offerId": OFFER, "events": []}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_agent_offer_activity_timeline", AsyncMock(return_value=timeline)) as load, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        load.assert_awaited_once_with({"id": OWNER}, OFFER)
        self.assertEqual(respond.call_args.args[1:], (200, timeline))

    def test_route_does_not_read_for_an_unauthenticated_request(self):
        handler = SimpleNamespace(
            path=f"/api/admin-dashboard?scope=agent_offer_activity_timeline&offer_id={OFFER}",
            headers={"authorization": "Bearer expired"},
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
             patch.object(API, "_agent_offer_activity_timeline", AsyncMock()) as load, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        load.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)

    def test_unavailable_activity_is_not_returned_as_an_empty_timeline(self):
        handler = SimpleNamespace(
            path=f"/api/admin-dashboard?scope=agent_offer_activity_timeline&offer_id={OFFER}",
            headers={"authorization": "Bearer token"},
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_get", AsyncMock(side_effect=[[{"id": OFFER}], {}])), \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        self.assertEqual(respond.call_args.args[1:], (
            503, {"error": "Offer activity is temporarily unavailable."}
        ))


if __name__ == "__main__":
    unittest.main()
