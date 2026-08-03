import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_partner_marketplace_tracker_reconciliation.sql").read_text(encoding="utf-8")


class PartnerMarketplaceTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_reflects_paid_activation_and_the_remaining_commercial_decision(self):
        self.assertIn("where slug = 'partner-marketplace'", SQL)
        self.assertIn("agreement-confirmed placement activation", SQL)
        self.assertIn("Checkout is authoritative for commercial billing", SQL)
        self.assertIn("launch charge is collected at checkout", SQL)
        self.assertIn("renews monthly unless canceled", SQL)
        self.assertIn("written agreement before activation", SQL)


if __name__ == "__main__":
    unittest.main()
