import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SubscriptionCheckoutFunnelMetricTests(unittest.TestCase):
    def test_admin_payload_counts_subscription_checkout_events(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"subscriptionCheckoutStartCount"', source)
        self.assertIn('"subscriptionCheckoutReturnCount"', source)
        self.assertIn('"subscriptionCheckoutReturnRate"', source)
        self.assertIn("subscription_checkout_started", source)
        self.assertIn("subscription_checkout_returned", source)

    def test_admin_dashboard_surfaces_subscription_checkout_funnel(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Subscription Checkout Funnel", source)
        self.assertIn("subscriptionCheckoutStartCount", source)
        self.assertIn("subscriptionCheckoutReturnCount", source)
        self.assertIn("subscriptionCheckoutReturnRate", source)


if __name__ == "__main__":
    unittest.main()
