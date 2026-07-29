from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_brokerage_form_sources.sql").read_text()


class BrokerageFormSourceFoundationTests(unittest.TestCase):
    def test_source_forms_are_private_and_brokerage_scoped(self):
        self.assertIn("create table if not exists public.hof_brokerage_form_sources", MIGRATION)
        self.assertIn("brokerage_id uuid not null", MIGRATION)
        self.assertIn("'brokerage-form-sources'", MIGRATION)
        self.assertIn("public, file_size_limit", MIGRATION)
        self.assertIn("false,", MIGRATION)

    def test_only_reviewed_txr_forms_are_allowed_by_the_initial_catalog(self):
        for form_code in ("TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508"):
            self.assertIn(f"'{form_code}'", MIGRATION)
        self.assertIn("authorization_attested boolean not null default false", MIGRATION)
        self.assertIn("authorized_by_user_id", MIGRATION)
        self.assertIn("authorized_at", MIGRATION)

    def test_agents_cannot_download_source_forms_from_storage(self):
        self.assertIn("hof_brokerage_form_sources_storage_admin_manage", MIGRATION)
        self.assertIn("m.role in ('broker_admin', 'owner')", MIGRATION)
        self.assertIn("Agents never get Storage access", MIGRATION)


if __name__ == "__main__":
    unittest.main()
