from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class UploadedDisclosureFeedbackTests(unittest.TestCase):
    def test_uploaded_disclosures_have_inline_status_region(self):
        self.assertIn('id="uploadedDocsStatus"', INDEX)
        self.assertIn('function setUploadedDisclosureStatus(message, type = \'err\', action = null)', INDEX)
        self.assertIn('role="status" aria-live="polite"', INDEX)

    def test_upload_validation_uses_inline_status_instead_of_alerts(self):
        self.assertIn("const setStatus = (message, type = 'err') => {", INDEX)
        self.assertIn('setUploadedDisclosureStatus(copy, type, action);', INDEX)
        self.assertIn("setStatus('Only PDF files can be uploaded right now: '", INDEX)
        self.assertIn("setUploadedDisclosureStatus('Review the uploaded PDF labels and order", INDEX)
        self.assertNotIn("alert('Only PDF files can be uploaded right now: '", INDEX)
        self.assertNotIn("alert('Review the uploaded PDF labels and order", INDEX)

    def test_iabs_handoff_offers_a_direct_profile_route_that_saves_and_focuses_the_upload(self):
        self.assertIn("label: 'Open My IABS in Profile'", INDEX)
        self.assertIn("saveDraft();\n          showAccountTab('profile');", INDEX)
        self.assertIn("upload?.focus?.();", INDEX)


if __name__ == "__main__":
    unittest.main()
