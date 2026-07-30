import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_partner_marketplace_tracker_reconciliation.sql").read_text(encoding="utf-8")


class PartnerMarketplaceTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_reflects_paid_activation_and_the_remaining_commercial_decision(self):
        self.assertIn("where slug = 'partner-marketplace'", SQL)
        self.assertIn("agreement-confirmed placement activation", SQL)
        self.assertIn("checkout starts the 90-day trial and auto-renewal", SQL)
        self.assertIn("placement-live start and separate written renewal", SQL)


if __name__ == "__main__":
    unittest.main()
