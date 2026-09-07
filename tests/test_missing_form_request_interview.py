import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class MissingFormRequestInterviewTests(unittest.TestCase):
    def test_missing_form_request_uses_a_short_structured_interview(self):
        self.assertIn('id="missingFormStructuredFields"', HTML)
        self.assertIn('id="missingFormTransaction"', HTML)
        self.assertIn('id="missingFormName"', HTML)
        self.assertIn('What type of transaction is this for?', HTML)
        self.assertIn('Which form or workflow do you need?', HTML)
        self.assertIn('Do not include client names, addresses, MLS numbers, or transaction terms.', HTML)

    def test_submission_keeps_the_existing_feedback_contract_and_normalizes_demand(self):
        self.assertIn("const missingFormTransaction = document.getElementById('missingFormTransaction')?.value || '';", HTML)
        self.assertIn("const missingFormName = document.getElementById('missingFormName')?.value?.trim() || '';", HTML)
        self.assertIn('Form request: ${missingFormName}', HTML)
        self.assertIn('Transaction: ${missingFormTransaction}', HTML)
        self.assertIn('/api/submit-feedback', HTML)
        self.assertIn("issueType === 'missing_addendum' && !missingFormTransaction", HTML)
        self.assertIn("issueType === 'missing_addendum' && !missingFormName", HTML)

    def test_missing_form_shortcut_opens_the_interview(self):
        self.assertIn("syncFeedbackFields();document.getElementById('missingFormTransaction').focus();", HTML)
        self.assertIn('Answer three short questions so we can prioritize the right Texas form or workflow.', HTML)


if __name__ == "__main__":
    unittest.main()
