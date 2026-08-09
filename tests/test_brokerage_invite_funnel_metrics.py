import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrokerageInviteFunnelMetricTests(unittest.TestCase):
    def test_invite_send_and_resend_events_are_privacy_safe(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("brokerage_invite_sent", source)
        self.assertIn("isResend", source)
        self.assertIn("role: 'agent'", source)

    def test_admin_payload_and_card_surface_invite_funnel(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"brokerageInviteSentCount"', backend)
        self.assertIn('"brokerageInviteResendCount"', backend)
        self.assertIn("Brokerage Invites Sent", frontend)
        self.assertIn("brokerageInviteResendCount", frontend)


if __name__ == "__main__":
    unittest.main()
