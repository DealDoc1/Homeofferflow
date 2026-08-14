import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_partner_placement_activation_gate.sql").read_text(encoding="utf-8")
PUBLIC_VIEW_MIGRATION = (ROOT / "supabase" / "homeofferflow_partner_placement_public_view.sql").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class PartnerPlacementActivationGateTests(unittest.TestCase):
    def test_schema_records_paid_application_and_agreement_confirmation(self):
        self.assertIn("source_lead_id uuid", MIGRATION)
        self.assertIn("agreement_confirmed_at timestamptz", MIGRATION)
        self.assertIn("hof_partner_placements_active_source_lead_key", MIGRATION)
        exclusivity = (ROOT / "supabase" / "migrations" / "20260813232218_partner_exclusive_market_guard.sql").read_text(encoding="utf-8")
        self.assertIn("hof_partner_placements_active_exclusive_market_key", exclusivity)
        self.assertIn("placement_tier = 'exclusive_market'", exclusivity)
        self.assertIn("lower(btrim(market_area))", exclusivity)

    def test_server_derives_public_placement_from_paid_application(self):
        self.assertIn("Only a paid partner application can activate a public placement.", ADMIN)
        self.assertIn("Complete the secure partner onboarding before activating a public placement.", ADMIN)
        self.assertIn("A completed HomeOfferFlow Partner Marketplace Agreement is required", ADMIN)
        self.assertIn("This paid partner application already has an active placement.", ADMIN)
        self.assertIn('"source_lead_id": payload["source_lead_id"]', ADMIN)
        self.assertIn('"agreement_confirmed_at": now', ADMIN)
        self.assertIn("_normalized_partner_market", ADMIN)
        self.assertIn("An active Premier Partner placement already reserves this category and market.", ADMIN)

    def test_admin_ui_requires_paid_application_and_signed_agreement(self):
        self.assertIn('id="partnerLeadId"', HTML)
        self.assertIn("populatePaidPartnerPlacementLeads", HTML)
        self.assertIn("partner_agreement_status", HTML)
        self.assertIn("Send agreement to SignWell", HTML)
        self.assertIn("support@homeofferflow.com", HTML)
        self.assertIn("No fully onboarded paid applications", HTML)
        self.assertIn("Setup complete", HTML)

    def test_admin_defaults_placement_tier_and_fee_from_paid_selection(self):
        self.assertIn('onchange="applyPartnerPlacementDefaultsFromLead()"', HTML)
        self.assertIn("function partnerPlacementDefaults(preferredModel)", HTML)
        self.assertIn("monthly_placement: { tier: 'premier', fee: 399", HTML)
        self.assertIn("market_exclusive: { tier: 'exclusive_market', fee: 799", HTML)
        self.assertIn("function applyPartnerPlacementDefaultsFromLead()", HTML)
        self.assertIn("data-placement-tier", HTML)

    def test_public_directory_hides_partner_contact_and_agreement_records(self):
        self.assertIn("revoke all on table public.hof_partner_placements from anon, authenticated", PUBLIC_VIEW_MIGRATION)
        self.assertIn("create or replace view public.hof_public_partner_placements", PUBLIC_VIEW_MIGRATION)
        self.assertNotIn("contact_email,", PUBLIC_VIEW_MIGRATION)
        self.assertNotIn("source_lead_id,", PUBLIC_VIEW_MIGRATION)

    def test_legacy_public_view_is_hardened_as_server_only_security_invoker(self):
        hardening = (ROOT / "supabase" / "homeofferflow_partner_public_view_invoker_hardening.sql").read_text(encoding="utf-8")
        self.assertIn("security_invoker = true", hardening)
        self.assertIn("revoke all on table public.hof_public_partner_placements from public, anon, authenticated", hardening)
        self.assertIn("grant select on table public.hof_public_partner_placements to service_role", hardening)
        self.assertNotIn("to anon, authenticated", hardening)


if __name__ == "__main__":
    unittest.main()
