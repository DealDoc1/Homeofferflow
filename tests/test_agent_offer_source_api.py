"""Owner-scoped full offer source for resuming existing agent work."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "agent_offer_source_admin", ROOT / "api" / "admin-dashboard.py"
)
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OFFER = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


class AgentOfferSourceAPITests(unittest.TestCase):
    def test_source_is_owner_scoped_active_and_contains_interview_data(self):
        offer = {
            "id": OFFER, "role": "agent", "property_address": "123 Main St",
            "buyer_name": "Buyer", "offer_data": {"buyerEmail": "buyer@example.test", "answer": "private to owner"},
        }
        with patch.object(API, "_get", AsyncMock(return_value=[offer])) as get:
            result = asyncio.run(API._agent_offer_source({"id": OWNER}, OFFER))
        query = get.await_args.args[0]
        self.assertIn("id=eq." + OFFER, query)
        self.assertIn("user_id=eq." + OWNER, query)
        self.assertIn("deleted_at=is.null", query)
        self.assertIn("offer_data", query)
        self.assertNotIn("select=*", query)
        self.assertEqual(result, {"offerId": OFFER, "offer": offer})

    def test_missing_or_foreign_offer_returns_no_source(self):
        with patch.object(API, "_get", AsyncMock(return_value=[])) as get:
            result = asyncio.run(API._agent_offer_source({"id": OWNER}, OFFER))
        self.assertIsNone(result)
        get.assert_awaited_once()

    def test_route_uses_verified_identity_and_returns_offer_source(self):
        handler = SimpleNamespace(
            path=f"/api/admin-dashboard?scope=agent_offer_source&offer_id={OFFER}",
            headers={"authorization": "Bearer token"},
        )
        source = {"offerId": OFFER, "offer": {"id": OFFER}}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_agent_offer_source", AsyncMock(return_value=source)) as load, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        load.assert_awaited_once_with({"id": OWNER}, OFFER)
        self.assertEqual(respond.call_args.args[1:], (200, source))

    def test_unauthenticated_route_does_not_read_offer_source(self):
        handler = SimpleNamespace(
            path=f"/api/admin-dashboard?scope=agent_offer_source&offer_id={OFFER}",
            headers={"authorization": "Bearer expired"},
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
             patch.object(API, "_agent_offer_source", AsyncMock()) as load, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        load.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)

    def test_source_route_distinguishes_missing_offer_from_storage_failure(self):
        handler = SimpleNamespace(path=f"/api/admin-dashboard?scope=agent_offer_source&offer_id={OFFER}",
                                  headers={"authorization": "Bearer token"})
        for rows, status in (([], 404), ({}, 503)):
            with self.subTest(status=status), patch.object(API, "SUPABASE_URL", "https://private.example"), \
                 patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
                 patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
                 patch.object(API, "_get", AsyncMock(return_value=rows)), \
                 patch.object(API, "_json") as respond:
                API.handler.do_GET(handler)
            self.assertEqual(respond.call_args.args[1], status)


if __name__ == "__main__":
    unittest.main()
