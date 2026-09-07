import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class CustomerWorkspaceLanguageTests(unittest.TestCase):
    def test_broker_workspace_uses_operating_language_not_build_language(self):
        self.assertIn("<h4>Broker Workspace</h4>", HTML)
        self.assertIn("Use this checklist to set up repeatable broker and team work.", HTML)
        self.assertNotIn("Broker role foundation", HTML)
        self.assertNotIn("before wider broker/team rollout", HTML)

    def test_restricted_form_status_is_clear_without_internal_foundation_jargon(self):
        self.assertIn("available as a private draft only", HTML)
        self.assertNotIn("private-draft foundation", HTML)

    def test_brokerage_profile_uses_finished_product_language(self):
        self.assertIn("<h4>Brokerage Profile</h4>", HTML)
        self.assertIn("Loading brokerage workspace...", HTML)
        self.assertIn("Save Brokerage Profile", HTML)
        self.assertIn("This account can now manage the brokerage workspace.", HTML)
        self.assertNotIn("Brokerage Branding Foundation", HTML)
        self.assertNotIn("foundation build.", HTML)
        self.assertNotIn("Submit Internal Note", HTML)


if __name__ == "__main__":
    unittest.main()
