import importlib.util
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "create-subscription-checkout" / "index.py"

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_example")
os.environ.setdefault("STRIPE_AGENT_MONTHLY_PRICE_ID", "price_agent_29_monthly")
os.environ.setdefault("STRIPE_AGENT_ANNUAL_PRICE_ID", "price_agent_annual")
os.environ.setdefault("STRIPE_INVESTOR_MONTHLY_PRICE_ID", "price_investor_monthly")
os.environ.setdefault("STRIPE_INVESTOR_ANNUAL_PRICE_ID", "price_investor_annual")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checkout = load_module("subscription_checkout", MODULE_PATH)


class SubscriptionCheckoutTests(unittest.TestCase):
    def test_ondemand_agent_checkout_requires_card_and_defers_first_invoice(self):
        form = checkout.build_stripe_checkout_form(
            {
                "plan": "agent",
                "billing": "monthly",
                "email": "agent@example.com",
                "userId": "user-1",
                "launch": "ondemand",
            },
            "https://www.homeofferflow.com",
        )

        self.assertEqual(form["line_items[0][price]"], "price_agent_29_monthly")
        self.assertEqual(form["allow_promotion_codes"], "false")
        self.assertEqual(form["payment_method_collection"], "always")
        self.assertEqual(form["subscription_data[trial_period_days]"], "60")
        self.assertEqual(form["metadata[launch]"], "ondemand")
        self.assertEqual(form["subscription_data[metadata][launch]"], "ondemand")

    def test_regular_agent_checkout_keeps_existing_behavior(self):
        form = checkout.build_stripe_checkout_form(
            {"plan": "agent", "billing": "monthly", "email": "agent@example.com"},
            "https://www.homeofferflow.com",
        )

        self.assertEqual(form["line_items[0][price]"], "price_agent_29_monthly")
        self.assertEqual(form["allow_promotion_codes"], "true")
        self.assertNotIn("payment_method_collection", form)
        self.assertNotIn("subscription_data[trial_period_days]", form)

    def test_ondemand_path_cannot_switch_to_annual_or_investor(self):
        with self.assertRaisesRegex(ValueError, "monthly Agent plan"):
            checkout.build_stripe_checkout_form(
                {"plan": "agent", "billing": "annual", "email": "agent@example.com", "launch": "ondemand"},
                "https://www.homeofferflow.com",
            )

        with self.assertRaisesRegex(ValueError, "monthly Agent plan"):
            checkout.build_stripe_checkout_form(
                {"plan": "investor", "billing": "monthly", "email": "investor@example.com", "launch": "ondemand"},
                "https://www.homeofferflow.com",
            )


if __name__ == "__main__":
    unittest.main()
