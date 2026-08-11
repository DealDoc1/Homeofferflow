import importlib.util
import os
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "stripe-webhook" / "index.py"


def load_webhook():
    spec = importlib.util.spec_from_file_location("stripe_webhook_role_authority", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StripeSubscriptionRoleAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.webhook = load_webhook()
        os.environ["STRIPE_AGENT_MONTHLY_PRICE_ID"] = "price_agent_monthly"
        os.environ["STRIPE_INVESTOR_MONTHLY_PRICE_ID"] = "price_investor_monthly"

    def test_webhook_uses_price_role_instead_of_mutable_subscription_metadata(self):
        request = self.webhook.handler.__new__(self.webhook.handler)
        request._iso_now = lambda: "2026-08-11T00:00:00+00:00"

        payload, user_id, _, _ = request._extract_subscription_payload({
            "id": "sub-agent",
            "customer": "cus-agent",
            "status": "active",
            "metadata": {"user_id": "user-1", "role": "homebuyer", "plan": "agent"},
            "items": {"data": [{"price": {"id": "price_agent_monthly"}}]},
        })

        self.assertEqual("user-1", user_id)
        self.assertEqual("agent", payload["role"])
        self.assertEqual(10, payload["packet_limit"])

    def test_investor_price_sets_investor_role_even_when_metadata_claims_agent(self):
        request = self.webhook.handler.__new__(self.webhook.handler)
        request._iso_now = lambda: "2026-08-11T00:00:00+00:00"

        payload, _, _, _ = request._extract_subscription_payload({
            "id": "sub-investor",
            "customer": "cus-investor",
            "status": "active",
            "metadata": {"user_id": "user-2", "role": "agent", "plan": "investor"},
            "items": {"data": [{"price": {"id": "price_investor_monthly"}}]},
        })

        self.assertEqual("investor", payload["role"])
        self.assertEqual(15, payload["packet_limit"])


if __name__ == "__main__":
    unittest.main()
