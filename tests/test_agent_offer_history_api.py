"""Authenticated paginated offer history API with a UI-sized projection."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "agent_offer_history_admin", ROOT / "api" / "admin-dashboard.py"
)
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class AgentOfferHistoryAPITests(unittest.TestCase):
    def test_summary_projects_only_native_card_fields_and_looks_one_row_ahead(self):
        row = {"id": "offer-id", "buyer2_legacy_name": "Co-buyer", "legacy_offer_price": "325000",
               "buyer_email": "buyer@example.test", "signwell_document_id": "private", "offer_data": {"private": True}}
        with patch.object(API, "_get", AsyncMock(return_value=[row] * 26)) as get:
            page = asyncio.run(API._agent_offer_history({"id": OWNER}, 25, view="summary"))
        query = get.await_args.args[0]
        self.assertIn(f"user_id=eq.{OWNER}&deleted_at=is.null", query)
        self.assertIn("last_updated.desc.nullslast,created_at.desc.nullslast,id.desc&offset=25&limit=26", query)
        self.assertIn("buyer2_name:offer_data->>buyer2", query)
        self.assertNotIn("buyer_email", query)
        self.assertEqual((len(page["offers"]), page["nextOffset"], page["hasMore"]), (25, 50, True))
        self.assertEqual(page["offers"][0]["buyer2_legacy_name"], "Co-buyer")
        self.assertEqual(page["offers"][0]["legacy_offer_price"], "325000")
        self.assertTrue({"buyer_email", "offer_data", "signwell_document_id"}.isdisjoint(page["offers"][0]))

    def test_delivery_projection_flags_only_the_matching_unconfirmed_saved_request(self):
        row = {
            "status": "Generated", "signwell_document_id": "tracked-id", "signwell_status": "Draft - Not Sent",
            "offer_data": {"_hof_signature_delivery": {
                "version": 1, "phase": "sending", "document_id": "tracked-id",
                "attempt_id": "private", "fingerprint": "private", "recipients": ["private"],
            }},
        }
        for overrides, expected in (
            ({}, True), ({"signwell_status": None}, True), ({"signwell_status": "sent"}, False),
            ({"signwell_status": "Expired"}, False), ({"signwell_status": "Bounced"}, False),
            ({"status": "Buyer Signed"}, False), ({"signwell_document_id": "different-id"}, False),
        ):
            with self.subTest(overrides=overrides):
                projected = API._project_agent_offer_workspace_row({**row, **overrides})
                flags = {"version": 1}
                if expected:
                    flags["confirmationPending"] = True
                self.assertEqual(projected["offer_data"]["_hof_signature_delivery"], flags)
        row["offer_data"]["_hof_signature_delivery"]["phase"] = "prepared"
        projected = API._project_agent_offer_workspace_row(row)
        self.assertEqual(projected["offer_data"]["_hof_signature_delivery"], {"version": 1})

    def test_history_is_owner_scoped_paginated_and_projects_only_workspace_data(self):
        row = {
            "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "user_id": OWNER,
            "role": "agent", "property_address": "123 Main St", "property_city": "Dallas", "buyer_name": "Buyer",
            "buyer_email": "buyer@example.test", "offer_price": 500000, "status": "Draft",
            "last_updated": "2026-10-29T10:00:00Z", "created_at": "2026-10-29T09:00:00Z",
            "generated_at": None, "signwell_document_id": None, "signwell_status": None,
            "deleted_at": None, "internal_column": "not selected",
            "option_days": 7,
            "offer_data": {
                "propertyAddress": "123 Main St", "buyerName": "Buyer",
                "offerPrice": 500000, "financing": "conventional",
                "closingDate": "2026-11-20",
                "transactionTracking": {
                    "version": 2, "acceptedContractConfirmed": True,
                    "effectiveDate": "2026-10-29", "optionDeadline": "2026-11-05",
                    "closingDate": "2026-11-20", "updatedAt": "2026-10-29T10:00:00+00:00",
                    "milestones": [{"label": "Survey delivery", "date": "2026-11-01"}],
                    "privateField": "must not be returned",
                },
                "privateAnswer": "must not be returned",
                "signwell": {"response": {"id": "legacy-document", "status": "awaiting_signature", "recipient_email": "private@example.test"}},
                "_hof_signature_delivery": {"version": 1, "recipient": "private@example.test"},
            },
        }
        with patch.object(API, "_get", AsyncMock(return_value=[row])) as get:
            result = asyncio.run(API._agent_offer_history({"id": OWNER}, offset="25", limit="25"))
        query = get.await_args.args[0]
        self.assertIn("user_id=eq." + OWNER, query)
        self.assertIn("deleted_at=is.null", query)
        self.assertIn("option_days", query)
        self.assertIn("order=last_updated.desc,id.desc&offset=25&limit=25", query)
        projected = result["offers"][0]
        self.assertNotIn("user_id", projected)
        self.assertNotIn("deleted_at", projected)
        self.assertNotIn("internal_column", projected)
        self.assertEqual(projected["offer_data"]["offerPrice"], 500000)
        self.assertEqual(projected["property_city"], "Dallas")
        self.assertEqual(projected["offer_data"]["closingDate"], "2026-11-20")
        self.assertEqual(projected["offer_data"]["signwell"], {
            "response": {"id": "legacy-document", "status": "awaiting_signature"}
        })
        self.assertEqual(projected["offer_data"]["_hof_signature_delivery"], {"version": 1})
        self.assertEqual(projected["offer_data"]["optionDays"], 7)
        self.assertEqual(projected["offer_data"]["transactionTracking"], {
            "version": 2, "acceptedContractConfirmed": True,
            "effectiveDate": "2026-10-29", "optionDeadline": "2026-11-05",
            "closingDate": "2026-11-20", "updatedAt": "2026-10-29T10:00:00+00:00",
            "milestones": [{"label": "Survey delivery", "date": "2026-11-01"}],
        })
        self.assertNotIn("privateAnswer", projected["offer_data"])
        self.assertNotIn("privateField", projected["offer_data"]["transactionTracking"])
        self.assertEqual((result["offset"], result["nextOffset"], result["hasMore"]), (25, 26, False))

    def test_history_includes_bounded_co_buyer_names_without_extra_contact_data(self):
        cases = [
            ({"buyer2_name": "  QA María  ", "offer_data": {"buyer2": "stale name"}}, "QA María"),
            ({"offer_data": {"buyer2": "  QA André  "}}, "QA André"),
            ({"buyer2_name": " ", "offer_data": {"buyer2Name": "QA Taylor"}}, "QA Taylor"),
            ({"buyer2_name": {"unexpected": "value"}, "offer_data": {"buyer2": ["invalid"], "buyer2Name": "QA Legacy"}}, "QA Legacy"),
            ({"buyer2_name": "X" * 500}, "X" * 200),
            ({}, ""),
        ]
        for values, expected in cases:
            row = {"id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "buyer2_email": "private@example.test", **values}
            row.setdefault("offer_data", {})["buyer2Email"] = "private@example.test"
            with self.subTest(expected=expected), patch.object(API, "_get", AsyncMock(return_value=[row])) as get:
                result = asyncio.run(API._agent_offer_history({"id": OWNER}))
            offer = result["offers"][0]
            self.assertEqual(offer["buyer2_name"], expected)
            self.assertIn("buyer2_name", get.await_args.args[0])
            self.assertNotIn("buyer2_email", offer)
            self.assertNotIn("buyer2Email", offer["offer_data"])

    def test_reloaded_timeline_version_can_update_the_same_offer_again(self):
        offer_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        owner_row = {
            "id": offer_id, "user_id": OWNER, "role": "agent", "status": "Signed",
            "property_address": "123 Main St", "option_days": 7,
            "offer_data": {"optionDays": 7, "transactionTracking": {
                "version": 2, "acceptedContractConfirmed": True,
                "effectiveDate": "2026-10-29", "optionDeadline": "2026-11-05",
                "closingDate": "2026-11-20", "updatedAt": "2026-10-29T10:00:00+00:00",
                "milestones": [{"label": "Survey delivery", "date": "2026-11-01"}],
            }},
        }
        with patch.object(API, "_get", AsyncMock(return_value=[owner_row])):
            history = asyncio.run(API._agent_offer_history({"id": OWNER}))
        saved = history["offers"][0]["offer_data"]["transactionTracking"]

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            async def post(self, url, *, headers, json):
                if json["p_expected_updated_at"] != saved["updatedAt"]:
                    return SimpleNamespace(status_code=200, json=lambda: None)
                return SimpleNamespace(status_code=200, json=lambda: json["p_tracking"])

        with patch.object(API, "_get", AsyncMock(return_value=[owner_row])), \
             patch.object(API.httpx, "AsyncClient", return_value=FakeClient()):
            updated = asyncio.run(API._save_agent_contract_timeline({"id": OWNER}, {
                "action": "save_agent_contract_timeline", "offerId": offer_id,
                "effectiveDate": "2026-10-29", "closingDate": "2026-11-21",
                "milestones": saved["milestones"], "expectedUpdatedAt": saved["updatedAt"],
            }))
        self.assertEqual(updated["offerId"], offer_id)
        self.assertEqual(updated["tracking"]["closingDate"], "2026-11-21")

    def test_rejects_out_of_range_cursor_and_unapproved_page_size(self):
        for offset, limit in (("-1", "25"), ("100001", "25"), ("0", "24"), ("bad", "25")):
            with self.subTest(offset=offset, limit=limit), patch.object(API, "_get", AsyncMock()) as get:
                with self.assertRaises(ValueError):
                    asyncio.run(API._agent_offer_history({"id": OWNER}, offset, limit))
                get.assert_not_awaited()

    def test_full_page_keeps_the_next_history_page_available(self):
        rows = [{"id": f"offer-{index}", "offer_data": {}} for index in range(25)]
        with patch.object(API, "_get", AsyncMock(return_value=rows)):
            result = asyncio.run(API._agent_offer_history({"id": OWNER}, offset=50))
        self.assertEqual(result["nextOffset"], 75)
        self.assertTrue(result["hasMore"])
        self.assertEqual(len(result["offers"]), 25)

    def test_route_uses_verified_user_for_history(self):
        handler = SimpleNamespace(
            path="/api/admin-dashboard?scope=agent_offer_history&offset=25&limit=25",
            headers={"authorization": "Bearer token"},
        )
        history = {"offers": [], "offset": 25, "nextOffset": 25, "hasMore": False}
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value={"id": OWNER})), \
             patch.object(API, "_agent_offer_history", AsyncMock(return_value=history)) as load, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        load.assert_awaited_once_with({"id": OWNER}, "25", "25")
        self.assertEqual(respond.call_args.args[1:], (200, history))

    def test_unauthenticated_request_does_not_read_history(self):
        handler = SimpleNamespace(
            path="/api/admin-dashboard?scope=agent_offer_history&offset=0&limit=25",
            headers={"authorization": "Bearer expired"},
        )
        with patch.object(API, "SUPABASE_URL", "https://private.example"), \
             patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"), \
             patch.object(API, "_verified_user", AsyncMock(return_value=None)), \
             patch.object(API, "_agent_offer_history", AsyncMock()) as load, \
             patch.object(API, "_json") as respond:
            API.handler.do_GET(handler)
        load.assert_not_awaited()
        self.assertEqual(respond.call_args.args[1], 401)

    def test_invalid_store_response_is_unavailable_instead_of_empty_history(self):
        handler = SimpleNamespace(path="/api/admin-dashboard?scope=agent_offer_history",
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
