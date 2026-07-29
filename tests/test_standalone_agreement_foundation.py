import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_standalone_agreements.sql").read_text()
SPEC = importlib.util.spec_from_file_location("standalone_agreement", ROOT / "api" / "standalone-agreement.py")
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


class StandaloneAgreementFoundationTests(unittest.TestCase):
    def test_private_standalone_records_are_separate_from_offers(self):
        self.assertIn("create table if not exists public.hof_standalone_agreements", MIGRATION)
        self.assertIn("form_code text not null check (form_code in ('TXR-1507'))", MIGRATION)
        self.assertIn("remain aggregate-only", MIGRATION)
        self.assertIn("hof_standalone_agreements_select_own", MIGRATION)

    def test_valid_short_form_draft_requires_every_decision(self):
        draft = MODULE.validate_draft(valid_payload())
        self.assertEqual(draft["client_names"], ["Test Buyer"])
        self.assertEqual(draft["agreement_data"]["service_level"], "full_services")
        self.assertEqual(draft["agreement_data"]["intermediary"], "authorized")

    def test_showing_services_requires_its_execution_fee(self):
        payload = valid_payload()
        payload["serviceLevel"] = "showing_services"
        with self.assertRaisesRegex(ValueError, "requires the execution fee"):
            MODULE.validate_draft(payload)

    def test_no_more_than_two_clients_and_market_area_are_required(self):
        payload = valid_payload()
        payload["clientNames"] = ["One", "Two", "Three"]
        with self.assertRaisesRegex(ValueError, "one or two"):
            MODULE.validate_draft(payload)
        payload = valid_payload()
        payload["marketArea"] = ""
        with self.assertRaisesRegex(ValueError, "Market area"):
            MODULE.validate_draft(payload)
