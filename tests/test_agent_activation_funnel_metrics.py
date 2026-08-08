import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")


class AgentActivationFunnelMetricsTests(unittest.TestCase):
    def test_backend_exposes_privacy_limited_activation_gaps(self):
        self.assertIn("agentProfileIncompleteCount", ADMIN)
        self.assertIn("agentWithoutOfferCount", ADMIN)
        self.assertIn("agentOfferWithoutActiveSubscriptionCount", ADMIN)
        self.assertIn("active_agent_subscription_ids", ADMIN)

    def test_admin_dashboard_renders_activation_gaps(self):
        self.assertIn("Agent Activation Gaps", HTML)
        self.assertIn("metrics.agentProfileIncompleteCount", HTML)
        self.assertIn("metrics.agentWithoutOfferCount", HTML)
        self.assertIn("metrics.agentOfferWithoutActiveSubscriptionCount", HTML)


if __name__ == "__main__":
    unittest.main()
