from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BillingRecoveryExtendedStatesTests(unittest.TestCase):
    def test_all_stripe_attention_states_offer_direct_billing_recovery(self):
        self.assertIn("['past_due', 'canceled', 'incomplete', 'incomplete_expired', 'unpaid', 'paused']", HTML)
        self.assertIn("openBillingPortal(\\'billing_recovery\\')", HTML)
        self.assertIn("const billingRecoveryNeeded", HTML)


if __name__ == "__main__":
    unittest.main()
