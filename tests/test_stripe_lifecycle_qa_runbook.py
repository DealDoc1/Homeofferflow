import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = (ROOT / "docs" / "STRIPE_LIFECYCLE_QA.md").read_text(encoding="utf-8")


class StripeLifecycleQaRunbookTests(unittest.TestCase):
    def test_runbook_requires_distinct_nonproduction_database(self):
        self.assertIn("STRIPE_WEBHOOK_TEST_SUPABASE_URL", RUNBOOK)
        self.assertIn("SUPABASE_PRODUCTION_URL", RUNBOOK)
        self.assertIn("is different from `SUPABASE_URL`", RUNBOOK)
        self.assertIn("Do not set these test-event variables on a production Vercel deployment", RUNBOOK)

    def test_runbook_covers_each_billing_lifecycle_and_idempotency(self):
        for event in (
            "checkout.session.completed",
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.paid",
            "invoice.payment_succeeded",
            "invoice.payment_failed",
        ):
            self.assertIn(event, RUNBOOK)
        self.assertIn("Resend a previously processed Stripe event", RUNBOOK)
        self.assertIn("remains `trialing`", RUNBOOK)
        self.assertIn("`past_due`", RUNBOOK)
        self.assertIn("`canceled`", RUNBOOK)

    def test_runbook_requires_trial_checkout_and_cleanup_evidence(self):
        for phrase in (
            "Card is collected; $0 is due today",
            "future $29/month renewal is disclosed",
            "Remove the Stripe test endpoint",
            "Delete or pause the isolated Supabase branch",
        ):
            self.assertIn(phrase, RUNBOOK)

    def test_runbook_uses_full_test_dependencies_for_lifecycle_guard(self):
        self.assertIn("python3", RUNBOOK)
        self.assertIn("tests.test_subscription_lifecycle_security", RUNBOOK)
        self.assertNotIn("PYTHONPATH=/private/tmp/hof_httpx_only", RUNBOOK)


if __name__ == "__main__":
    unittest.main()
