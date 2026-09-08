import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AgentLaunchScopeTests(unittest.TestCase):
    def test_dashboard_discloses_live_and_non_live_form_scope(self):
        self.assertIn('id="hof-agent-launch-scope-v1"', HTML)
        self.assertIn("Forms available in HomeOfferFlow", HTML)
        self.assertIn("Available now", HTML)
        self.assertIn("Guided forms", HTML)
        self.assertIn("When signature sending is available, you review the completed document and confirm the recipients first.", HTML)

    def test_scope_does_not_overstate_unreleased_agent_form_workflows(self):
        for form_group in (
            "TXR-1501, TXR-1506, TXR-1507, TXR-1508, TXR-1905, TXR-1914, TXR-1917, TXR-1919, TXR-1948, TXR-1953, and TXR-1954 library",
            "Documents outside the current sending scope",
        ):
            self.assertIn(form_group, HTML)
        self.assertIn(
            "Documents outside the current sending scope remain available to prepare and review.",
            HTML,
        )
        self.assertIn(
            "HomeOfferFlow clearly identifies whether a completed document can be sent for signature.",
            HTML,
        )
        self.assertNotIn("Use your approved brokerage process", HTML)

    def test_scope_explains_shared_txr_library_and_private_draft_limit(self):
        self.assertIn("every signed-in agent", HTML)
        for form_code in (
            "TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508", "TXR-1905",
            "TXR-1914", "TXR-1917", "TXR-1919", "TXR-1948", "TXR-1953", "TXR-1954",
        ):
            self.assertIn(form_code, HTML)
        self.assertIn("When signature sending is available, you review the completed document and confirm the recipients first.", HTML)

    def test_scope_provides_a_dedicated_missing_form_request_path(self):
        self.assertIn("openMissingFormRequest", HTML)
        self.assertIn("Request a Missing Form", HTML)
        self.assertIn("issue.value = 'missing_addendum'", HTML)
        self.assertIn("Do not include confidential client information", HTML)


if __name__ == "__main__":
    unittest.main()
