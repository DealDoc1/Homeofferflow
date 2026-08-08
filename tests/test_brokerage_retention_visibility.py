import pathlib
import unittest


HTML = (pathlib.Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BrokerageRetentionVisibilityTests(unittest.TestCase):
    def test_broker_dashboard_surfaces_activity_and_billing_window(self):
        self.assertIn("function brokerageAgentDate", HTML)
        self.assertIn("function brokerageAgentBillingWindow", HTML)
        self.assertIn("Plan / renewal", HTML)
        self.assertIn("Last activity", HTML)
        self.assertIn("agent.activity?.lastOfferAt", HTML)
        self.assertIn("agent.trialEndsAt", HTML)


if __name__ == "__main__":
    unittest.main()
