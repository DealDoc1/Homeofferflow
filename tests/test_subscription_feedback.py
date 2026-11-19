from pathlib import Path
import subprocess
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class SubscriptionFeedbackTests(unittest.TestCase):
    def test_subscription_checkout_recovery_runtime(self):
        result = subprocess.run(
            ["node", "--test", str(Path(__file__).with_name("subscription_checkout_recovery.runtime.cjs"))],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_subscription_card_exposes_accessible_action_status(self):
        self.assertIn('id="subscriptionActionStatus"', INDEX)
        self.assertIn('role="status" aria-live="polite"', INDEX)
        self.assertIn('id="subscriptionActionStatus" class="platform-status" role="status" aria-live="polite" aria-atomic="true"', INDEX)
        self.assertIn("function setSubscriptionActionStatus(message, type = 'err')", INDEX)
        self.assertIn("function setSubscriptionActionBusy(message)", INDEX)
        self.assertIn("setSubscriptionActionBusy('Opening secure Stripe Checkout…')", INDEX)
        self.assertIn("setSubscriptionActionBusy('Opening secure Stripe Billing…')", INDEX)
        self.assertIn("el.setAttribute('aria-busy', 'true')", INDEX)

    def test_billing_and_checkout_failures_use_inline_status(self):
        self.assertIn("setSubscriptionActionStatus('Could not open billing portal: '", INDEX)
        start = INDEX.index("  async function startSubscriptionCheckout(")
        checkout = INDEX[start:INDEX.index("  function checkSubscriptionReturn(", start)]
        self.assertIn("We couldn’t open subscription checkout.", checkout)
        self.assertIn("We couldn’t check your acceptance of the current terms.", checkout)
        self.assertIn("window.hofCustomerActionError?.(err, fallback) || fallback", checkout)
        self.assertNotIn("alert('Could not open billing portal: '", INDEX)
        self.assertNotIn("alert('Subscription checkout failed: '", INDEX)


if __name__ == "__main__":
    unittest.main()
