import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_standalone_agreements.sql").read_text()
EXPANSION_MIGRATION = (ROOT / "supabase" / "homeofferflow_expand_standalone_representation_forms.sql").read_text()
SHOWING_MIGRATION = (ROOT / "supabase" / "homeofferflow_add_txr_1508_showing_drafts.sql").read_text()
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SPEC = importlib.util.spec_from_file_location("standalone_agreement", ROOT / "api" / "admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_payload():
    return {
        "formCode": "TXR-1507",
        "formSourceId": "00000000-0000-0000-0000-000000000001",
        "clientNames": ["Test Buyer"],
        "marketArea": "Collin and Denton Counties, Texas",
        "termStart": "2026-08-01",
        "termEnd": "2027-01-31",
        "serviceLevel": "full_services",
        "intermediary": "authorized",
        "compensation": {"purchasePercentage": "3"},
    }


def valid_long_payload():
    return {
        "formCode": "TXR-1501",
        "formSourceId": "00000000-0000-0000-0000-000000000001",
        "clientNames": ["Test Buyer"],
        "clientAddress": "721 Broderick Lane",
        "clientCityStateZip": "Prosper, TX 75078",
        "clientPhone": "2143649890",
        "clientEmail": "buyer@example.com",
        "marketArea": "Collin and Denton Counties, Texas",
        "termStart": "2026-08-01",
        "termEnd": "2027-01-31",
        "paymentCounty": "Collin",
        "intermediary": "authorized",
        "compensation": {"purchasePercentage": "3"},
    }


def valid_showing_payload():
    return {
        "formCode": "TXR-1508",
        "formSourceId": "00000000-0000-0000-0000-000000000001",
        "clientNames": ["Test Customer"],
        "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX",
        "otherBrokerAgreement": ["no"],
        "unrepresentedAcknowledgment": True,
    }


class StandaloneAgreementFoundationTests(unittest.TestCase):
    def test_private_standalone_records_are_separate_from_offers(self):
        self.assertIn("create table if not exists public.hof_standalone_agreements", MIGRATION)
        self.assertIn("form_code text not null check (form_code in ('TXR-1507'))", MIGRATION)
        self.assertIn("remain aggregate-only", MIGRATION)
        self.assertIn("hof_standalone_agreements_select_own", MIGRATION)
        self.assertIn("('TXR-1501', 'TXR-1507')", EXPANSION_MIGRATION)
        self.assertIn("('TXR-1501', 'TXR-1507', 'TXR-1508')", SHOWING_MIGRATION)

    def test_valid_short_form_draft_requires_every_decision(self):
        draft = MODULE._parse_txr_1507_draft(valid_payload())
        self.assertEqual(draft["client_names"], ["Test Buyer"])
        self.assertEqual(draft["agreement_data"]["service_level"], "full_services")
        self.assertEqual(draft["agreement_data"]["intermediary"], "authorized")

    def test_showing_services_requires_its_execution_fee(self):
        payload = valid_payload()
        payload["serviceLevel"] = "showing_services"
        with self.assertRaisesRegex(ValueError, "requires the execution fee"):
            MODULE._parse_txr_1507_draft(payload)

    def test_draft_rejects_invalid_term_or_unselected_compensation(self):
        payload = valid_payload()
        payload["termEnd"] = "2026-07-31"
        with self.assertRaisesRegex(ValueError, "cannot be before"):
            MODULE._parse_txr_1507_draft(payload)
        payload = valid_payload()
        payload["compensation"] = {}
        with self.assertRaisesRegex(ValueError, "at least one broker-approved"):
            MODULE._parse_txr_1507_draft(payload)

    def test_draft_does_not_accept_duplicate_clients_or_malformed_fees(self):
        payload = valid_payload()
        payload["clientNames"] = ["Test Buyer", "test buyer"]
        with self.assertRaisesRegex(ValueError, "listed only once"):
            MODULE._parse_txr_1507_draft(payload)
        payload = valid_payload()
        payload["compensation"] = {"purchaseFlatFee": "five hundred"}
        with self.assertRaisesRegex(ValueError, "dollar amount"):
            MODULE._parse_txr_1507_draft(payload)

    def test_no_more_than_two_clients_and_market_area_are_required(self):
        payload = valid_payload()
        payload["clientNames"] = ["One", "Two", "Three"]
        with self.assertRaisesRegex(ValueError, "one or two"):
            MODULE._parse_txr_1507_draft(payload)
        payload = valid_payload()
        payload["marketArea"] = ""
        with self.assertRaisesRegex(ValueError, "Market area"):
            MODULE._parse_txr_1507_draft(payload)

    def test_valid_long_form_draft_is_private_and_deliberate(self):
        draft = MODULE._parse_txr_1501_draft(valid_long_payload())
        self.assertEqual(draft["client_names"], ["Test Buyer"])
        self.assertEqual(draft["agreement_data"]["payment_county"], "Collin")
        self.assertEqual(draft["agreement_data"]["purchase_percentage"], "3")

    def test_long_form_rejects_invalid_contact_retainer_or_protection_terms(self):
        payload = valid_long_payload()
        payload["clientEmail"] = "not-an-email"
        with self.assertRaisesRegex(ValueError, "email must be valid"):
            MODULE._parse_txr_1501_draft(payload)
        payload = valid_long_payload()
        payload["retainerAmount"] = "500"
        with self.assertRaisesRegex(ValueError, "retainer"):
            MODULE._parse_txr_1501_draft(payload)
        payload = valid_long_payload()
        payload["protectionDays"] = "0"
        with self.assertRaisesRegex(ValueError, "Protection period"):
            MODULE._parse_txr_1501_draft(payload)

    def test_valid_showing_draft_is_limited_to_unrepresented_customer_intake(self):
        draft = MODULE._parse_txr_1508_draft(valid_showing_payload())
        self.assertEqual(draft["client_names"], ["Test Customer"])
        self.assertEqual(draft["agreement_data"]["other_broker_agreement"], ["no"])
        self.assertTrue(draft["agreement_data"]["unrepresented_acknowledgment"])

    def test_showing_draft_requires_each_representation_status_and_limit_acknowledgment(self):
        payload = valid_showing_payload()
        payload["otherBrokerAgreement"] = []
        with self.assertRaisesRegex(ValueError, "representation-agreement status"):
            MODULE._parse_txr_1508_draft(payload)
        payload = valid_showing_payload()
        payload["unrepresentedAcknowledgment"] = False
        with self.assertRaisesRegex(ValueError, "no-representation"):
            MODULE._parse_txr_1508_draft(payload)

    def test_agent_ui_requires_an_approved_private_source_and_saves_draft_only(self):
        self.assertIn("Start TXR-1507 draft", HTML)
        self.assertIn("approved-form check", HTML)
        self.assertIn("Source revision", HTML)
        self.assertIn("This saves a private draft only", HTML)
        self.assertIn("create_txr_1507_draft", HTML)
        self.assertIn("/api/admin-dashboard", HTML)
        self.assertIn("Draft saved privately. It has not been sent for signature.", HTML)
        self.assertIn('name="serviceLevel" value="full_services" required', HTML)
        self.assertNotIn('name="serviceLevel" value="full_services" checked', HTML)
        self.assertIn("Start TXR-1501 draft", HTML)
        self.assertIn("TXR-1501 is not yet enabled for your brokerage", HTML)
        self.assertIn("create_txr_1501_draft", HTML)
        self.assertIn("Start TXR-1508 draft", HTML)
        self.assertIn("TXR-1508 is not yet enabled for your brokerage", HTML)
        self.assertIn("create_txr_1508_draft", HTML)
        self.assertIn("no representation, no compensation, no advice", HTML)

    def test_draft_action_reuses_an_existing_authenticated_function(self):
        self.assertFalse((ROOT / "api" / "standalone-agreement.py").exists())
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("create_txr_1507_draft", backend)
        self.assertIn("create_txr_1501_draft", backend)
        self.assertIn("create_txr_1508_draft", backend)
        self.assertIn("_active_brokerage_member", backend)
