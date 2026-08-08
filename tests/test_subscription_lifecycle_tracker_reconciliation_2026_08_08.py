import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT
    / "supabase"
    / "homeofferflow_subscription_lifecycle_tracker_reconciliation_2026_08_08.sql"
).read_text(encoding="utf-8")


class SubscriptionLifecycleTrackerReconciliation20260808Tests(unittest.TestCase):
    def test_tracker_points_to_verified_production_release(self):
        self.assertIn("3abba8d verified production release", SQL)
        self.assertIn("Stripe lifecycle guardrails are deployed", SQL)

    def test_tracker_keeps_nonproduction_event_delivery_gate(self):
        self.assertIn("isolated nonproduction Stripe lifecycle matrix", SQL)
        self.assertIn("never connect Stripe test-mode events to the production webhook endpoint", SQL)
        self.assertIn("where slug = 'subscription-usage-management'", SQL)

    def test_tracker_update_is_metadata_only(self):
        lowered = SQL.lower()
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("hof_subscriptions", lowered)
        self.assertNotIn("hof_brokerage_members", lowered)


if __name__ == "__main__":
    unittest.main()
