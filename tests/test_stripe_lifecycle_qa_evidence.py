import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (ROOT / "docs" / "release-evidence" / "stripe-lifecycle-qa-results-2026-08-08.md").read_text(encoding="utf-8")
AUTOMATED = (ROOT / "docs" / "release-evidence" / "stripe-lifecycle-automated-coverage-2026-08-09.md").read_text(encoding="utf-8")


class StripeLifecycleQaEvidenceTests(unittest.TestCase):
    def test_evidence_identifies_isolated_branch_and_processed_event_types(self):
        self.assertIn("mtalxbxlutkuqcafjsac", EVIDENCE)
        for event_type in (
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.payment_failed",
            "invoice.paid",
        ):
            self.assertIn(event_type, EVIDENCE)

    def test_evidence_does_not_overclaim_completion(self):
        self.assertIn("does not claim that the full", EVIDENCE)
        self.assertIn("runbook is complete", EVIDENCE)
        self.assertIn("Open items before declaring the runbook complete", EVIDENCE)
        self.assertIn("intermediate snapshot", EVIDENCE)

    def test_automated_companion_maps_required_lifecycle_assertions(self):
        self.assertIn("657 tests passing", AUTOMATED)
        for expected in (
            "test_paid_trial_invoice_keeps_current_trialing_status",
            "test_scheduled_cancellation_keeps_access_until_the_saved_end_date",
            "test_recovered_subscription_does_not_undo_manual_broker_suspension",
            "test_webhook_ledger_deduplicates_completed_events_without_storing_event_body",
            "test_production_never_accepts_sandbox_events_even_if_the_flag_is_set",
        ):
            self.assertIn(expected, AUTOMATED)
        self.assertIn("replace a signed Stripe test delivery", AUTOMATED)


if __name__ == "__main__":
    unittest.main()
