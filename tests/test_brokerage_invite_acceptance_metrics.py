import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrokerageInviteAcceptanceMetricsTests(unittest.TestCase):
    def test_brokerage_dashboard_surfaces_aggregate_invite_acceptance(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"inviteAcceptanceRate"', backend)
        self.assertIn('"acceptedInviteActivationRate"', backend)
        self.assertIn('acceptedInviteNeedingActivationCount', backend)
        self.assertIn('inviteAccepted', backend)
        self.assertIn('"acceptedInviteCount"', backend)
        self.assertIn('"inviteTotalCount"', backend)
        self.assertIn('Invite acceptance', frontend)
        self.assertIn('acceptedInviteCount', frontend)

    def test_pending_invites_surface_actionable_acceptance_follow_up(self):
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('First invite follow-up:', frontend)
        self.assertIn('Invite follow-up:', frontend)
        self.assertIn('inviteAcceptanceNotice', frontend)
        self.assertIn('Accepted → active', frontend)
        self.assertIn('Invite accepted', frontend)


if __name__ == "__main__":
    unittest.main()
