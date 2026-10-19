"""Actual review/API paths with fictional services; never sends a document."""
import asyncio
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from lib.seller_disclosure_explanations import RENDER_REVISION
from lib.seller_review_access import current_review

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("review_binding_admin", ROOT / "api/admin-dashboard.py")
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
VERSION = "44444444-4444-4444-8444-444444444444"
OTHER_VERSION = "55555555-5555-4555-8555-555555555555"
DRAFT = {"id": "22222222-2222-4222-8222-222222222222",
         "brokerage_id": "33333333-3333-4333-8333-333333333333",
         "agent_user_id": "11111111-1111-4111-8111-111111111111",
         "seller_names": ["QA Seller One", "QA Seller Two"],
         "review_content_revision": VERSION, "seller_review_attested": False}


def links():
    return [{"id": str(i), "draft_id": DRAFT["id"], "brokerage_id": DRAFT["brokerage_id"],
             "agent_user_id": DRAFT["agent_user_id"], "seller_index": i,
             "seller_name": name, "seller_attested_name": name,
             "seller_attested_at": "2026-10-15T10:00:00Z", "viewed_at": "2026-10-15T09:59:00Z",
             "session_expires_at": "2099-01-01T00:00:00Z",
             "review_content_revision": VERSION, "review_render_revision": RENDER_REVISION}
            for i, name in enumerate(DRAFT["seller_names"], 1)]


class Client:
    rows = []
    writes = []
    def __init__(self, **kwargs): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def patch(self, url, **kwargs):
        self.writes.append((url, kwargs))
        class Response:
            status_code = 200
            def json(self): return Client.rows
        return Response()
    async def post(self, url, **kwargs):
        self.writes.append((url, kwargs))
        class Response:
            status_code = 201
            def json(self): return [{"id": "fictional-created-link"}]
        return Response()


class SellerReviewRevisionBindingTests(unittest.TestCase):
    def setUp(self):
        Client.rows, Client.writes = [], []

    def test_identity_alone_cannot_bind_old_missing_or_other_render_versions(self):
        good = links()[0]
        self.assertTrue(current_review(good, DRAFT, RENDER_REVISION))
        for change in ({"review_content_revision": None}, {"review_content_revision": "bad"},
                       {"review_content_revision": OTHER_VERSION},
                       {"review_render_revision": "older-layout"}, {"revoked_at": "2026-10-15"}):
            with self.subTest(change=change):
                self.assertFalse(current_review({**good, **change}, DRAFT, RENDER_REVISION))
        self.assertFalse(current_review(good, {}, RENDER_REVISION))

    def complete(self, rows):
        get = AsyncMock(return_value=rows)
        with patch.object(API, "_get", get):
            result = asyncio.run(API._seller_reviews_complete_for_draft(copy.deepcopy(DRAFT)))
        self.assertIn("review_content_revision=eq." + VERSION, get.await_args.args[0])
        self.assertIn("agent_user_id=eq." + DRAFT["agent_user_id"], get.await_args.args[0])
        return result

    def test_only_current_attestation_for_each_exact_seller_passes(self):
        self.assertTrue(self.complete(links()))
        for rows in ([], links()[:1], [links()[0], links()[0]]):
            self.assertFalse(self.complete(rows))
        for key, value in (("seller_attested_name", "Someone Else"), ("seller_name", "Someone Else"),
                           ("seller_attested_at", None), ("seller_index", 1),
                           ("review_content_revision", OTHER_VERSION),
                           ("review_render_revision", "old"), ("revoked_at", "2026-10-15")):
            rows = links(); rows[1][key] = value
            with self.subTest(key=key):
                self.assertFalse(self.complete(rows))

    def test_legacy_unassigned_single_seller_link_does_not_pass_version_requirement(self):
        draft = {**DRAFT, "seller_names": ["QA Seller One"]}
        with patch.object(API, "_get", AsyncMock(return_value=[{**links()[0], "seller_index": None}])):
            self.assertFalse(asyncio.run(API._seller_reviews_complete_for_draft(draft)))

    def test_stale_session_cannot_view_new_answers_or_record_viewed(self):
        draft = {**DRAFT, "review_content_revision": OTHER_VERSION}
        event = AsyncMock()
        with patch.object(API, "_get", AsyncMock(side_effect=[[links()[0]], [draft]])), \
             patch.object(API, "_record_offer_event", event), \
             patch.object(API.httpx, "AsyncClient", side_effect=AssertionError("No write permitted")):
            with self.assertRaisesRegex(PermissionError, "changed"):
                asyncio.run(API._seller_review_context("x" * 40))
        event.assert_not_awaited()

    def test_changed_between_review_and_pdf_query_cannot_render_other_answers(self):
        with patch.object(API, "_get", AsyncMock(return_value=[{**DRAFT, "review_content_revision": OTHER_VERSION}])):
            with self.assertRaisesRegex(PermissionError, "changed"):
                asyncio.run(API._render_seller_disclosure_draft_preview(None, DRAFT["id"], review_context=links()[0]))
            with self.assertRaisesRegex(PermissionError, "changed"):
                asyncio.run(API._render_seller_disclosure_draft_preview(
                    {"id": DRAFT["agent_user_id"]}, DRAFT["id"], expected_review_revision=VERSION))

    def test_aggregate_cache_write_is_version_conditional_and_zero_rows_is_not_success(self):
        for returned, expected in (([], False), ([DRAFT], True)):
            Client.rows = returned; Client.writes = []
            with patch.object(API, "_get", AsyncMock(side_effect=[[DRAFT], links()])), \
                 patch.object(API.httpx, "AsyncClient", Client):
                self.assertEqual(asyncio.run(API._refresh_seller_review_attestation(
                    DRAFT["id"], DRAFT["brokerage_id"])), expected)
            url, options = Client.writes[0]
            self.assertIn("status=eq.draft&review_content_revision=eq." + VERSION, url)
            self.assertEqual(options["json"]["seller_review_render_revision"], RENDER_REVISION)
            self.assertEqual(options["headers"]["Prefer"], "return=representation")

    def test_partial_review_never_sets_aggregate_true(self):
        with patch.object(API, "_get", AsyncMock(side_effect=[[DRAFT], links()[:1]])), \
             patch.object(API.httpx, "AsyncClient", side_effect=AssertionError("No aggregate write")):
            self.assertFalse(asyncio.run(API._refresh_seller_review_attestation(DRAFT["id"], DRAFT["brokerage_id"])))

    def test_zero_row_attestation_does_not_announce_completion(self):
        link = {**links()[0], "seller_attested_at": None}
        refresh, event = AsyncMock(), AsyncMock()
        with patch.object(API, "_seller_review_context", AsyncMock(return_value=(link, DRAFT))), \
             patch.object(API, "_refresh_seller_review_attestation", refresh), \
             patch.object(API, "_record_offer_event", event), patch.object(API.httpx, "AsyncClient", Client):
            with self.assertRaisesRegex(PermissionError, "changed"):
                asyncio.run(API._attest_seller_review("fictional", {"sellerName": "QA Seller One"}))
        self.assertIn("revoked_at=is.null&review_content_revision=eq." + VERSION, Client.writes[0][0])
        refresh.assert_not_awaited(); event.assert_not_awaited()

    def test_cached_true_without_current_review_never_reaches_pdf_or_provider(self):
        record = {**DRAFT, "seller_review_attested": True, "seller_review_render_revision": RENDER_REVISION}
        render, deliver = AsyncMock(), AsyncMock()
        with patch.multiple(API, TXR_SIGNING_ENABLED=True, SIGNWELL_ENABLED=True, SIGNWELL_API_KEY="fictional"), \
             patch.object(API, "_get", AsyncMock(side_effect=[[record], links()[:1]])), \
             patch.object(API, "_render_seller_disclosure_draft_preview", render), \
             patch.object(API, "_deliver_tracked_signwell_request", deliver):
            with self.assertRaisesRegex(PermissionError, "Every seller"):
                asyncio.run(API._send_seller_disclosure_for_signature({"id": DRAFT["agent_user_id"]}, {"draftId": DRAFT["id"]}))
        render.assert_not_awaited(); deliver.assert_not_awaited()

    def test_missing_schema_is_not_silently_treated_as_reviewed(self):
        with patch.object(API, "_get", AsyncMock(return_value=[{**DRAFT, "review_content_revision": None}])):
            with self.assertRaisesRegex(RuntimeError, "temporarily unavailable"):
                asyncio.run(API._create_seller_disclosure_review_link({"id": DRAFT["agent_user_id"]}, {"draftId": DRAFT["id"]}))

    def test_new_review_links_capture_saved_content_and_current_render_version(self):
        email = AsyncMock()
        reviews = [{"sellerName": name, "sellerIndex": i, "sellerEmail": f"qa{i}@example.test"}
                   for i, name in enumerate(DRAFT["seller_names"], 1)]
        with patch.object(API, "_get", AsyncMock(side_effect=[[{**DRAFT, "property_address": "Fictional QA"}], []])), \
             patch.object(API.httpx, "AsyncClient", Client), patch.object(API, "_deliver_seller_review_email", email):
            result = asyncio.run(API._create_seller_disclosure_review_link(
                {"id": DRAFT["agent_user_id"]}, {"draftId": DRAFT["id"], "sellerReviews": reviews}))
        self.assertEqual(len(result["links"]), 2)
        self.assertEqual(email.await_count, 2)  # Fictional AsyncMock only.
        for _, options in Client.writes:
            self.assertEqual(options["json"]["review_content_revision"], VERSION)
            self.assertEqual(options["json"]["review_render_revision"], RENDER_REVISION)

    def test_successful_attestation_checks_exact_write_then_refreshes_all_sellers(self):
        link = {**links()[0], "seller_attested_at": None}
        Client.rows = [{"id": link["id"]}]
        refresh, event = AsyncMock(return_value=True), AsyncMock()
        with patch.object(API, "_seller_review_context", AsyncMock(return_value=(link, DRAFT))), \
             patch.object(API, "_refresh_seller_review_attestation", refresh), \
             patch.object(API, "_record_offer_event", event), patch.object(API.httpx, "AsyncClient", Client):
            result = asyncio.run(API._attest_seller_review("fictional", {"sellerName": "QA Seller One"}))
        self.assertTrue(result["allSellersAttested"])
        refresh.assert_awaited_once_with(DRAFT["id"], DRAFT["brokerage_id"])
        event.assert_awaited_once()

    def test_saving_reviewed_draft_resets_all_constraint_coupled_fields(self):
        source = "66666666-6666-4666-8666-666666666666"
        with patch.object(API, "_get", AsyncMock(return_value=[{"id": source, "brokerage_id": DRAFT["brokerage_id"], "source_revision": "qa-source"}])):
            _, record = asyncio.run(API._prepare_seller_disclosure_draft_record(
                {"id": DRAFT["agent_user_id"]}, {"formCode": "TREC-55-1", "disclosureSourceId": source, "propertyAddress": "100 Fictional QA Lane",
                                                 "sellerNames": ["QA Seller One"], "responseData": {}}))
        self.assertFalse(record["seller_review_attested"])
        for key in ("seller_review_attested_at", "seller_review_attested_by", "seller_review_render_revision"):
            self.assertIsNone(record[key])

    def test_saving_cannot_erase_a_tracked_signature_or_its_delivery_journal(self):
        for tracking in ({"signwell_document_id": "fictional-tracked"},
                         {"response_data": {API.signwell_delivery.JOURNAL_KEY: {"phase": "created"}}}):
            with self.subTest(tracking=tracking), \
                 patch.object(API, "_prepare_seller_disclosure_draft_record", AsyncMock(return_value=(DRAFT["brokerage_id"], {}))), \
                 patch.object(API, "_get", AsyncMock(return_value=[{**DRAFT, **tracking}])), \
                 patch.object(API.httpx, "AsyncClient", side_effect=AssertionError("No save permitted")):
                with self.assertRaisesRegex(PermissionError, "already has a signing request"):
                    asyncio.run(API._update_seller_disclosure_draft(
                        {"id": DRAFT["agent_user_id"]}, {"draftId": DRAFT["id"]}))

    def test_save_losing_race_to_signature_claim_is_not_reported_as_saved(self):
        with patch.object(API, "_prepare_seller_disclosure_draft_record", AsyncMock(return_value=(DRAFT["brokerage_id"], {}))), \
             patch.object(API, "_get", AsyncMock(return_value=[DRAFT])), patch.object(API.httpx, "AsyncClient", Client):
            with self.assertRaisesRegex(RuntimeError, "not returned"):
                asyncio.run(API._update_seller_disclosure_draft(
                    {"id": DRAFT["agent_user_id"]}, {"draftId": DRAFT["id"]}))
        self.assertIn("signwell_document_id=is.null", Client.writes[0][0])
