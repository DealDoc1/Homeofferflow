import unittest
from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BuyerCheckoutReturnConfirmationTests(unittest.TestCase):
    def test_return_url_is_not_treated_as_payment_proof(self):
        self.assertIn("const checkoutReturned =", HTML)
        self.assertIn("showPaymentSuccess(paymentEmail, { checkoutConfirmationPending: true });", HTML)
        self.assertIn("A browser return parameter is not proof of payment", HTML)
        self.assertIn("webhook is the source of truth", HTML)

    def test_return_screen_uses_confirmation_copy_and_keeps_the_draft(self):
        self.assertIn("We’re confirming your checkout", HTML)
        self.assertIn("We’ll email a receipt and your offer packet after payment is confirmed.", HTML)
        self.assertIn("if (!checkoutConfirmationPending)", HTML)
        self.assertIn("copied return URL must not erase a buyer's work", HTML)
        self.assertIn("Payment Checkout Returned", HTML)


if __name__ == "__main__":
    unittest.main()
