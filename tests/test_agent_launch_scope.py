import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AgentLaunchScopeTests(unittest.TestCase):
    def test_dashboard_discloses_live_and_non_live_form_scope(self):
        self.assertIn('id="hof-agent-launch-scope-v1"', HTML)
        self.assertIn("Forms available in HomeOfferFlow", HTML)
        self.assertIn("Available now", HTML)
        self.assertIn("Not a live signing workflow yet", HTML)

    def test_scope_does_not_overstate_unreleased_agent_form_workflows(self):
        for form_group in (
            "Buyer/tenant representation agreements",
            "listing agreements",
            "seller disclosures",
            "lease-listing and tenant-representation packets",
        ):
            self.assertIn(form_group, HTML)
        self.assertIn(
            "Do not represent a draft-only or unavailable form as generated, sent, or executed",
            HTML,
        )


if __name__ == "__main__":
    unittest.main()
