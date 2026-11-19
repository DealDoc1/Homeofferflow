"""Owner-scoped offer context for the seller disclosure handoff."""
import asyncio
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "seller_disclosure_offer_context_admin", ROOT / "api" / "admin-dashboard.py"
)
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OFFER = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


class SellerDisclosureOfferContextAPITests(unittest.TestCase):
    def test_context_read_is_owner_scoped_and_returns_only_disclosure_fields(self):
        row = {
            "id": OFFER,
            "property_address": "  123 Main Street  ",
            "offer_data": {
                "seller1Name": " Seller One ", "seller2": "Seller Two",
                "seller1Email": "seller@example.test", "buyer1Name": "Private Buyer",
                "defect_roof": "Private offer answer",
            },
        }
        with patch.object(API, "_get", AsyncMock(return_value=[row])) as get:
            result = asyncio.run(API._agent_seller_disclosure_offer_context(
                {"id": OWNER}, OFFER
            ))
        query = get.await_args.args[0]
        self.assertIn("id=eq." + OFFER, query)
        self.assertIn("user_id=eq." + OWNER, query)
        self.assertIn("deleted_at=is.null", query)
        self.assertIn("select=id,property_address,offer_data", query)
        self.assertEqual(result, {
            "offerId": OFFER, "propertyAddress": "123 Main Street",
            "seller1Name": "Seller One", "seller2Name": "Seller Two",
            "seller1Email": "seller@example.test", "seller2Email": "",
        })
        self.assertNotIn("buyer1Name", result)
        self.assertNotIn("defect_roof", result)

    def test_missing_offer_returns_no_context(self):
        with patch.object(API, "_get", AsyncMock(return_value=[])):
            result = asyncio.run(API._agent_seller_disclosure_offer_context(
                {"id": OWNER}, OFFER
            ))
        self.assertIsNone(result)

    def test_route_requires_a_verified_user_before_reading_offer(self):
        handler = type("Handler", (), {
            "path": f"/api/admin-dashboard?scope=agent_seller_disclosure_offer_context&offer_id={OFFER}",
            "headers": {"authorization": "Bearer expired"},
        })()
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
             patch.object(API, "_get", AsyncMock()) as get, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        get.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)

    def test_route_distinguishes_a_missing_offer_from_an_unavailable_lookup(self):
        handler = type("Handler", (), {
            "path": f"/api/admin-dashboard?scope=agent_seller_disclosure_offer_context&offer_id={OFFER}",
            "headers": {"authorization": "Bearer test-token"},
        })()
        for rows, status in (([], 404), ({"unexpected": True}, 503), ([{"id": OWNER}], 503)):
            with self.subTest(rows=rows), \
                 patch.object(API, "SUPABASE_URL", "https://private.example"), \
                 patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
                 patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
                 patch.object(API, "_get", AsyncMock(return_value=rows)), \
                 patch.object(API, "_json") as respond:
                API.handler.do_GET(handler)
            self.assertEqual(respond.call_args.args[1], status)


if __name__ == "__main__":
    unittest.main()
