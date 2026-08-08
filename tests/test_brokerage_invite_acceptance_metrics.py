import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrokerageInviteAcceptanceMetricsTests(unittest.TestCase):
    def test_brokerage_dashboard_surfaces_aggregate_invite_acceptance(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"inviteAcceptanceRate"', backend)
        self.assertIn('"acceptedInviteCount"', backend)
        self.assertIn('"inviteTotalCount"', backend)
        self.assertIn('Invite acceptance', frontend)
        self.assertIn('acceptedInviteCount', frontend)


if __name__ == "__main__":
    unittest.main()
