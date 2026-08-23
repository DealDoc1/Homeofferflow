from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class PaymentFeedbackTests(unittest.TestCase):
    def test_payment_step_has_inline_accessible_status(self):
        self.assertIn('id="paymentActionStatus"', INDEX)
        self.assertIn('function setPaymentStatus(message, type = \'err\')', INDEX)
        self.assertIn('role="status" aria-live="polite"', INDEX)

    def test_payment_validation_and_errors_use_inline_status(self):
        self.assertIn("setPaymentStatus('Please select a plan before continuing.')", INDEX)
        self.assertIn("setPaymentStatus('Payment error: ' +", INDEX)
        self.assertIn("setPaymentStatus('Each signer needs a different email address.')", INDEX)
        self.assertNotIn("alert('Please select a plan before continuing.')", INDEX)
        self.assertNotIn("alert('Payment error: '", INDEX)
        self.assertNotIn("alert('Each signer needs a different email address.')", INDEX)


if __name__ == "__main__":
    unittest.main()
