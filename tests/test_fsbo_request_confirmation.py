import pathlib
import unittest


HTML = (pathlib.Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class FsboRequestConfirmationTests(unittest.TestCase):
    def test_fsbo_submission_keeps_a_durable_intake_handoff(self):
        self.assertIn("downloadFsboRequestSummary", HTML)
        self.assertIn("homeofferflow-fsbo-request-summary.txt", HTML)
        self.assertIn("Seller request saved", HTML)
        self.assertIn("confirm scope, provider involvement, availability, and final pricing", HTML)
        self.assertIn("This is an intake record, not checkout", HTML)
        self.assertIn("const fsboNextSteps", HTML)
        self.assertIn("Your next steps:", HTML)
        self.assertIn("Wait for qualified professional review before choosing a contract path.", HTML)

    def test_fsbo_submission_prevents_same_device_duplicate_lead_retries(self):
        self.assertIn('id="fsboSellerSubmit"', HTML)
        self.assertIn("function fsboSubmissionKey(payload)", HTML)
        self.assertIn("sessionStorage.getItem(submissionKey)", HTML)
        self.assertIn("sessionStorage.setItem(submissionKey", HTML)
        self.assertIn("Change the package selection or property details", HTML)

    def test_fsbo_intake_draft_is_preserved_until_submission(self):
        self.assertIn("hof_fsbo_intake_draft_v1", HTML)
        self.assertIn("function saveFsboDraft()", HTML)
        self.assertIn("window.restoreFsboDraft", HTML)
        self.assertIn("clearFsboDraft();", HTML)
        self.assertIn("field?.addEventListener('change', saveFsboDraft)", HTML)

    def test_fsbo_confirmation_keeps_a_privacy_minimized_same_device_receipt(self):
        self.assertIn("hof_fsbo_request_receipt_v1", HTML)
        self.assertIn("function saveFsboRequestReceipt(selected)", HTML)
        self.assertIn("function renderFsboRequestReceipt()", HTML)
        self.assertIn("Seller request saved on this device.", HTML)
        self.assertIn("fsboReceiptMaxAgeMs", HTML)
        self.assertIn("localStorage.removeItem(fsboReceiptStorageKey)", HTML)


if __name__ == "__main__":
    unittest.main()
