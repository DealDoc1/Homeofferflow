import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "api" / "fsbo-lead.py"
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
SPEC = importlib.util.spec_from_file_location("fsbo_lead", MODULE_PATH)
fsbo_lead = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fsbo_lead)


class FakeResponse:
    status_code = 201
    text = '[{"id":"partner-lead-123"}]'

    def json(self):
        return [{"id": "partner-lead-123"}]


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.request = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, headers=None, json=None):
        self.request = {"url": url, "headers": headers, "json": json}
        return FakeResponse()


class PartnerLeadTests(unittest.TestCase):
    def test_required_fields_are_enforced(self):
        with self.assertRaisesRegex(ValueError, "required"):
            fsbo_lead._build_partner_payload({"company_name": "Title Co"})

    def test_invalid_email_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "valid contact email"):
            fsbo_lead._build_partner_payload({
                "company_name": "Title Co",
                "contact_name": "Pat Partner",
                "contact_email": "not-an-email",
                "market_area": "North Texas",
            })

    def test_payload_is_normalized_and_choices_are_allowlisted(self):
        payload = fsbo_lead._build_partner_payload({
            "partner_type": "title",
            "company_name": "  North   Texas Title  ",
            "contact_name": " Pat Partner ",
            "contact_email": "PAT@EXAMPLE.COM",
            "market_area": " Collin and Grayson Counties ",
            "preferred_model": "market_exclusive",
            "monthly_budget_range": "500_999",
            "utm_source": "founder_outreach",
        })
        self.assertEqual(payload["company_name"], "North Texas Title")
        self.assertEqual(payload["contact_email"], "pat@example.com")
        self.assertEqual(payload["partner_type"], "title")
        self.assertEqual(payload["preferred_model"], "market_exclusive")
        self.assertEqual(payload["monthly_budget_range"], "500_999")
        self.assertEqual(payload["status"], "new")

    def test_unknown_choices_fall_back_to_safe_defaults(self):
        payload = fsbo_lead._build_partner_payload({
            "partner_type": "unsupported",
            "company_name": "Example Co",
            "contact_name": "Pat Partner",
            "contact_email": "pat@example.com",
            "market_area": "Texas",
            "preferred_model": "unsupported",
            "monthly_budget_range": "unsupported",
        })
        self.assertEqual(payload["partner_type"], "other")
        self.assertEqual(payload["preferred_model"], "founding_pilot")
        self.assertEqual(payload["monthly_budget_range"], "discuss")

    def test_public_sales_tiers_map_to_allowed_models_and_budget_bands(self):
        tiers = (
            ("founding_pilot", "under_250"),
            ("monthly_placement", "250_499"),
            ("market_exclusive", "500_999"),
        )
        for preferred_model, monthly_budget_range in tiers:
            with self.subTest(preferred_model=preferred_model):
                payload = fsbo_lead._build_partner_payload({
                    "partner_type": "inspection",
                    "company_name": "North Texas Partner",
                    "contact_name": "Pat Partner",
                    "contact_email": "pat@example.com",
                    "market_area": "North Texas",
                    "preferred_model": preferred_model,
                    "monthly_budget_range": monthly_budget_range,
                })
                self.assertEqual(payload["preferred_model"], preferred_model)
                self.assertEqual(payload["monthly_budget_range"], monthly_budget_range)

    def test_server_insert_uses_service_role_and_partner_table(self):
        payload = fsbo_lead._build_partner_payload({
            "partner_type": "inspection",
            "company_name": "Inspect North Texas",
            "contact_name": "Pat Partner",
            "contact_email": "pat@example.com",
            "market_area": "DFW",
        })
        with patch.object(fsbo_lead.httpx, "Client", FakeClient):
            row = fsbo_lead._insert_partner_lead(payload)
        self.assertEqual(row["id"], "partner-lead-123")


if __name__ == "__main__":
    unittest.main()
