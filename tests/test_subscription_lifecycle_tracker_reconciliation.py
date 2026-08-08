import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "homeofferflow_subscription_lifecycle_tracker_reconciliation.sql"
).read_text(encoding="utf-8")


class SubscriptionLifecycleTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_names_the_released_scheduled_cancellation_qa(self):
        self.assertIn("77e787b brokerage billing suspension reason hardening", MIGRATION)
        self.assertIn("billing suspension", MIGRATION)
        self.assertIn("renewal recovery", MIGRATION)

    def test_tracker_preserves_a_safe_nonproduction_lifecycle_gate(self):
        self.assertIn("dedicated nonproduction Stripe endpoint", MIGRATION)
        self.assertIn("never connect Stripe test-mode events to production", MIGRATION)
        self.assertIn("where slug = 'subscription-usage-management'", MIGRATION)


if __name__ == "__main__":
    unittest.main()
