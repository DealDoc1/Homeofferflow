"""Owner-derived seller lead creation contract and API behavior."""
import asyncio
import importlib.util
import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from lib import seller_lead_creation as leads

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("seller_lead_creation_admin", ROOT / "api" / "admin-dashboard.py")
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BROKERAGE = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
LEAD = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def body(**updates):
    value = {
        "action": "create_seller_lead", "sellerType": "agent_listing",
        "propertyAddress": "  123 Main Street, Dallas, TX ", "sellerName": " Seller One ",
        "sellerEmail": " SELLER@example.com ", "sellerPhone": " (214) 555-0142 ",
        "askingPrice": "550000.50", "mortgageBalance": "120000", "desiredCloseDate": "2026-12-15",
        "notes": " Private follow-up note ",
    }
    value.update(updates)
    return value


class SellerLeadCreationValidationTests(unittest.TestCase):
    def test_normalizes_optional_fields_and_money(self):
        record = leads.validate_seller_lead_creation(body())
        self.assertEqual(record, {
            "seller_type": "agent_listing", "property_address": "123 Main Street, Dallas, TX",
            "seller_name": "Seller One", "seller_email": "seller@example.com",
            "seller_phone": "(214) 555-0142", "asking_price": "550000.50",
            "mortgage_balance": "120000.00", "desired_close_date": "2026-12-15",
            "notes": "Private follow-up note",
        })

    def test_rejects_forged_owner_brokerage_status_and_extra_fields(self):
        for key, value in (("user_id", OWNER), ("brokerage_id", BROKERAGE), ("status", "qualified"), ("source", "admin")):
            data = body()
            data[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "only"):
                leads.validate_seller_lead_creation(data)

    def test_rejects_invalid_type_address_email_amount_date_and_notes(self):
        cases = (
            {"sellerType": "tenant"}, {"propertyAddress": "  "},
            {"sellerEmail": "invalid"}, {"askingPrice": "-1"},
            {"askingPrice": "1.001"}, {"mortgageBalance": "NaN"},
            {"desiredCloseDate": "2026-02-30"}, {"desiredCloseDate": "20261215"},
            {"notes": "x" * 1501},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                leads.validate_seller_lead_creation(body(**changes))


class SellerLeadCreationAPITests(unittest.TestCase):
    def test_agent_read_is_owner_scoped_limited_and_returns_only_needed_fields(self):
        rows = [{"id": LEAD, "seller_type": "fsbo", "property_address": "123 Main Street",
                 "seller_name": "Seller One", "seller_email": "seller@example.com",
                 "asking_price": "500000", "status": "new"}]
        with patch.object(API, "_get", AsyncMock(return_value=rows)) as get:
            result = asyncio.run(API._agent_seller_leads({"id": OWNER}))
        self.assertEqual(result, rows)
        query = get.await_args.args[0]
        self.assertIn("user_id=eq." + OWNER, query)
        self.assertIn("limit=12", query)
        self.assertNotIn("notes", query)
        self.assertNotIn("brokerage_id", query)
        self.assertNotIn("user_id,", query)

    def test_authenticated_get_route_returns_agent_seller_leads(self):
        handler = SimpleNamespace(path="/api/admin-dashboard?scope=agent_seller_leads",
                                  headers={"authorization": "Bearer token"})
        rows = [{"id": LEAD, "seller_type": "fsbo", "property_address": "123 Main Street"}]
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_get", AsyncMock(return_value=rows)) as get, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        self.assertIn("user_id=eq." + OWNER, get.await_args.args[0])
        self.assertEqual(respond.call_args.args[1], 200)
        self.assertEqual(respond.call_args.args[2], {"sellerLeads": rows})

    def test_server_assigns_owner_brokerage_and_status(self):
        saved = {"id": LEAD}
        response = SimpleNamespace(status_code=201, json=lambda: [saved])
        post_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            post = post_call

        with patch.object(API, "_optional_brokerage_id", AsyncMock(return_value=BROKERAGE)) as brokerage, \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._create_seller_lead({"id": OWNER}, body()))
        self.assertEqual(result, saved)
        brokerage.assert_awaited_once_with({"id": OWNER})
        inserted = post_call.await_args.kwargs["json"]
        self.assertEqual((inserted["user_id"], inserted["brokerage_id"], inserted["status"]), (OWNER, BROKERAGE, "new"))

    def test_invalid_session_user_id_is_rejected_before_write(self):
        with patch.object(API, "_optional_brokerage_id", AsyncMock()) as brokerage, \
             patch.object(API.httpx, "AsyncClient") as client:
            with self.assertRaisesRegex(ValueError, "Sign in again"):
                asyncio.run(API._create_seller_lead({"id": "not-a-uuid"}, body()))
        brokerage.assert_not_awaited()
        client.assert_not_called()

    def test_personal_agent_can_save_lead_without_brokerage(self):
        response = SimpleNamespace(status_code=201, json=lambda: [{"id": LEAD}])
        post_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            post = post_call

        with patch.object(API, "_optional_brokerage_id", AsyncMock(return_value=None)), \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._create_seller_lead({"id": OWNER}, body(sellerEmail=None)))
        self.assertIsNone(post_call.await_args.kwargs["json"]["brokerage_id"])
        self.assertIsNone(post_call.await_args.kwargs["json"]["seller_email"])
        self.assertIn("?select=id", post_call.await_args.args[0])
        self.assertEqual(result["id"], LEAD)

    def test_authenticated_route_returns_seller_lead(self):
        data = body()
        raw = json.dumps(data).encode()
        handler = SimpleNamespace(path="/api/admin-dashboard", headers={
            "authorization": "Bearer token", "Content-Length": str(len(raw))
        }, rfile=BytesIO(raw))
        record = {"id": LEAD, "user_id": OWNER, "status": "new"}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_create_seller_lead", AsyncMock(return_value=record)) as create, \
             patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        create.assert_awaited_once_with({"id": OWNER}, data)
        self.assertEqual(respond.call_args.args[1], 201)
        self.assertEqual(respond.call_args.args[2], {"ok": True, "sellerLead": record})


if __name__ == "__main__":
    unittest.main()
