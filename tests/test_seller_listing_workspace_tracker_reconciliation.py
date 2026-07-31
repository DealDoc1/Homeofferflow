from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT
    / "supabase"
    / "homeofferflow_seller_listing_workspace_tracker_reconciliation.sql"
).read_text(encoding="utf-8")


class SellerListingWorkspaceTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_marks_only_the_intake_foundation_active(self):
        self.assertIn("where slug = 'seller-workflow'", SQL)
        self.assertIn("status = 'in_progress'", SQL)
        self.assertIn("environment = 'production'", SQL)
        self.assertIn("Agent-private sale/lease intake", SQL)
        self.assertIn("remain source-gated", SQL)
        self.assertIn("rendered-PDF QA", SQL)
        self.assertNotIn("status = 'production'", SQL)


if __name__ == "__main__":
    unittest.main()
