"""Owner-scoped offer detail API returns only fields needed by the workspace."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "agent_offer_detail_admin", ROOT / "api" / "admin-dashboard.py"
)
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OFFER = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


class AgentOfferDetailAPITests(unittest.TestCase):
    def test_detail_checks_owner_and_returns_a_small_offer_projection(self):
        row = {
            "id": OFFER, "status": "Draft", "signwell_status": None,
            "signwell_document_id": None, "property_address": "123 Main St",
            "property_city": "Dallas", "property_zip": "75201", "buyer_name": "Buyer Example",
            "buyer_email": "buyer@example.test", "offer_price": 500000,
            "role": "agent", "generated_at": "2026-10-20T10:00:00Z",
            "created_at": "2026-10-20T09:00:00Z", "last_updated": "2026-10-20T10:00:00Z",
            "private_internal": "must not be selected",
            "offer_data": {
                "buyerName": "Buyer Example", "financing": "conventional",
                "offerPrice": 500000,
                "hoa": "yes", "privateNote": "must not be returned",
                "signwell": {"response": {"id": "legacy-doc", "status": "awaiting_signature", "recipient_email": "private@example.test"}},
                "transactionTracking": {
                    "effectiveDate": "2026-10-20", "acceptedContractConfirmed": True,
                    "privateNote": "must not be returned",
                },
            },
        }
        with patch.object(API, "_get", AsyncMock(side_effect=[
            [row], [{"id": "event", "event_type": "status", "status": "Draft", "metadata": {}, "created_at": "now"}]
        ])) as get:
            result = asyncio.run(API._agent_offer_detail({"id": OWNER}, OFFER))
        detail_query = get.await_args_list[0].args[0]
        self.assertIn("user_id=eq." + OWNER, detail_query)
        self.assertIn("deleted_at=is.null", detail_query)
        self.assertIn("property_city,property_state,property_zip", detail_query)
        self.assertIn("signwell_document_id,signwell_status,offer_data,option_days", detail_query)
        self.assertEqual(get.await_count, 2)
        self.assertIn("hof_offer_events?", get.await_args_list[1].args[0])
        self.assertIn("user_id=eq." + OWNER, get.await_args_list[1].args[0])
        self.assertEqual(result["offerId"], OFFER)
        self.assertEqual(result["offer"]["property_zip"], "75201")
        self.assertEqual(result["offer"]["offer_data"], {
            "buyerName": "Buyer Example", "financing": "conventional", "hoa": "yes",
            "offerPrice": 500000,
            "signwell": {"response": {"id": "legacy-doc", "status": "awaiting_signature"}},
            "transactionTracking": {
                "effectiveDate": "2026-10-20", "acceptedContractConfirmed": True,
            },
        })
        self.assertNotIn("private_internal", result["offer"])
        self.assertEqual(result["events"], [{
            "id": "event", "event_type": "status", "status": "Draft",
            "metadata": {}, "created_at": "now",
        }])

    def test_missing_or_foreign_offer_has_no_timeline_read(self):
        with patch.object(API, "_get", AsyncMock(return_value=[])) as get:
            result = asyncio.run(API._agent_offer_detail({"id": OWNER}, OFFER))
        self.assertIsNone(result)
        get.assert_awaited_once()

    def test_activity_failure_does_not_hide_the_offer_detail(self):
        row = {"id": OFFER, "status": "Draft", "offer_data": {"financing": "cash"}}
        with patch.object(API, "_get", AsyncMock(side_effect=[
            [row], RuntimeError("activity store unavailable")
        ])):
            result = asyncio.run(API._agent_offer_detail({"id": OWNER}, OFFER))
        self.assertEqual(result["offer"]["id"], OFFER)
        self.assertEqual(result["events"], [])
        self.assertTrue(result["activityUnavailable"])

    def test_route_requires_verified_user_and_returns_detail(self):
        handler = SimpleNamespace(
            path=f"/api/admin-dashboard?scope=agent_offer_detail&offer_id={OFFER}",
            headers={"authorization": "Bearer token"},
        )
        detail = {"offerId": OFFER, "offer": {"id": OFFER}, "events": []}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_agent_offer_detail", AsyncMock(return_value=detail)) as load, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        load.assert_awaited_once_with({"id": OWNER}, OFFER)
        self.assertEqual(respond.call_args.args[1:], (200, detail))

    def test_unauthenticated_request_does_not_load_offer(self):
        handler = SimpleNamespace(
            path=f"/api/admin-dashboard?scope=agent_offer_detail&offer_id={OFFER}",
            headers={"authorization": "Bearer expired"},
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
             patch.object(API, "_agent_offer_detail", AsyncMock()) as load, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        load.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)

    def test_offer_store_failure_is_unavailable_instead_of_missing(self):
        handler = SimpleNamespace(path=f"/api/admin-dashboard?scope=agent_offer_detail&offer_id={OFFER}",
                                  headers={"authorization": "Bearer token"})
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_get", AsyncMock(return_value={})), \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        self.assertEqual(respond.call_args.args[1], 503)


if __name__ == "__main__":
    unittest.main()
