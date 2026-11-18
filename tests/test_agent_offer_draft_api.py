"""Authenticated, packet-safe dashboard offer draft persistence."""
import asyncio
import importlib.util
import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agent_offer_draft_admin", ROOT / "api" / "admin-dashboard.py")
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OFFER_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def draft_offer():
    return {
        "role": "agent", "property_address": "QA property", "property_city": "Plano",
        "property_state": "TX", "property_zip": None, "property_county": None,
        "buyer_name": "QA buyer", "buyer_email": "buyer@example.test", "buyer_phone": None,
        "buyer2_name": None, "buyer2_email": None, "seller_name": None, "agent_name": "Agent",
        "agent_email": "agent@example.test", "agent_phone": None, "agent_license": None,
        "agent_brokerage": None, "agent_broker_license": None, "offer_price": 400000,
        "financing_type": "cash", "loan_amount": None, "down_payment": None,
        "earnest_money": None, "option_fee": None, "option_days": None,
        "closing_date": None, "title_company": None, "escrow_agent": None,
        "offer_data": {
            "userType": "agent", "repairsText": "Preserve this interview answer",
            "uploadedDocNames": ["reattach.pdf"], "_hofOfferId": OFFER_ID,
            "_hof_signature_delivery": {"private": True}, "_subscription_user_id": OWNER,
            "_paragraph4_source_pdf_bytes": "private bytes", "backend_saved": True,
            "signwell": {"document_id": "private-doc"}, "signwellDocumentId": "private-doc",
            "signwellStatus": "completed", "generatedAt": "old", "packetGenerationError": "old",
            "signingUrl": "https://private.invalid", "recipients": [{"email": "buyer@example.test"}],
            "uploadedDisclosureDocs": [{"base64": "private PDF"}],
        },
    }


class AgentOfferDraftAPITests(unittest.TestCase):
    def test_create_derives_owner_and_saves_only_a_clean_draft(self):
        response = SimpleNamespace(status_code=201, json=lambda: [{"id": OFFER_ID, "last_updated": "new-version"}])
        post = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            async def post(self, *args, **kwargs): return await post(*args, **kwargs)

        data = {"action": "save_agent_offer_draft", "offerId": None, "offer": draft_offer()}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "_headers", return_value={"Authorization": "service-role"}), \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._save_agent_offer_draft({"id": OWNER}, data))
        row = post.await_args.kwargs["json"]
        self.assertEqual(row["user_id"], OWNER)
        self.assertEqual(row["status"], "Draft")
        self.assertNotIn("last_updated", data["offer"])
        self.assertEqual(row["property_address"], "QA property")
        self.assertEqual(row["offer_data"]["repairsText"], "Preserve this interview answer")
        self.assertEqual(row["offer_data"]["uploadedDocNames"], ["reattach.pdf"])
        self.assertIsNone(row["offer_data"]["_hofOfferId"])
        for key in (
            "_hof_signature_delivery", "_subscription_user_id", "_paragraph4_source_pdf_bytes",
            "backend_saved", "signwell", "signwellDocumentId", "signwellStatus", "generatedAt",
            "packetGenerationError", "signingUrl", "recipients", "uploadedDisclosureDocs",
        ):
            self.assertNotIn(key, row["offer_data"])
        self.assertEqual(result, {"id": OFFER_ID, "saved": True, "created": True, "updatedAt": "new-version"})

    def test_update_is_owner_scoped_version_checked_and_never_writes_packet_status(self):
        response = SimpleNamespace(status_code=200, json=lambda: [{"id": OFFER_ID, "last_updated": "new-version"}])
        patch_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            async def patch(self, *args, **kwargs): return await patch_call(*args, **kwargs)

        data = {"action": "save_agent_offer_draft", "offerId": OFFER_ID, "offer": draft_offer(), "expectedUpdatedAt": "old-version"}
        current = [{"id": OFFER_ID, "status": "Draft", "last_updated": "old-version", "offer_data": {}}]
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "_headers", return_value={}), \
             patch.object(API, "_get", AsyncMock(return_value=current)) as get, \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._save_agent_offer_draft({"id": OWNER}, data))
        get.assert_awaited_once()
        query = get.await_args.args[0]
        self.assertIn(f"user_id=eq.{OWNER}", query)
        self.assertIn("deleted_at=is.null", query)
        url = patch_call.await_args.args[0]
        self.assertIn(f"id=eq.{OFFER_ID}", url)
        self.assertIn(f"user_id=eq.{OWNER}", url)
        self.assertIn("last_updated=eq.old-version", url)
        row = patch_call.await_args.kwargs["json"]
        self.assertEqual(row["offer_data"]["_hofOfferId"], OFFER_ID)
        for key in ("status", "generated_at", "signwell_document_id", "signwell_status"):
            self.assertNotIn(key, row)
        self.assertEqual(result, {"id": OFFER_ID, "saved": True, "created": False, "updatedAt": "new-version"})

    def test_prepared_or_non_draft_rows_request_a_clean_copy_without_writing(self):
        for row in (
            {"status": "Buyer Signed"}, {"status": "Generated"},
            {"status": "Draft", "signwell_document_id": "doc"},
            {"status": "Draft", "offer_data": {"signwell": {"response": {"id": "doc"}}}},
            {"status": "Draft", "offer_data": {"_hof_signature_delivery": {}}},
        ):
            with self.subTest(row=row), patch.object(API, "_get", AsyncMock(return_value=[{
                "id": OFFER_ID, "last_updated": "v1", **row,
            }])) as get, patch.object(API.httpx, "AsyncClient") as client:
                result = asyncio.run(API._save_agent_offer_draft(
                    {"id": OWNER}, {"action": "save_agent_offer_draft", "offerId": OFFER_ID, "offer": draft_offer(), "expectedUpdatedAt": "old-version"}
                ))
            self.assertTrue(result["copyRequired"])
            self.assertFalse(result["saved"])
            client.assert_not_called()

    def test_missing_foreign_and_deleted_rows_never_write(self):
        with patch.object(API, "_get", AsyncMock(return_value=[])) as get, \
             patch.object(API.httpx, "AsyncClient") as client:
            with self.assertRaisesRegex(PermissionError, "unavailable"):
                asyncio.run(API._save_agent_offer_draft(
                    {"id": OWNER}, {"action": "save_agent_offer_draft", "offerId": OFFER_ID, "offer": draft_offer(), "expectedUpdatedAt": "old-version"}
                ))
        get.assert_awaited_once()
        client.assert_not_called()

    def test_concurrent_update_conflict_does_not_report_a_saved_draft(self):
        response = SimpleNamespace(status_code=200, json=lambda: [])
        patch_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            async def patch(self, *args, **kwargs): return await patch_call(*args, **kwargs)

        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "_headers", return_value={}), \
             patch.object(API, "_get", AsyncMock(return_value=[{
                 "id": OFFER_ID, "status": "Draft", "last_updated": "old-version", "offer_data": {},
             }])), patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._save_agent_offer_draft(
                {"id": OWNER}, {"action": "save_agent_offer_draft", "offerId": OFFER_ID,
                                "offer": draft_offer(), "expectedUpdatedAt": "old-version"}
            ))
        self.assertTrue(result["conflict"])
        self.assertFalse(result["saved"])


    def test_stale_or_legacy_snapshot_requires_a_copy_without_patching(self):
        base = {"action": "save_agent_offer_draft", "offerId": OFFER_ID, "offer": draft_offer()}
        current = {"id": OFFER_ID, "status": "Draft", "last_updated": "latest", "offer_data": {}}
        for revision in ({}, {"expectedUpdatedAt": "old-version"}, {"expectedUpdatedAt": None}):
            with self.subTest(revision=revision), patch.object(API, "_get", AsyncMock(return_value=[current])), \
                 patch.object(API.httpx, "AsyncClient") as client:
                result = asyncio.run(API._save_agent_offer_draft({"id": OWNER}, {**base, **revision}))
            self.assertTrue(result["copyRequired"])
            self.assertTrue(result["conflict"])
            client.assert_not_called()

    def test_unsupported_fields_roles_and_amounts_are_rejected(self):
        cases = []
        extra = draft_offer(); extra["owner_id"] = OWNER; cases.append(extra)
        invalid_role = draft_offer(); invalid_role["role"] = "homebuyer"; cases.append(invalid_role)
        invalid_amount = draft_offer(); invalid_amount["offer_price"] = -1; cases.append(invalid_amount)
        invalid_days = draft_offer(); invalid_days["option_days"] = 400; cases.append(invalid_days)
        for offer in cases:
            with self.subTest(offer=offer), patch.object(API, "_get", AsyncMock()) as get, \
                 patch.object(API.httpx, "AsyncClient") as client:
                with self.assertRaises(ValueError):
                    asyncio.run(API._save_agent_offer_draft(
                        {"id": OWNER}, {"action": "save_agent_offer_draft", "offerId": None, "offer": offer}
                    ))
            get.assert_not_awaited()
            client.assert_not_called()

    def test_authenticated_route_creates_and_large_body_is_bounded(self):
        payload = {"action": "save_agent_offer_draft", "offerId": None, "offer": draft_offer()}
        payload["offer"]["offer_data"]["repairsText"] = "x" * (API.MAX_BODY_BYTES + 1)
        raw = json.dumps(payload).encode()
        handler = SimpleNamespace(
            path="/api/admin-dashboard", headers={"authorization": "Bearer token", "Content-Length": str(len(raw))},
            rfile=BytesIO(raw),
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_save_agent_offer_draft", AsyncMock(return_value={
                 "id": OFFER_ID, "saved": True, "created": True,
             })) as save, patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        save.assert_awaited_once()
        self.assertEqual(respond.call_args.args[1], 201)

        too_large = json.dumps({"action": "save_agent_offer_draft", "padding": "x" * API.MAX_AGENT_OFFER_DRAFT_BODY_BYTES}).encode()
        oversized_handler = SimpleNamespace(
            path="/api/admin-dashboard", headers={"authorization": "Bearer token", "Content-Length": str(len(too_large))},
            rfile=BytesIO(too_large),
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_save_agent_offer_draft", AsyncMock()) as save, \
             patch.object(API, "_json") as respond:
            API.handler.do_POST(oversized_handler)
        save.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 413)

    def test_unauthenticated_route_never_saves(self):
        raw = json.dumps({"action": "save_agent_offer_draft", "offerId": None, "offer": draft_offer()}).encode()
        handler = SimpleNamespace(
            path="/api/admin-dashboard", headers={"authorization": "Bearer expired", "Content-Length": str(len(raw))},
            rfile=BytesIO(raw),
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
             patch.object(API, "_save_agent_offer_draft", AsyncMock()) as save, \
             patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        save.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)


if __name__ == "__main__":
    unittest.main()
