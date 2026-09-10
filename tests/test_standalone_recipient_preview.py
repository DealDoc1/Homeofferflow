import asyncio
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("admin_recipient_preview", ROOT / "api" / "admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
AGREEMENT_ID = "11111111-1111-4111-8111-111111111111"
USER = {"id": "owner-1", "email": "agent@example.com"}


def showing_draft(plan="associate_and_clients"):
    return {
        "id": AGREEMENT_ID, "brokerage_id": "brokerage-1", "form_code": "TXR-1508",
        "client_names": ["Customer One"],
        "agreement_data": {"signer_plan": plan, "private_notes": "Must not be returned"},
    }


class StandaloneRecipientPreviewTests(unittest.TestCase):
    def test_preview_includes_the_actual_account_associate_and_scopes_the_draft(self):
        get = AsyncMock(side_effect=[[showing_draft()], [{"name": "Office"}]])
        profiles = AsyncMock(return_value=[{"agent_name": "Agent One", "agent_email": "different@example.com"}])
        with patch.object(MODULE, "_get", get), patch.object(MODULE, "_get_optional", profiles):
            result = asyncio.run(MODULE._standalone_signing_recipient_preview(USER, AGREEMENT_ID))
        self.assertIn(f"id=eq.{AGREEMENT_ID}", get.call_args_list[0].args[0])
        self.assertIn("agent_user_id=eq.owner-1", get.call_args_list[0].args[0])
        self.assertIn("status=eq.draft", get.call_args_list[0].args[0])
        self.assertEqual(result["recipients"], [
            {"id": "1", "name": "Customer One", "email": "", "emailEditable": True, "label": "Client 1"},
            {"id": "associate", "name": "Agent One", "email": "agent@example.com", "emailEditable": False, "label": "Associate signer (your account)"},
        ])
        self.assertNotIn("agreement_data", result)
        self.assertNotIn("private_notes", str(result))

    def test_broker_plan_displays_the_broker_instead_of_the_requesting_agent(self):
        get = AsyncMock(side_effect=[[showing_draft("broker_and_clients")], [
            {"contact_name": "Broker One", "contact_email": "broker@example.com"}
        ]])
        with patch.object(MODULE, "_get", get), patch.object(MODULE, "_get_optional", AsyncMock(return_value=[])):
            result = asyncio.run(MODULE._standalone_signing_recipient_preview(USER, AGREEMENT_ID))
        self.assertEqual(result["recipients"][-1]["id"], "broker")
        self.assertEqual(result["recipients"][-1]["email"], "broker@example.com")
        self.assertFalse(result["recipients"][-1]["emailEditable"])

    def test_purchase_addenda_do_not_add_an_agent_or_query_broker_contacts(self):
        draft = {"id": AGREEMENT_ID, "form_code": "TXR-1953", "client_names": ["Buyer", "Seller"],
                 "agreement_data": {"buyer_names": ["Buyer"], "seller_names": ["Seller"]}}
        get = AsyncMock(return_value=[draft])
        profiles = AsyncMock()
        with patch.object(MODULE, "_get", get), patch.object(MODULE, "_get_optional", profiles):
            result = asyncio.run(MODULE._standalone_signing_recipient_preview(USER, AGREEMENT_ID))
        self.assertEqual([recipient["label"] for recipient in result["recipients"]], ["Buyer 1", "Seller 1"])
        self.assertTrue(all(recipient["emailEditable"] for recipient in result["recipients"]))
        get.assert_awaited_once()
        profiles.assert_not_awaited()

    def test_unavailable_or_other_owner_draft_does_not_expose_signing_contacts(self):
        get = AsyncMock(return_value=[])
        profiles = AsyncMock()
        with patch.object(MODULE, "_get", get), patch.object(MODULE, "_get_optional", profiles):
            with self.assertRaises(PermissionError):
                asyncio.run(MODULE._standalone_signing_recipient_preview(USER, AGREEMENT_ID))
        get.assert_awaited_once()
        profiles.assert_not_awaited()

    def test_invalid_draft_identifier_never_reaches_the_database(self):
        get = AsyncMock()
        with patch.object(MODULE, "_get", get), self.assertRaises(ValueError):
            asyncio.run(MODULE._standalone_signing_recipient_preview(USER, "not-a-uuid"))
        get.assert_not_awaited()


class SigningRecipientConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.recipients = [
            {"id": "1", "name": "Customer One", "email": "customer@example.com"},
            {"id": "associate", "name": "Agent One", "email": "agent@example.com"},
        ]

    def test_exact_visible_list_is_accepted_case_insensitively_for_email(self):
        confirmed = copy.deepcopy(self.recipients)
        confirmed[0]["email"] = "CUSTOMER@example.com"
        MODULE._validate_confirmed_signing_recipients(self.recipients, confirmed)

    def test_missing_extra_changed_or_reordered_recipients_are_rejected(self):
        changed = copy.deepcopy(self.recipients)
        changed[-1]["email"] = "unexpected@example.com"
        for confirmed in (None, {}, self.recipients[:1], changed, self.recipients[::-1]):
            with self.subTest(confirmed=confirmed), self.assertRaisesRegex(ValueError, "Reopen Send"):
                MODULE._validate_confirmed_signing_recipients(self.recipients, confirmed)

    def test_customer_cannot_share_the_account_signer_email(self):
        recipients = copy.deepcopy(self.recipients)
        recipients[0]["email"] = "AGENT@example.com"
        with self.assertRaisesRegex(ValueError, "different signing email"):
            MODULE._validate_confirmed_signing_recipients(recipients, recipients)

    def test_unconfirmed_send_stops_before_source_download_or_signwell_request(self):
        draft = showing_draft()
        draft.update({"form_source_id": "source-1", "source_revision": "02-25-26"})
        get = AsyncMock(return_value=[draft])
        resolve = AsyncMock(return_value=self.recipients)
        with patch.object(MODULE, "TXR_SIGNING_ENABLED", True), patch.object(MODULE, "SIGNWELL_ENABLED", True), \
             patch.object(MODULE, "SIGNWELL_API_KEY", "test-only"), patch.object(MODULE, "_get", get), \
             patch.object(MODULE, "_standalone_signing_recipients", resolve), \
             patch.object(MODULE.httpx, "AsyncClient") as client, self.assertRaisesRegex(ValueError, "Reopen Send"):
            asyncio.run(MODULE._send_txr_agreement_for_signature(USER, {
                "agreementId": AGREEMENT_ID, "clientEmails": ["customer@example.com"],
            }))
        get.assert_awaited_once()
        client.assert_not_called()

    def test_send_screen_loads_all_contacts_before_enabling_delivery(self):
        html = (ROOT / "index.html").read_text()
        start = html.index("async function openSendDialog")
        end = html.index("async function refreshAgreementSignWellStatus", start)
        source = html[start:end]
        self.assertIn("scope=standalone_signing_recipients", source)
        self.assertIn("Review everyone who will receive this document", source)
        self.assertIn("readonly", source)
        self.assertIn("confirmedRecipients", source)
        self.assertIn('type="submit" disabled', source)
        self.assertIn("if (!signers.length) return;", source)


if __name__ == "__main__":
    unittest.main()
