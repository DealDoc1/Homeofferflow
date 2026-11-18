"""Server-owned duplicate rules for saved offers."""
import asyncio
import importlib.util
import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "agent_offer_duplicate_admin", ROOT / "api" / "admin-dashboard.py"
)
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SOURCE_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
REQUEST_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
COPY_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"homeofferflow:duplicate-offer:{OWNER}:{SOURCE_ID}:{REQUEST_ID}"))
PAYLOAD = {"action": "duplicate_agent_offer", "offerId": SOURCE_ID, "requestId": REQUEST_ID}


def source_offer():
    return {
        "id": SOURCE_ID, "role": "investor", "property_address": "123 Main St",
        "buyer_name": "Buyer", "buyer_email": None, "offer_price": 500000,
        "offer_data": {
            "buyerEmail": "buyer@example.test", "financing": "cash",
            "keepThisAnswer": "still needed by the interview",
            "_hofOfferId": SOURCE_ID, "_hof_signature_delivery": {"version": 1},
            "_subscription_user_id": OWNER, "_paragraph4_source_pdf_bytes": "secret-bytes",
            "backend_saved": True, "signwell": {"document_id": "doc-private"},
            "signwellDocumentId": "doc-private", "signwellStatus": "completed",
            "signwell_document_id": "doc-private", "signwell_status": "completed",
            "generatedAt": "2026-10-20", "generated_at": "2026-10-20",
            "packetGeneratedAt": "2026-10-20", "packetGenerationError": "old error",
            "packetGenerationFailedAt": "old time", "packetGenerationFailureCategory": "provider",
            "signwellLastStatusRefresh": "old refresh", "signwellRecipientStatuses": [{"email": "x"}],
            "signingUrl": "https://private.test", "signing_url": "https://private.test",
            "embeddedSigningUrl": "https://private.test", "embedded_signing_url": "https://private.test",
            "recipients": [{"email": "buyer@example.test"}],
            "uploadedDisclosureDocs": [{"base64": "private PDF"}], "uploadedDocNames": ["private.pdf"],
            "transactionTracking": {"acceptedContractConfirmed": True, "effectiveDate": "2026-11-01"},
        },
    }


class AgentOfferDuplicateAPITests(unittest.TestCase):
    def test_duplicate_derives_owner_and_creates_a_clean_unsent_draft(self):
        response = SimpleNamespace(status_code=201, json=lambda: [{"id": COPY_ID}])
        post_call = AsyncMock(return_value=response)

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            post = post_call

        user = {"id": OWNER}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "_headers", return_value={"Authorization": "service-role"}), \
             patch.object(API, "_get", AsyncMock(return_value=[])) as existing, \
             patch.object(API, "_agent_offer_source", AsyncMock(return_value={"offer": source_offer()})) as load, \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            result = asyncio.run(API._duplicate_agent_offer(user, PAYLOAD))
        load.assert_awaited_once_with(user, SOURCE_ID)
        self.assertIn(f"id=eq.{COPY_ID}&user_id=eq.{OWNER}&deleted_at=is.null", existing.await_args.args[0])
        url = post_call.await_args.args[0]
        self.assertIn("/rest/v1/hof_offers?on_conflict=id&select=id", url)
        self.assertEqual(post_call.await_args.kwargs["headers"]["Prefer"], "resolution=ignore-duplicates,return=representation")
        row = post_call.await_args.kwargs["json"]
        self.assertEqual(row["id"], COPY_ID)
        self.assertEqual(row["user_id"], OWNER)
        self.assertEqual(row["role"], "investor")
        self.assertEqual(row["property_address"], "123 Main St (Copy)")
        self.assertEqual(row["buyer_email"], "buyer@example.test")
        self.assertEqual(row["status"], "Draft")
        self.assertEqual(row["offer_data"]["keepThisAnswer"], "still needed by the interview")
        self.assertIsNone(row["offer_data"]["_hofOfferId"])
        for key in (
            "_hof_signature_delivery", "_subscription_user_id", "_paragraph4_source_pdf_bytes",
            "backend_saved", "signwell", "signwellDocumentId", "signwellStatus",
            "signwell_document_id", "signwell_status", "generatedAt", "generated_at",
            "packetGeneratedAt", "packetGenerationError", "packetGenerationFailedAt",
            "packetGenerationFailureCategory", "signwellLastStatusRefresh",
            "signwellRecipientStatuses", "signingUrl", "signing_url", "embeddedSigningUrl",
            "embedded_signing_url", "recipients", "uploadedDisclosureDocs", "uploadedDocNames", "transactionTracking",
        ):
            self.assertNotIn(key, row["offer_data"])
        self.assertEqual(result, {"id": COPY_ID, "copiedFromOfferId": SOURCE_ID})

    def test_rejects_client_authored_fields_without_loading_source(self):
        payload = {**PAYLOAD, "user_id": OWNER}
        with patch.object(API, "_agent_offer_source", AsyncMock()) as load:
            with self.assertRaisesRegex(ValueError, "only the offer"):
                asyncio.run(API._duplicate_agent_offer({"id": OWNER}, payload))
        load.assert_not_awaited()

    def test_missing_or_foreign_source_does_not_create_a_copy(self):
        with patch.object(API, "_agent_offer_source", AsyncMock(return_value=None)) as load, \
             patch.object(API, "_get", AsyncMock(return_value=[])), \
             patch.object(API.httpx, "AsyncClient") as client:
            result = asyncio.run(API._duplicate_agent_offer({"id": OWNER}, PAYLOAD))
        self.assertIsNone(result)
        load.assert_awaited_once()
        client.assert_not_called()

    def test_insert_failure_never_reports_a_created_copy(self):
        response = SimpleNamespace(status_code=500, json=lambda: [])

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            post = AsyncMock(return_value=response)

        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "_headers", return_value={}), \
             patch.object(API, "_get", AsyncMock(return_value=[])), \
             patch.object(API, "_agent_offer_source", AsyncMock(return_value={"offer": source_offer()})), \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            with self.assertRaisesRegex(RuntimeError, "Could not save the copied offer"):
                asyncio.run(API._duplicate_agent_offer({"id": OWNER}, PAYLOAD))

    def test_retry_recovers_the_saved_copy_without_another_insert(self):
        with patch.object(API, "_get", AsyncMock(return_value=[{"id": COPY_ID}])), \
             patch.object(API, "_agent_offer_source", AsyncMock()) as load, \
             patch.object(API.httpx, "AsyncClient") as client:
            result = asyncio.run(API._duplicate_agent_offer({"id": OWNER}, PAYLOAD))
        self.assertEqual(result, {"id": COPY_ID, "copiedFromOfferId": SOURCE_ID})
        load.assert_not_awaited()
        client.assert_not_called()

    def test_conflicting_insert_recovers_only_an_active_owned_copy(self):
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.post.return_value = SimpleNamespace(status_code=201, json=lambda: [])
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "_headers", return_value={}), \
             patch.object(API, "_agent_offer_source", AsyncMock(return_value={"offer": source_offer()})), \
             patch.object(API.httpx, "AsyncClient", return_value=client):
            for existing in ([{"id": COPY_ID}], []):
                with self.subTest(existing=existing), patch.object(API, "_get", AsyncMock(side_effect=[[], existing])) as read:
                    if existing:
                        self.assertEqual(asyncio.run(API._duplicate_agent_offer({"id": OWNER}, PAYLOAD))["id"], COPY_ID)
                    else:
                        with self.assertRaises(PermissionError):
                            asyncio.run(API._duplicate_agent_offer({"id": OWNER}, PAYLOAD))
                    self.assertEqual(read.await_args_list[0].args, read.await_args_list[1].args)

    def test_authenticated_route_returns_copy_and_not_found_for_unavailable_source(self):
        def post(user, duplicate_result):
            raw = json.dumps(PAYLOAD).encode()
            handler = SimpleNamespace(
                path="/api/admin-dashboard",
                headers={"authorization": "Bearer token", "Content-Length": str(len(raw))},
                rfile=BytesIO(raw),
            )
            with patch.object(API, "SUPABASE_URL", "https://private.example"), \
                 patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
                 patch.object(API, "_verified_user", AsyncMock(return_value=user)), \
                 patch.object(API, "_duplicate_agent_offer", AsyncMock(return_value=duplicate_result)) as duplicate, \
                 patch.object(API, "_json") as respond:
                API.handler.do_POST(handler)
            return duplicate, respond.call_args.args[1:]

        copy = {"id": COPY_ID, "copiedFromOfferId": SOURCE_ID}
        duplicate, response = post({"id": OWNER}, copy)
        duplicate.assert_awaited_once()
        self.assertEqual(response, (201, {"ok": True, "offer": copy}))
        _, missing_response = post({"id": OWNER}, None)
        self.assertEqual(missing_response, (404, {"error": "That offer is unavailable."}))

    def test_unauthenticated_route_does_not_duplicate(self):
        raw = json.dumps(PAYLOAD).encode()
        handler = SimpleNamespace(
            path="/api/admin-dashboard",
            headers={"authorization": "Bearer expired", "Content-Length": str(len(raw))},
            rfile=BytesIO(raw),
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
             patch.object(API, "_duplicate_agent_offer", AsyncMock()) as duplicate, \
             patch.object(API, "_json") as respond:
            API.handler.do_POST(handler)
        duplicate.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)


if __name__ == "__main__":
    unittest.main()
