import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class InvestorWorkspaceFocusTests(unittest.TestCase):
    def test_dashboard_uses_investor_specific_copy_and_hides_agent_picker(self):
        self.assertIn("const isInvestor = roleName === 'Investor';", INDEX)
        self.assertIn("Investor workspace ready", INDEX)
        self.assertIn("Offer preparation for repeat property decisions.", INDEX)
        self.assertIn("Start an offer", INDEX)
        self.assertIn("if (agentPicker) agentPicker.hidden = window.hofAuth?.role === 'investor';", INDEX)
        self.assertIn("Start a guided offer, return to saved work", INDEX)
        self.assertIn("if (String(root.hofAuth?.role || '').toLowerCase() === 'investor') {", INDEX)
        self.assertIn("card.hidden = true;", INDEX)

    def test_installed_app_transaction_shortcut_starts_an_investor_offer(self):
        self.assertIn("if (role === 'investor') {\n        await openNewOfferShortcut(role);", INDEX)
        self.assertIn("if (window.hofAuth?.role === 'investor') {\n        await openNewOfferShortcut('investor');", INDEX)


if __name__ == "__main__":
    unittest.main()
