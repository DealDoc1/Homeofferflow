import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_legacy_table_access_hardening.sql").read_text(
    encoding="utf-8"
)


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


if __name__ == "__main__":
    unittest.main()
