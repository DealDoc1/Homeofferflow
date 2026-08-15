from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class ProfileSavePrivacyTests(unittest.TestCase):
    def test_profile_save_uses_native_email_validation_before_persisting_defaults(self):
        self.assertIn('id="profAgentEmail" type="email" inputmode="email" autocomplete="email"', HTML)
        self.assertIn('id="profInvestorEmail" type="email" inputmode="email" autocomplete="email"', HTML)
        start = HTML.index("async function saveAccountProfile()")
        end = HTML.index("let user = hofAuth.session?.user || null;", start)
        profile_save = HTML[start:end]
        self.assertIn("profileEmailInput?.checkValidity()", profile_save)
        self.assertIn("profileEmailInput.focus();", profile_save)

    def test_profile_save_does_not_log_contact_payloads_to_the_browser_console(self):
        start = HTML.index("async function saveAccountProfile()")
        end = HTML.index("function setInputIfEmpty", start)
        profile_save = HTML[start:end]

        self.assertNotIn("console.log('Saving account profile'", profile_save)
        self.assertNotIn("console.log('Profile saved successfully'", profile_save)
        self.assertIn("setAccountStatus('Profile saved. Your future offers will start with these defaults.'", profile_save)


if __name__ == "__main__":
    unittest.main()
