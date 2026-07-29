import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_legacy_table_access_hardening.sql").read_text(
    encoding="utf-8"
)
PRIVATE_BROWSER_TABLES = (
    ROOT / "supabase" / "homeofferflow_private_browser_tables_no_anon.sql"
).read_text(encoding="utf-8")


class LegacyTableAccessHardeningTests(unittest.TestCase):
    def test_legacy_tables_are_not_exposed_to_browser_roles(self):
        self.assertIn("from anon, authenticated", MIGRATION)

        for table_name in (
            "audit_log",
            "documents",
            "help_requests",
            "offer_intakes",
            "offer_invites",
            "offer_terms",
            "offers",
            "parties",
            "payments",
            "sign_requests",
            "transactions",
        ):
            self.assertIn(f"public.{table_name}", MIGRATION)

    def test_private_application_tables_revoke_anon_but_keep_owner_rls_workflows(self):
        self.assertIn("from anon", PRIVATE_BROWSER_TABLES)
        self.assertNotIn("from anon, authenticated", PRIVATE_BROWSER_TABLES)

        for table_name in (
            "hof_agent_profiles",
            "hof_ai_offer_reviews",
            "hof_feedback",
            "hof_investor_profiles",
            "hof_offer_events",
            "hof_offers",
            "hof_seller_leads",
            "hof_usage_events",
        ):
            self.assertIn(f"public.{table_name}", PRIVATE_BROWSER_TABLES)


if __name__ == "__main__":
    unittest.main()
