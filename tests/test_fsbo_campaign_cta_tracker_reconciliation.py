from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "migrations" / "20260814130000_fsbo_campaign_cta_tracker_reconciliation.sql").read_text(encoding="utf-8")


class FsboCampaignCtaTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_records_the_verified_campaign_copy_release_without_changing_commercial_scope(self):
        self.assertIn("where slug = 'fsbo-workflow'", SQL)
        self.assertIn("a1980c0 production: FSBO campaign CTA package-label alignment", SQL)
        self.assertIn("remain no-checkout intake", SQL)
        self.assertIn("before introducing any paid seller checkout", SQL)


if __name__ == "__main__":
    unittest.main()
