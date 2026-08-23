from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class PaymentFeedbackTests(unittest.TestCase):
    def test_payment_step_has_inline_accessible_status(self):
        self.assertIn('id="paymentActionStatus"', INDEX)
        self.assertIn('function setPaymentStatus(message, type = \'err\')', INDEX)
        self.assertIn('role="status" aria-live="polite"', INDEX)
        self.assertIn('id="paymentActionStatus" class="platform-status" role="status" aria-live="polite" aria-atomic="true"', INDEX)

    def test_secure_checkout_button_exposes_busy_state_and_restores_after_error(self):
        start = INDEX.index('async function handlePayment()')
        end = INDEX.index('async function generateSubscribedPacket()', start)
        payment = INDEX[start:end]
        self.assertIn("btn.setAttribute('aria-busy', 'true')", payment)
        self.assertIn("btn.setAttribute('aria-disabled', 'true')", payment)
        self.assertIn("btn.setAttribute('aria-busy', 'false')", payment)
        self.assertIn("btn.setAttribute('aria-disabled', 'false')", payment)

    def test_payment_validation_and_errors_use_inline_status(self):
        self.assertIn("setPaymentStatus('Please select a plan before continuing.')", INDEX)
        self.assertIn("setPaymentStatus('Payment error: ' +", INDEX)
        self.assertIn("setPaymentStatus('Each signer needs a different email address.')", INDEX)
        self.assertNotIn("alert('Please select a plan before continuing.')", INDEX)
        self.assertNotIn("alert('Payment error: '", INDEX)
        self.assertNotIn("alert('Each signer needs a different email address.')", INDEX)


if __name__ == "__main__":
    unittest.main()
