from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase/migrations/20260808160000_seller_lead_intake_integrity.sql"
).read_text(encoding="utf-8")
PACKAGE_MIGRATION = (
    ROOT / "supabase/migrations/20260808190000_seller_lead_package_context.sql"
).read_text(encoding="utf-8")
ATTRIBUTION_MIGRATION = (
    ROOT / "supabase/migrations/20260811141707_seller_lead_campaign_attribution.sql"
).read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
API = (ROOT / "api/fsbo-lead.py").read_text(encoding="utf-8")
ADMIN_API = (ROOT / "api/admin-dashboard.py").read_text(encoding="utf-8")


class SellerLeadIntakeIntegrityTests(unittest.TestCase):
    def test_database_constrains_seller_lead_values(self):
        for marker in (
            "hof_seller_leads_seller_type_allowed",
            "hof_seller_leads_status_allowed",
            "hof_seller_leads_property_address_length",
            "hof_seller_leads_seller_name_length",
            "hof_seller_leads_seller_email_length",
            "hof_seller_leads_seller_phone_length",
            "hof_seller_leads_notes_length",
            "hof_seller_leads_amounts_nonnegative",
        ):
            self.assertIn(marker, MIGRATION)
        self.assertIn("alter column property_address set not null", MIGRATION)
        self.assertIn("hof_touch_seller_lead_updated_at", MIGRATION)

    def test_browser_policy_is_authenticated_owner_only(self):
        self.assertIn("to authenticated", MIGRATION)
        self.assertIn("(select auth.uid()) = user_id", MIGRATION)
        self.assertIn("revoke all on function public.hof_touch_seller_lead_updated_at() from public", MIGRATION)

    def test_public_fsbo_path_remains_explicitly_supported(self):
        self.assertIn("'fsbo'", MIGRATION)
        self.assertIn("seller_type: 'fsbo'", INDEX)

    def test_browser_read_does_not_request_unbounded_row_shape(self):
        self.assertIn(
            "select('id,user_id,brokerage_id,seller_type,property_address,seller_name,seller_email,seller_phone,asking_price,mortgage_balance,desired_close_date,notes,status,created_at,updated_at')",
            INDEX,
        )

    def test_package_context_is_persisted_and_admin_follow_up_is_available(self):
        for marker in (
            "property_city",
            "property_county",
            "property_state",
            "property_zip",
            "service_level",
            "package_name",
            "package_price",
            "timeline",
            "partner_categories",
        ):
            self.assertIn(marker, PACKAGE_MIGRATION)
            self.assertIn(marker, API)
            self.assertIn(marker, ADMIN_API)
        self.assertIn("scope == \"seller_leads\"", ADMIN_API)
        self.assertIn("update_seller_lead", ADMIN_API)
        self.assertIn("Seller / FSBO Follow-up Queue", INDEX)
        self.assertIn("admin-contact-action", INDEX)
        self.assertIn("mailto:${encodeURIComponent(email)}", INDEX)
        self.assertIn("tel:${encodeURIComponent(phone)}", INDEX)

    def test_package_context_constraints_are_safe_to_replay_in_a_preview(self):
        self.assertIn("do $$", PACKAGE_MIGRATION)
        self.assertIn("pg_constraint", PACKAGE_MIGRATION)
        for marker in (
            "hof_seller_leads_service_level_length",
            "hof_seller_leads_package_name_length",
            "hof_seller_leads_timeline_length",
            "hof_seller_leads_partner_categories_array",
        ):
            self.assertIn(marker, PACKAGE_MIGRATION)

    def test_campaign_attribution_is_limited_to_standard_utm_fields(self):
        for marker in (
            "source",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
        ):
            self.assertIn(marker, ATTRIBUTION_MIGRATION)
            self.assertIn(marker, API)
            self.assertIn(marker, ADMIN_API)
        self.assertIn("hof_seller_leads_source_allowed", ATTRIBUTION_MIGRATION)
        self.assertIn("hof_seller_leads_source_created_at_idx", ATTRIBUTION_MIGRATION)
        self.assertIn("new URLSearchParams(window.location.search)", INDEX)
        self.assertNotIn("add column if not exists landing_page", ATTRIBUTION_MIGRATION)
        self.assertNotIn("add column if not exists referrer", ATTRIBUTION_MIGRATION)


if __name__ == "__main__":
    unittest.main()
