import importlib.util
import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "api" / "fsbo-lead.py"
BASELINE_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "supabase" / "homeofferflow_partner_leads.sql"
CATEGORY_MIGRATION_PATH = Path(__file__).resolve().parents[1] / "supabase" / "homeofferflow_expand_partner_categories.sql"
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
        type(self).last_request = self.request
        return FakeResponse()

    def get(self, url, headers=None):
        self.request = {"url": url, "headers": headers}
        type(self).last_request = self.request
        response = FakeResponse()
        response.status_code = 200
        response.text = '[{"id":"placement-1","partner_name":"North Texas Movers"}]'
        response.json = lambda: [{"id": "placement-1", "partner_name": "North Texas Movers"}]
        return response


class PartnerLeadTests(unittest.TestCase):
    @staticmethod
    def _constraint_categories(sql, marker):
        match = re.search(
            rf"{re.escape(marker)}.*?check\s*\(partner_type\s+in\s*\((.*?)\)\)",
            sql,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            raise AssertionError(f"Could not find partner category constraint after {marker!r}.")
        return set(re.findall(r"'([a-z0-9_]+)'", match.group(1)))

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

    def test_roofing_and_home_service_categories_are_preserved(self):
        categories = (
            "roofing",
            "hvac",
            "plumbing",
            "electrical",
            "foundation_structural",
            "general_contractor",
            "pest_termite",
            "septic_well",
            "restoration",
            "surveyor",
            "security_smart_home",
        )
        for partner_type in categories:
            with self.subTest(partner_type=partner_type):
                payload = fsbo_lead._build_partner_payload({
                    "partner_type": partner_type,
                    "company_name": "North Texas Home Services",
                    "contact_name": "Pat Partner",
                    "contact_email": "pat@example.com",
                    "market_area": "North Texas",
                })
                self.assertEqual(payload["partner_type"], partner_type)

    def test_database_constraints_allow_every_api_partner_type(self):
        baseline_sql = BASELINE_SCHEMA_PATH.read_text(encoding="utf-8")
        migration_sql = CATEGORY_MIGRATION_PATH.read_text(encoding="utf-8")
        baseline_categories = self._constraint_categories(
            baseline_sql,
            "partner_type text not null default 'other'",
        )
        migration_categories = self._constraint_categories(
            migration_sql,
            "add constraint hof_partner_leads_partner_type_check",
        )

        self.assertEqual(baseline_categories, fsbo_lead.ALLOWED_PARTNER_TYPES)
        self.assertEqual(migration_categories, fsbo_lead.ALLOWED_PARTNER_TYPES)
        self.assertIn(
            "validate constraint hof_partner_leads_partner_type_check",
            migration_sql.lower(),
        )

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

    def test_public_directory_only_requests_platform_wide_safe_fields(self):
        with patch.object(fsbo_lead.httpx, "Client", FakeClient):
            rows = fsbo_lead._list_public_partner_placements("moving_storage", "DFW")
        self.assertEqual(rows[0]["partner_name"], "North Texas Movers")
        request_url = FakeClient.last_request["url"]
        self.assertIn("brokerage_id=is.null", request_url)
        self.assertIn("partner_type=eq.moving_storage", request_url)
        self.assertIn("select=id%2Cpartner_type%2Cpartner_name", request_url)
        self.assertNotIn("contact_email", request_url)
        self.assertNotIn("source_lead_id", rows[0])

    def test_directory_cta_lookup_is_server_side_and_never_returns_the_source_lead_id(self):
        self.assertIn('_DIRECTORY_LOOKUP_FIELDS = f"{PUBLIC_PARTNER_FIELDS},source_lead_id"', MODULE_PATH.read_text())
        self.assertIn('row.pop("source_lead_id", "")', MODULE_PATH.read_text())
        self.assertIn('row["cta_label"] = ctas[source_lead_id]', MODULE_PATH.read_text())


if __name__ == "__main__":
    unittest.main()
