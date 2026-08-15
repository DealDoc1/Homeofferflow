import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKOUT = (ROOT / "api" / "create-checkout.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class ConsumerCheckoutScopeTests(unittest.TestCase):
    def test_browser_cannot_choose_a_price_or_unfulfilled_review_tier(self):
        self.assertIn("const SELF_SERVE_PLAN = 'self'", CHECKOUT)
        self.assertIn("Only the Self-Serve buyer offer packet is currently available", CHECKOUT)
        self.assertIn("Checkout price is selected by HomeOfferFlow, not the browser", CHECKOUT)
        self.assertNotIn("priceId ||", CHECKOUT)
        self.assertNotIn("priceId ||\n", CHECKOUT)

    def test_checkout_redirects_are_anchored_to_homeofferflow_origins(self):
        self.assertIn("function safeOrigin(req)", CHECKOUT)
        self.assertIn("host === 'www.homeofferflow.com'", CHECKOUT)
        self.assertNotIn("String(successUrl).startsWith('http')", CHECKOUT)
        self.assertIn("const safeSuccessUrl = `${origin}/?payment=success", CHECKOUT)

    def test_consumer_checkout_does_not_advertise_unfulfilled_review_services(self):
        self.assertIn("Self-Serve Buyer Offer Packet", INDEX)
        self.assertIn("does not include an agent, broker, or attorney review service", INDEX)
        self.assertNotIn("Licensed TX agent reviews", INDEX)
        self.assertNotIn("Legal risk assessment", INDEX)
        self.assertNotIn("Full legal coverage", INDEX)

    def test_receipt_email_is_validated_and_focused_before_checkout(self):
        self.assertIn('id="paymentEmail" name="paymentEmail" inputmode="email" autocomplete="email"', INDEX)
        start = INDEX.index("async function handlePayment()")
        end = INDEX.index("sessionStorage.setItem('hofOfferData'", start)
        checkout = INDEX[start:end]
        self.assertIn("paymentEmailInput?.checkValidity()", checkout)
        self.assertIn("paymentEmailInput.focus();", checkout)
        self.assertIn("paymentEmailInput.value = email", checkout)


if __name__ == "__main__":
    unittest.main()
