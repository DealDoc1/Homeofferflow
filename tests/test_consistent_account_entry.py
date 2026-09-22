import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class ConsistentAccountEntryTests(unittest.TestCase):
    def test_global_signed_out_account_action_is_role_neutral(self):
        self.assertIn(
            'id="accountCta" onclick="openAuthModal(state?.data?.userType || \'agent\')">Sign In</button>',
            INDEX,
        )
        self.assertGreaterEqual(INDEX.count("accountCta.textContent = 'Sign In';"), 2)
        self.assertIn("account.textContent = 'Sign In';", INDEX)
        self.assertNotIn("Agent / Broker Login", INDEX)

    def test_initial_dialog_title_includes_every_supported_account_role(self):
        self.assertIn('<h3 id="authTitle">HomeOfferFlow Account</h3>', INDEX)
        self.assertIn('data-auth-role="agent"', INDEX)
        self.assertIn('data-auth-role="broker"', INDEX)
        self.assertIn('data-auth-role="investor"', INDEX)

    def test_customer_actions_use_sign_in_as_the_standard_verb(self):
        self.assertIn("Please sign in before starting a subscription.", INDEX)
        self.assertIn(
            "Please sign in before generating an agent or investor packet.", INDEX,
        )
        self.assertNotIn("Please log in before", INDEX)


if __name__ == "__main__":
    unittest.main()
