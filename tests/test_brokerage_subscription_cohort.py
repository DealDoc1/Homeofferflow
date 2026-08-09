import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrokerageSubscriptionCohortTests(unittest.TestCase):
    def test_accepted_invite_subscription_cohort_is_server_derived(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("accepted_invite_subscribed_count", backend)
        self.assertIn('"acceptedInviteSubscriptionRate"', backend)
        self.assertIn("Accepted → subscribed", frontend)
        self.assertIn("acceptedInviteSubscribedCount", frontend)


if __name__ == "__main__":
    unittest.main()
