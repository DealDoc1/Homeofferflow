from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "homeofferflow_seller_temp_lease_tracker_reconciliation.sql"
).read_text()
PRODUCTION_MIGRATION = (
    ROOT / "supabase" / "homeofferflow_seller_temp_lease_production_reconciliation.sql"
).read_text()


class SellerTemporaryLeaseTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_matches_the_verified_production_release(self):
        self.assertIn("where slug = 'seller-temporary-lease'", MIGRATION)
        self.assertIn("status = 'production'", MIGRATION)
        self.assertIn("environment = 'production'", MIGRATION)
        self.assertIn("08272d6 Release seller temporary lease execution", MIGRATION)
        self.assertIn("four-party seller temporary lease SignWell recipient-order coverage", MIGRATION)

    def test_production_reconciliation_matches_completed_release_evidence(self):
        self.assertIn("where slug = 'seller-temporary-lease'", PRODUCTION_MIGRATION)
        self.assertIn("where slug = 'target-seller-temporary-lease'", PRODUCTION_MIGRATION)
        self.assertIn("status = 'production'", PRODUCTION_MIGRATION)
        self.assertIn("environment = 'production'", PRODUCTION_MIGRATION)
        self.assertIn("08272d6 Release seller temporary lease execution", PRODUCTION_MIGRATION)
        self.assertIn("four-party seller temporary lease SignWell recipient-order coverage", PRODUCTION_MIGRATION)


if __name__ == "__main__":
    unittest.main()
