import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "capture_stripe_lifecycle_snapshot",
    ROOT / "scripts" / "capture_stripe_lifecycle_snapshot.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StripeLifecycleSnapshotTests(unittest.TestCase):
    def test_snapshot_is_aggregate_only_and_tracks_intermediate_states(self):
        snapshot = MODULE.build_snapshot(
            "past_due suspension",
            [
                {"status": "trialing", "trial_ends_at": "2026-09-01T00:00:00Z", "updated_at": "2026-08-09T00:00:00Z"},
                {"status": "past_due", "cancel_at_period_end": True, "cancel_at": "2026-09-15T00:00:00Z"},
            ],
            [
                {"status": "suspended", "suspension_reason": "billing"},
                {"status": "suspended", "suspension_reason": "manual"},
            ],
            [
                {"event_type": "invoice.payment_failed", "livemode": False, "processing_state": "processed", "received_at": "2026-08-09T00:00:00Z"},
            ],
        )
        self.assertEqual(snapshot["checkpoint"], "past_due suspension")
        self.assertEqual(snapshot["subscriptions"]["status_counts"], {"past_due": 1, "trialing": 1})
        self.assertEqual(snapshot["brokerage_memberships"]["suspension_reason_counts"], {"billing": 1, "manual": 1})
        self.assertEqual(snapshot["webhook_ledger"]["processing_state_counts"], {"processed": 1})
        self.assertEqual(snapshot["webhook_ledger"]["event_type_counts"], {"invoice.payment_failed": 1})
        serialized = str(snapshot)
        self.assertNotIn("customer@example.com", serialized)
        self.assertNotIn("sub_", serialized)

    def test_isolation_guard_rejects_production(self):
        from unittest.mock import patch

        env = {
            "SUPABASE_URL": "https://prod.supabase.co",
            "STRIPE_WEBHOOK_TEST_SUPABASE_URL": "https://prod.supabase.co",
            "SUPABASE_PRODUCTION_URL": "https://prod.supabase.co",
            "VERCEL_ENV": "production",
        }
        with patch.dict("os.environ", env, clear=True):
            with self.assertRaises(RuntimeError):
                MODULE._assert_isolated_environment()


if __name__ == "__main__":
    unittest.main()
