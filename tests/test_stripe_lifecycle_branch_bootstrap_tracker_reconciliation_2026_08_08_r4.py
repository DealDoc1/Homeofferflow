import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT
    / "supabase"
    / "homeofferflow_stripe_lifecycle_branch_bootstrap_tracker_reconciliation_2026_08_08_r4.sql"
).read_text(encoding="utf-8")


class StripeLifecycleBranchBootstrapTrackerR4Tests(unittest.TestCase):
    def test_tracker_records_the_fourth_failed_attempt_without_unlocking_stripe(self):
        self.assertIn("Four approved-cost Supabase branch attempts", SQL)
        self.assertIn("No Stripe test endpoint was created", SQL)
        self.assertIn("Obtain Supabase branch-service diagnostics", SQL)

    def test_update_is_limited_to_tracker_metadata(self):
        lowered = SQL.lower()
        self.assertNotIn("hof_subscriptions", lowered)
        self.assertNotIn("hof_brokerage_members", lowered)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("delete from", lowered)


if __name__ == "__main__":
    unittest.main()
