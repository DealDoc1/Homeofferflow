import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class PlainLanguageWorkspaceErrorTests(unittest.TestCase):
    def test_workspace_actions_do_not_expose_raw_service_errors(self):
        self.assertIn("function platformCustomerError(error, fallback)", INDEX)
        for technical_copy in (
            "Seller leads could not load: ",
            "Offer comparisons could not load: ",
            "Listing workspaces could not load: ",
            "Partners could not load: ",
            "Listing workspace identifier is invalid.",
            "Offer comparison identifier is invalid.",
        ):
            self.assertNotIn(technical_copy, INDEX)

        for recovery_copy in (
            "We couldn’t load your seller list. Refresh the workspace and try again.",
            "We couldn’t load the offer comparisons. Refresh the workspace and try again.",
            "We couldn’t load your listing workspaces. Refresh and try again.",
            "We couldn’t find that listing workspace. Refresh and try again.",
        ):
            self.assertIn(recovery_copy, INDEX)

    def test_buyer_checkout_failure_stays_plain_and_confirms_no_charge_started(self):
        self.assertNotIn("setPaymentStatus('Payment error: ' + (err?.message || err))", INDEX)
        self.assertIn(
            "We couldn’t open secure checkout. No payment was started. Review your details and try again.",
            INDEX,
        )
        self.assertIn("setPaymentStatus(window.hofCustomerActionError?.(err, checkoutFallback)", INDEX)


if __name__ == "__main__":
    unittest.main()
