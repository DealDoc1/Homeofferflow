from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_seo_tracker_reconciliation.sql").read_text(encoding="utf-8")


class SeoTrackerReconciliationTests(unittest.TestCase):
    def test_reconciliation_records_verified_production_release(self):
        self.assertIn("where slug = 'seo-hero-update'", SQL)
        self.assertIn("status = 'production'", SQL)
        self.assertIn("environment = 'production'", SQL)
        self.assertIn("qa_status = 'passed'", SQL)
        self.assertIn("current_release = '58784fa Production SEO hero and launch-scope copy", SQL)
        self.assertIn("github_ref = '58784fa'", SQL)
        self.assertIn("completed_at = coalesce(completed_at, now())", SQL)

    def test_reconciliation_does_not_activate_restricted_forms(self):
        self.assertNotIn("hof_brokerage_form_sources", SQL)
        self.assertNotIn("txr_all_agents_authorized = true", SQL)
        self.assertNotIn("authorization_attested = true", SQL)


if __name__ == "__main__":
    unittest.main()
