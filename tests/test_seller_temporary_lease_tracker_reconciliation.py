from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "homeofferflow_seller_temp_lease_tracker_reconciliation.sql"
).read_text()


class SellerTemporaryLeaseTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_never_marks_the_fail_closed_path_as_production(self):
        self.assertIn("where slug = 'seller-temporary-lease'", MIGRATION)
        self.assertIn("status = 'staging_passed'", MIGRATION)
        self.assertIn("environment = 'staging'", MIGRATION)
        self.assertIn("Production adapter still blocks this path", MIGRATION)
        self.assertNotIn("status = 'production'", MIGRATION)


if __name__ == "__main__":
    unittest.main()
