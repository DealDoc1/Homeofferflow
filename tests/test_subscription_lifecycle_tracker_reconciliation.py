import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_MIGRATION = (
    ROOT / "supabase" / "homeofferflow_subscription_lifecycle_tracker_reconciliation.sql"
).read_text(encoding="utf-8")
CURRENT_MIGRATION = (
    ROOT
    / "supabase"
    / "homeofferflow_subscription_lifecycle_tracker_reconciliation_2026_08_08.sql"
).read_text(encoding="utf-8")


class SubscriptionLifecycleTrackerReconciliationTests(unittest.TestCase):
    def test_legacy_reconciliation_is_preserved_as_historical_evidence(self):
        self.assertIn("77e787b brokerage billing suspension reason hardening", LEGACY_MIGRATION)
        self.assertIn("requires the next intentional Vercel production deployment", LEGACY_MIGRATION)

    def test_tracker_names_the_released_scheduled_cancellation_qa(self):
        self.assertIn("3abba8d verified production release", CURRENT_MIGRATION)
        self.assertIn("billing suspension", CURRENT_MIGRATION)
        self.assertIn("renewal recovery", CURRENT_MIGRATION)

    def test_tracker_preserves_a_safe_nonproduction_lifecycle_gate(self):
        self.assertIn("dedicated nonproduction Stripe lifecycle run", CURRENT_MIGRATION)
        self.assertIn("never connect Stripe test-mode events to the production webhook endpoint", CURRENT_MIGRATION)
        self.assertIn("where slug = 'subscription-usage-management'", CURRENT_MIGRATION)


if __name__ == "__main__":
    unittest.main()
