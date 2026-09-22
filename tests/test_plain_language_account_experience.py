import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class PlainLanguageAccountExperienceTests(unittest.TestCase):
    def test_account_sign_in_uses_clear_secure_link_language(self):
        self.assertIn("Email My Secure Sign-In Link", INDEX)
        self.assertIn(
            "Secure sign-in link sent. Check your email, then return here to continue.",
            INDEX,
        )
        self.assertNotIn(">Send Magic Link<", INDEX)
        self.assertNotIn("Magic link sent.", INDEX)

    def test_account_sign_in_never_exposes_provider_setup_instructions(self):
        send_start = INDEX.index("async function sendMagicLink()")
        send_end = INDEX.index("function recordAgentLandingAuthStage", send_start)
        send_flow = INDEX[send_start:send_end]

        self.assertIn("window.hofCustomerActionError?.(err, fallback)", send_flow)
        self.assertIn("contact support@homeofferflow.com", send_flow)
        self.assertNotIn("Supabase Auth URL settings", send_flow)
        self.assertNotIn("setAuthStatus(err?.message", send_flow)

    def test_profile_save_keeps_technical_errors_out_of_the_workspace(self):
        save_start = INDEX.index("async function saveAccountProfile()")
        save_end = INDEX.index("function setInputIfEmpty", save_start)
        save_flow = INDEX[save_start:save_end]

        self.assertIn("Your workspace could not connect. Refresh and try again.", save_flow)
        self.assertIn("Your entries are still on this screen.", save_flow)
        self.assertIn("window.hofCustomerActionError?.(err, fallback)", save_flow)
        self.assertNotIn("Supabase did not load", save_flow)
        self.assertNotIn("setAccountStatus(msg", save_flow)

    def test_feedback_confirmation_and_recovery_stay_customer_facing(self):
        submit_start = INDEX.index("async function submitBetaFeedback()")
        submit_end = INDEX.index("function renderBetaOnboardingChecklist", submit_start)
        submit_flow = INDEX[submit_start:submit_end]

        self.assertIn("your feedback is saved securely", submit_flow)
        self.assertIn("Copy your note and email support@homeofferflow.com", submit_flow)
        self.assertNotIn("saved in Supabase", submit_flow)
        self.assertNotIn("Error: ' + (err?.message", submit_flow)


if __name__ == "__main__":
    unittest.main()
