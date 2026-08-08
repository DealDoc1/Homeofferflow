from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase/migrations/20260808160000_seller_lead_intake_integrity.sql"
).read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


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


if __name__ == "__main__":
    unittest.main()
