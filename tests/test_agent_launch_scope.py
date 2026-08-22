import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AgentLaunchScopeTests(unittest.TestCase):
    def test_dashboard_discloses_live_and_non_live_form_scope(self):
        self.assertIn('id="hof-agent-launch-scope-v1"', HTML)
        self.assertIn("Forms available in HomeOfferFlow", HTML)
        self.assertIn("Available now", HTML)
        self.assertIn("Restricted signing scope", HTML)

    def test_scope_does_not_overstate_unreleased_agent_form_workflows(self):
        for form_group in (
            "TXR-1501, TXR-1506, TXR-1507, and TXR-1508",
            "listing agreements",
            "seller disclosures",
            "lease-listing packets",
        ):
            self.assertIn(form_group, HTML)
        self.assertIn(
            "Do not represent a draft-only or unavailable form as generated, sent, or executed",
            HTML,
        )

    def test_scope_explains_two_level_texas_realtors_authorization_gate(self):
        self.assertIn("brokerage administrator must attest", HTML)
        self.assertIn("each agent must confirm their own current authorization", HTML)
        self.assertIn("never infers membership from a license number alone", HTML)

    def test_scope_provides_a_dedicated_missing_form_request_path(self):
        self.assertIn("openMissingFormRequest", HTML)
        self.assertIn("Request a Missing Form", HTML)
        self.assertIn("issue.value = 'missing_addendum'", HTML)
        self.assertIn("Do not include confidential client information", HTML)


if __name__ == "__main__":
    unittest.main()
