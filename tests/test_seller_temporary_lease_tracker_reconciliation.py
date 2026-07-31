from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "homeofferflow_seller_temp_lease_tracker_reconciliation.sql"
).read_text()


class SellerTemporaryLeaseTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_matches_the_verified_production_release(self):
        self.assertIn("where slug = 'seller-temporary-lease'", MIGRATION)
        self.assertIn("status = 'production'", MIGRATION)
        self.assertIn("environment = 'production'", MIGRATION)
        self.assertIn("buyer/landlord and seller/tenant execution routing", MIGRATION)
        self.assertIn("approved seller-lease golden regression", MIGRATION)


if __name__ == "__main__":
    unittest.main()
