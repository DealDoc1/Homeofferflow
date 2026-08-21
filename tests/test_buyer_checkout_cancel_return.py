import unittest
from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BuyerCheckoutCancelReturnTests(unittest.TestCase):
    def test_cancelled_buyer_checkout_restores_the_saved_payment_step(self):
        self.assertIn("params.get('payment') === 'cancelled'", HTML)
        self.assertIn("const paymentStep = getCurrentSteps().indexOf('step9');", HTML)
        self.assertIn("if (paymentStep >= 0) showStep(paymentStep);", HTML)
        self.assertIn("if (state.selectedPlan && state.selectedPrice) selectPlan", HTML)
        self.assertIn("hofOfferData", HTML)

    def test_cancelled_buyer_checkout_is_clear_and_does_not_auto_charge(self):
        self.assertIn('id="paymentCheckoutReturnNotice"', HTML)
        self.assertIn("Checkout was not completed, and no charge was made.", HTML)
        self.assertIn('id="paymentCheckoutResumeButton"', HTML)
        self.assertIn('onclick="resumeCancelledBuyerCheckout()"', HTML)
        self.assertIn("function resumeCancelledBuyerCheckout()", HTML)
        self.assertIn("Payment Checkout Recovery Selected", HTML)
        self.assertIn("state: 'terms_required'", HTML)
        self.assertIn("state: 'email_required'", HTML)
        self.assertIn("state: 'stripe_restart'", HTML)
        self.assertIn("handlePayment();", HTML)
        self.assertIn("Payment Checkout Cancelled Returned", HTML)
        self.assertIn("window.history.replaceState({}, document.title, cleanUrl);", HTML)

    def test_partner_checkout_return_is_not_routed_to_buyer_payment_success(self):
        self.assertIn("if (params.get('partner_checkout')) return;", HTML)
        self.assertLess(
            HTML.index("if (params.get('partner_checkout')) return;"),
            HTML.index("params.get('payment') === 'cancelled'"),
        )


if __name__ == "__main__":
    unittest.main()
