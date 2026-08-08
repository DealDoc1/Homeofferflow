from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT / "supabase/migrations/20260808162000_reconcile_seller_intake_tracker.sql"
).read_text(encoding="utf-8")


class SellerIntakeTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_keeps_seller_execution_gated(self):
        self.assertIn("where slug in ('seller-workflow', 'fsbo-workflow')", SQL)
        self.assertIn("status = 'in_progress'", SQL)
        self.assertIn("environment = 'production'", SQL)
        self.assertIn("Seller disclosure, listing agreement, and lease-listing execution remain source-gated", SQL)
        self.assertIn("completed-signature visual QA", SQL)
        self.assertNotIn("status = 'production'", SQL)


if __name__ == "__main__":
    unittest.main()
