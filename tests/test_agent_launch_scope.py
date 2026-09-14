import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AgentLaunchScopeTests(unittest.TestCase):
    def test_dashboard_discloses_a_simple_document_path(self):
        self.assertIn('id="hof-agent-launch-scope-v1"', HTML)
        self.assertIn("Forms available in HomeOfferFlow", HTML)
        self.assertIn("Available now", HTML)
        self.assertIn("Guided documents", HTML)
        self.assertIn("For any document that can be sent for signature, review the completed PDF and confirm every recipient first.", HTML)

    def test_scope_does_not_overstate_signature_availability(self):
        self.assertIn("Every signed-in agent can prepare documents from the shared library.", HTML)
        self.assertIn("For any document that can be sent for signature", HTML)
        self.assertNotIn("Use your approved brokerage process", HTML)
        self.assertIn("and any applicable brokerage process.", HTML)

    def test_scope_keeps_the_catalog_out_of_the_dashboard_summary(self):
        self.assertIn("every signed-in agent", HTML)
        self.assertNotIn("Every signed-in agent can prepare a document from the shared TXR-1501", HTML)
        self.assertIn("See available shared forms", HTML)

    def test_scope_provides_a_dedicated_missing_form_request_path(self):
        self.assertIn("openMissingFormRequest", HTML)
        self.assertIn("Request a Missing Form", HTML)
        self.assertIn("issue.value = 'missing_addendum'", HTML)
        self.assertIn("Do not include confidential client information", HTML)

    def test_appraisal_draft_copy_uses_clear_grammatical_language(self):
        self.assertIn("prepare an appraisal private draft", HTML)
        self.assertNotIn("prepare a appraisal private draft", HTML)


if __name__ == "__main__":
    unittest.main()
