"""Exercise the real disclosure send boundary with fictional, in-memory services.

No source download, database write, provider request or email is possible here.
Completed-provider PDF placement remains separate evidence.
"""
import asyncio
import base64
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch
from lib.seller_disclosure_explanations import RENDER_REVISION

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "seller_disclosure_boundary_admin", ROOT / "api" / "admin-dashboard.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

USER = {"id": "11111111-1111-4111-8111-111111111111"}
DRAFT_ID = "22222222-2222-4222-8222-222222222222"
PDF_STUB = b"fictional test bytes; not a source or signed PDF"


def draft_record(sellers=1, buyers=0, water=False):
    return {
        "id": DRAFT_ID,
        "brokerage_id": "33333333-3333-4333-8333-333333333333",
        "agent_user_id": USER["id"],
        "review_content_revision": "44444444-4444-4444-8444-444444444444",
        "seller_review_render_revision": RENDER_REVISION,
        "seller_names": [f"QA Seller {i + 1}" for i in range(sellers)],
        "buyer_names": [f"QA Buyer {i + 1}" for i in range(buyers)],
        "property_address": "100 Fictional QA Lane",
        "disclosure_source_id": "fictional-disclosure-source",
        "disclosure_source_revision": "fictional-disclosure-revision",
        "water_source_id": "fictional-water-source" if water else None,
        "water_source_revision": "fictional-water-revision" if water else None,
        "response_data": {"item_1_range_oven": "Y"},
        "water_rights_data": {},
        "signwell_document_id": None,
    }


class SellerDisclosureSigningBoundaryTests(unittest.TestCase):
    def run_boundary(self, record, *, emails=None, rows=None, render_error=None):
        count = len(record["seller_names"]) + len(record["buyer_names"])
        if emails is None:
            emails = [f"qa-party-{i}@example.com" for i in range(count)]
        get = AsyncMock(return_value=[record] if rows is None else rows)
        render = AsyncMock(return_value=PDF_STUB, side_effect=render_error)
        deliver = AsyncMock(return_value={
            "document_id": "fictional-provider-document",
            "document": {"id": "fictional-provider-document", "status": "sent"},
            "message": "Fictional delivery only", "recovered": False,
        })
        with patch.multiple(MODULE, TXR_SIGNING_ENABLED=True,
                            SIGNWELL_ENABLED=True, SIGNWELL_API_KEY="fictional-test-key",
                            SIGNWELL_TEST_MODE=True), \
             patch.object(MODULE, "_get", get), \
             patch.object(MODULE, "_seller_reviews_complete_for_draft", AsyncMock(return_value=True)), \
             patch.object(MODULE, "_render_seller_disclosure_draft_preview", render), \
             patch.object(MODULE, "_deliver_tracked_signwell_request", deliver):
            try:
                result = asyncio.run(MODULE._send_seller_disclosure_for_signature(
                    USER, {"draftId": DRAFT_ID, "signerEmails": emails}
                ))
            except Exception as error:
                return error, get, render, deliver
        return result, get, render, deliver

    def test_all_supported_party_counts_and_optional_water_use_real_field_builder(self):
        from lib.trec_seller_disclosure import build_signwell_fields

        for sellers in (1, 2):
            for buyers in (0, 1, 2):
                for water in (False, True):
                    with self.subTest(sellers=sellers, buyers=buyers, water=water):
                        record = draft_record(sellers, buyers, water)
                        result, get, render, deliver = self.run_boundary(record)
                        self.assertIsInstance(result, dict)
                        self.assertEqual(result["recipientCount"], sellers + buyers)
                        self.assertTrue(result["testMode"])
                        query = get.await_args.args[0]
                        for guard in (f"id=eq.{DRAFT_ID}",
                                      f"agent_user_id=eq.{USER['id']}",
                                      "status=eq.draft", "seller_review_attested=is.true"):
                            self.assertIn(guard, query)
                        render.assert_awaited_once()
                        self.assertEqual(render.await_args.args, (USER, DRAFT_ID))
                        deliver.assert_awaited_once()
                        args = deliver.await_args.args
                        self.assertEqual(args[1:4],
                                         ("hof_seller_disclosure_drafts", record, "response_data"))
                        payload, context = args[5:7]
                        self.assertTrue(payload["draft"])
                        self.assertTrue(payload["test_mode"])
                        self.assertFalse(payload["apply_signing_order"])
                        self.assertFalse(payload["with_signature_page"])
                        self.assertEqual(base64.b64decode(payload["files"][0]["file_base64"]), PDF_STUB)
                        expected_names = record["seller_names"] + record["buyer_names"]
                        self.assertEqual([r["name"] for r in payload["recipients"]], expected_names)
                        self.assertEqual([r["id"] for r in payload["recipients"]],
                                         [str(i + 1) for i in range(sellers + buyers)])
                        signing_data = {k: record[k] for k in ("seller_names", "buyer_names")}
                        expected_fields = build_signwell_fields(MODULE.TREC_55_1_FORM_CODE, signing_data)[0]
                        if water:
                            expected_fields += build_signwell_fields(
                                MODULE.TREC_61_0_FORM_CODE, signing_data, page_offset=4)[0]
                        self.assertEqual(len(payload["fields"]), len(payload["files"]))
                        self.assertEqual(payload["fields"], [expected_fields])
                        self.assertEqual(context["owner_id"], USER["id"])
                        self.assertEqual(context["draft_id"], DRAFT_ID)
                        self.assertEqual(context["response_data"], record["response_data"])

    def test_unavailable_or_unreviewed_draft_cannot_render_or_send(self):
        error, _, render, deliver = self.run_boundary(draft_record(), rows=[])
        self.assertIsInstance(error, PermissionError)
        render.assert_not_awaited()
        deliver.assert_not_awaited()

    def test_existing_untracked_request_cannot_create_a_second_send(self):
        record = {**draft_record(), "signwell_document_id": "existing-document"}
        error, _, render, deliver = self.run_boundary(record)
        self.assertIsInstance(error, PermissionError)
        render.assert_not_awaited()
        deliver.assert_not_awaited()

    def test_invalid_or_duplicate_recipient_emails_stop_before_render(self):
        for emails in ([], ["not-an-email", "qa@example.com"],
                       ["SAME@example.com", "same@example.com"]):
            with self.subTest(emails=emails):
                error, _, render, deliver = self.run_boundary(draft_record(2), emails=emails)
                self.assertIsInstance(error, ValueError)
                render.assert_not_awaited()
                deliver.assert_not_awaited()

    def test_source_preview_failure_never_reaches_provider_delivery(self):
        error, _, render, deliver = self.run_boundary(
            draft_record(), render_error=ValueError("Fictional source unavailable"))
        self.assertIsInstance(error, ValueError)
        render.assert_awaited_once()
        deliver.assert_not_awaited()
