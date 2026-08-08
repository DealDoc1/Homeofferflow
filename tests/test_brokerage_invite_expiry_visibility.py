import unittest
from pathlib import Path


class BrokerageInviteExpiryVisibilityTests(unittest.TestCase):
    def test_server_exposes_expiry_cohorts(self):
        source = Path('api/admin-dashboard.py').read_text()
        self.assertIn('pending_invites_expiring_soon', source)
        self.assertIn('pendingInvitesExpiringSoon', source)
        self.assertIn('pendingInvitesExpired', source)

    def test_ui_uses_camel_case_expiry_and_prompts_resend(self):
        source = Path('index.html').read_text()
        self.assertIn('Invites expiring soon', source)
        self.assertIn('Invitation attention:', source)
        self.assertIn('invite.expiresAt', source)


if __name__ == '__main__':
    unittest.main()
