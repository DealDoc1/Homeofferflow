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
        response.text = '[{"id":"placement-1","partner_type":"moving_storage","partner_name":"North Texas Movers","placement_tier":"founding"}]'
        response.json = lambda: [{"id": "placement-1", "partner_type":"moving_storage", "partner_name": "North Texas Movers", "placement_tier":"founding"}]
        return response


class PartnerLeadTests(unittest.TestCase):
    def test_insurance_planning_events_use_active_placement_and_only_aggregate_metadata(self):
        data = {'event_type': 'partner_directory_impression', 'partner_id': '22222222-2222-4222-8222-222222222222',
                'partner_type': 'insurance', 'placement_tier': 'founding', 'directory_surface': 'insurance_planning',
                'email': 'not-retained@example.test', 'propertyAddress': 'Do not retain'}
        with patch.object(fsbo_lead.httpx, 'Client', FakeClient), patch.object(fsbo_lead, '_record_partner_checkout_event') as record:
            fsbo_lead._record_partner_directory_event(data)
        self.assertIn('is_active=eq.true', FakeClient.last_request['url'])
        metadata = record.call_args.args[3]
        self.assertEqual(metadata['directorySurface'], 'insurance_planning')
        self.assertEqual(set(metadata), {'partnerId', 'partnerType', 'placementTier', 'directorySurface'})

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
        self.assertEqual(payload["partner_program"], "beta")
        self.assertEqual(payload["status"], "new")

    def test_partner_attribution_keeps_only_an_allowlisted_aggregate_channel(self):
        base = {
            "company_name": "North Texas Title",
            "contact_name": "Pat Partner",
            "contact_email": "pat@example.com",
            "market_area": "North Texas",
        }
        organic = fsbo_lead._build_partner_payload({**base, "acquisition_channel": "organic"})
        self.assertEqual(organic["source"], "tracked_partner_landing")
        self.assertEqual(organic["utm_source"], "organic")
        self.assertEqual(organic["utm_medium"], "privacy_safe_channel")
        self.assertNotIn("landing_page", organic)

        rejected = fsbo_lead._build_partner_payload({
            **base,
            "source": "caller_controlled",
            "landing_page": "https://example.test/private?person=value",
            "acquisition_channel": "example.test/private",
        })
        self.assertEqual(rejected["source"], "website_partner_modal")
        self.assertIsNone(rejected["utm_source"])
        self.assertNotIn("landing_page", rejected)

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

    def test_partner_application_receipt_is_replyable_escaped_and_idempotent(self):
        captured = {}

        class Response:
            status_code = 200

        class Client:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def post(self, *args, **kwargs):
                captured["args"] = args
                captured["kwargs"] = kwargs
                return Response()

        payload = {"company_name": "<script>bad</script>", "contact_name": "Pat Partner", "contact_email": "partner@example.com", "market_area": "North Texas", "preferred_model": "monthly_placement"}
        with patch.object(fsbo_lead, "RESEND_API_KEY", "re_test"), patch.object(fsbo_lead.httpx, "Client", return_value=Client()):
            self.assertEqual(fsbo_lead._send_partner_application_confirmation(payload), "sent")
        self.assertEqual(captured["args"][0], "https://api.resend.com/emails")
        self.assertEqual(captured["kwargs"]["json"]["to"], ["partner@example.com"])
        self.assertEqual(captured["kwargs"]["json"]["reply_to"], "support@homeofferflow.com")
        self.assertEqual(captured["kwargs"]["json"]["bcc"], ["support@homeofferflow.com"])
        self.assertEqual(captured["kwargs"]["json"]["tags"], [
            {"name": "email_type", "value": "partner_application_receipt"},
            {"name": "partner_tier", "value": "monthly_placement"},
        ])
        self.assertNotIn("<script>", captured["kwargs"]["json"]["html"])
        self.assertIn("complimentary during beta", captured["kwargs"]["json"]["text"])
        self.assertIn("What happens next", captured["kwargs"]["json"]["text"])
        self.assertIn("no payment or automatic paid conversion", captured["kwargs"]["json"]["text"])
        self.assertIn("Review your selected partner tier: https://www.homeofferflow.com/partners?partner_tier=monthly_placement", captured["kwargs"]["json"]["text"])
        self.assertIn("<h3>What happens next</h3>", captured["kwargs"]["json"]["html"])
        self.assertIn('href="https://www.homeofferflow.com/partners?partner_tier=monthly_placement', captured["kwargs"]["json"]["html"])
        self.assertTrue(captured["kwargs"]["headers"]["Idempotency-Key"].startswith("partner-application-"))

    def test_partner_receipt_does_not_bcc_the_applicant_to_themselves(self):
        captured = {}

        class Response:
            status_code = 200

        class Client:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def post(self, *args, **kwargs):
                captured["payload"] = kwargs["json"]
                return Response()

        with patch.object(fsbo_lead, "RESEND_API_KEY", "re_test"), patch.object(fsbo_lead, "PARTNER_APPLICATION_ALERT_TO", "partner@example.com"), patch.object(fsbo_lead.httpx, "Client", return_value=Client()):
            self.assertEqual(fsbo_lead._send_partner_application_confirmation({"contact_email": "partner@example.com"}), "sent")
        self.assertNotIn("bcc", captured["payload"])

    def test_partner_application_receipt_steps_are_allowlisted_and_fall_back_safely(self):
        beta_steps = fsbo_lead._partner_application_receipt_steps({"preferred_model": "market_exclusive"})
        self.assertIn("complimentary during beta", beta_steps[1])
        self.assertIn("automatic paid conversion", beta_steps[1])
        self.assertIn("complimentary during beta", fsbo_lead._partner_application_receipt_steps({"preferred_model": "not-a-tier"})[1])

    def test_custom_partner_request_receipt_does_not_describe_a_checkout_path(self):
        steps = fsbo_lead._partner_application_receipt_steps({"preferred_model": "discuss"})
        self.assertIn("complimentary during beta", steps[1])
        self.assertIn("no payment", steps[1])

    def test_partner_application_receipt_telemetry_is_aggregate_and_allowlisted(self):
        captured = []
        with patch.object(fsbo_lead, "_record_partner_checkout_event", side_effect=lambda *args: captured.append(args)):
            fsbo_lead._record_partner_application_receipt_event({"preferred_model": "monthly_placement", "contact_email": "partner@example.com"}, "sent")
            fsbo_lead._record_partner_application_receipt_event({}, "unexpected")
        self.assertEqual(len(captured), 1)
        event_type, status, _, metadata = captured[0]
        self.assertEqual(event_type, "partner_application_receipt_sent")
        self.assertEqual(status, "sent")
        self.assertEqual(metadata, {"surface": "partner_application_receipt", "tier": "monthly_placement"})

    def test_public_directory_only_requests_platform_wide_safe_fields(self):
        with patch.object(fsbo_lead.httpx, "Client", FakeClient):
            rows = fsbo_lead._list_public_partner_placements("moving_storage", "DFW", "directory")
        self.assertEqual(rows[0]["partner_name"], "North Texas Movers")
        request_url = FakeClient.last_request["url"]
        self.assertIn("brokerage_id=is.null", request_url)
        self.assertIn("partner_type=eq.moving_storage", request_url)
        self.assertIn("select=id%2Cpartner_type%2Cpartner_name", request_url)
        self.assertIn("limit=1000", request_url)
        self.assertNotIn("contact_email", request_url)
        self.assertNotIn("source_lead_id", rows[0])

    def test_shared_partner_api_caps_directory_by_category_and_workflow_to_one_top_premier(self):
        rows = [
            {"id":"core-a","partner_type":"title","partner_name":"Core A","placement_tier":"founding"},
            {"id":"premier-b","partner_type":"title","partner_name":"Premier B","placement_tier":"exclusive_market"},
            {"id":"featured","partner_type":"title","partner_name":"Featured","placement_tier":"premier"},
            {"id":"core-b","partner_type":"title","partner_name":"Core B","placement_tier":"founding"},
            {"id":"premier-a","partner_type":"title","partner_name":"Premier A","placement_tier":"exclusive_market"},
            {"id":"insurance-premier","partner_type":"insurance","partner_name":"Insurance Premier","placement_tier":"exclusive_market"},
            {"id":"insurance-core","partner_type":"insurance","partner_name":"Insurance Core","placement_tier":"founding"},
        ]
        directory = fsbo_lead._select_partner_placements_for_view(rows, "directory")
        workflow = fsbo_lead._select_partner_placements_for_view(rows, "workflow")
        self.assertEqual([row["id"] for row in directory], [
            "insurance-premier","insurance-core","premier-a","premier-b","featured"
        ])
        self.assertEqual([row["id"] for row in workflow], ["insurance-premier"])
        self.assertEqual(fsbo_lead._select_partner_placements_for_view(rows, "legacy"), rows)

    def test_category_filtered_workflow_cannot_select_a_second_category_premier(self):
        placements = [
            {"id":"insurance-premier","partner_type":"insurance","partner_name":"Insurance Premier","placement_tier":"exclusive_market"},
            {"id":"title-premier","partner_type":"title","partner_name":"Title Premier","placement_tier":"exclusive_market"},
        ]

        class PlacementClient:
            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def get(self, url, headers=None):
                self_url = url
                response = FakeResponse()
                response.status_code = 200
                response.text = "[]"
                response.json = lambda: placements
                PlacementClient.last_url = self_url
                return response

        with patch.object(fsbo_lead.httpx, "Client", PlacementClient):
            title_rows = fsbo_lead._list_public_partner_placements("title", view="workflow")
        self.assertEqual(title_rows, [])
        self.assertNotIn("partner_type=eq.title", PlacementClient.last_url)

    def test_public_partner_route_accepts_view_and_preserves_response_shape(self):
        endpoint = object.__new__(fsbo_lead.handler)
        endpoint.path = "/api/fsbo-lead?partner_directory=1&surface=workflow&category=title"
        expected = [{"id":"premier","partner_type":"title","placement_tier":"exclusive_market"}]
        response = object()
        with patch.object(fsbo_lead, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(fsbo_lead, "SUPABASE_SERVICE_ROLE_KEY", "test"), \
             patch.object(fsbo_lead, "_list_public_partner_placements", return_value=expected) as load, \
             patch.object(fsbo_lead, "_send", return_value=response) as send:
            result = endpoint.do_GET()
        load.assert_called_once_with("title", None, "workflow")
        send.assert_called_once_with(endpoint, 200, {"ok":True,"partners":expected})
        self.assertIs(result, response)

    def test_directory_cta_lookup_is_server_side_and_never_returns_the_source_lead_id(self):
        self.assertIn('_DIRECTORY_LOOKUP_FIELDS = f"{PUBLIC_PARTNER_FIELDS},source_lead_id"', MODULE_PATH.read_text())
        self.assertIn('row.pop("source_lead_id", "")', MODULE_PATH.read_text())
        self.assertIn('row["cta_label"] = ctas[source_lead_id]', MODULE_PATH.read_text())


if __name__ == "__main__":
    unittest.main()
