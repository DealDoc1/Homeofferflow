from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class PartnerAdminFeedbackTests(unittest.TestCase):
    def test_partner_revenue_actions_use_workspace_status(self):
        for message in (
            "Could not send the partner agreement.",
            "Could not copy partner setup link.",
            "Could not copy partner setup invitation.",
            "Could not copy partner checkout invitation.",
            "Could not email onboarding access.",
            "Could not update partner lead.",
            "Could not update seller lead.",
        ):
            self.assertIn("window.announceWorkspaceStatus?.(err?.message || '" + message + "')", INDEX)
        self.assertIn("Partner agreement sent through SignWell.", INDEX)

    def test_partner_admin_actions_no_longer_use_browser_alerts(self):
        segment = INDEX[INDEX.index('async function sendPartnerAgreementForSignature'):INDEX.index('function sellerLeadStatusOptions')]
        self.assertNotIn('alert(', segment)
        self.assertIn('window.announceWorkspaceStatus?.(', segment)


if __name__ == "__main__":
    unittest.main()
