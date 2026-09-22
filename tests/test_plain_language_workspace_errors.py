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

    def test_document_and_brokerage_actions_filter_raw_service_errors(self):
        self.assertIn("const technicalMessage = /(supabase|postgres|database|constraint|column|row-level|", INDEX)
        self.assertIn("root.querySelectorAll?.('.hof-iabs-status.error, .platform-status.err')", INDEX)
        self.assertIn("window.hofSanitizeVisibleErrors?.(root)", INDEX)
        self.assertIn("We couldn’t complete that action. Please try again.", INDEX)

        for raw_display in (
            "status.textContent = error.message || 'Could not prepare the mineral addendum.'",
            "window.announceWorkspaceStatus?.(error.message || 'Signature delivery is temporarily unavailable.')",
            "safe(error.message) + '</div>'",
            "status.textContent = error.message || 'Could not load the signing recipients.'",
            "window.announceWorkspaceStatus?.(error.message || 'Could not download the completed PDF.')",
            "message.textContent = error.message || 'Could not send the seller disclosure for signature.'",
            "platformStatus('aiDashboardStatus', err?.message || 'Could not save AI review snapshot.'",
            "Could not load offer detail: ' + esc(err?.message || err)",
        ):
            self.assertNotIn(raw_display, INDEX)

        for recovery_copy in (
            "We couldn’t prepare the mineral addendum. Please review your answers and try again.",
            "We couldn’t send the signature request. Your document is still saved—please try again.",
            "We couldn’t load the brokerage activity. Refresh and try again.",
            "We couldn’t load the signing recipients. Close this window and try again.",
            "We couldn’t download the completed PDF. Please try again.",
            "We couldn’t send the seller disclosure for signature. Your document is still saved—please try again.",
            "We couldn’t save this offer review. Please try again.",
            "We couldn’t load the offer details. Refresh and try again.",
        ):
            self.assertIn(recovery_copy, INDEX)


if __name__ == "__main__":
    unittest.main()
