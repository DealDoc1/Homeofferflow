import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrokerageInviteAgeVisibilityTests(unittest.TestCase):
    def test_server_exposes_aged_pending_invite_cohort(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("pending_invites_aged", source)
        self.assertIn('"pendingInvitesAged"', source)

    def test_ui_prompts_follow_up_for_aged_invites(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("pendingInvitesAged", source)
        self.assertIn("Invites older than 7 days", source)


if __name__ == "__main__":
    unittest.main()
