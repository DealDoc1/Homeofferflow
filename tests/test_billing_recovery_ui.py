from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BillingRecoveryUiTests(unittest.TestCase):
    def test_past_due_accounts_have_direct_billing_recovery_action(self):
        start = HTML.index("} else if (isBlocked) {")
        end = HTML.index("} else {", start)
        blocked = HTML[start:end]
        self.assertIn("status === 'past_due'", blocked)
        self.assertIn('Fix Billing', blocked)
        self.assertIn('openBillingPortal()', blocked)
        self.assertIn('Update the saved payment method in Stripe Billing', blocked)

    def test_canceled_accounts_keep_reactivation_paths(self):
        start = HTML.index("} else if (isBlocked) {")
        end = HTML.index("} else {", start)
        blocked = HTML[start:end]
        self.assertIn('Reactivate Monthly', blocked)
        self.assertIn('Reactivate Annual', blocked)
        self.assertIn('Your subscription is canceled.', blocked)

    def test_payable_accounts_do_not_offer_duplicate_checkout_reactivation(self):
        start = HTML.index("function renderSubscriptionCard()")
        end = HTML.index("async function openBillingPortal", start)
        subscription = HTML[start:end]
        self.assertIn("const subscriptionReplacementNeeded = status === 'canceled' || status === 'incomplete_expired';", subscription)
        self.assertIn("(subscriptionReplacementNeeded ? '<button class=\"btn-secondary\"", subscription)
        self.assertIn("const billingRecoveryNeeded = status === 'past_due' || status === 'incomplete' || status === 'incomplete_expired' || status === 'unpaid' || status === 'paused';", subscription)

    def test_generation_guard_offers_billing_recovery_at_point_of_failure(self):
        start = HTML.index("async function canGenerateOffer(showAlert = true)")
        end = HTML.index("\n  async function logOfferEvent", start)
        guard = HTML[start:end]
        self.assertIn("Open Manage Billing now?", guard)
        self.assertIn("openBillingPortal('generation_blocked')", guard)
        self.assertIn("openBillingPortal('generation_limit')", guard)


if __name__ == "__main__":
    unittest.main()
