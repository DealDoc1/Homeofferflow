import unittest
from pathlib import Path


class SubscriptionRenewalNoticeTests(unittest.TestCase):
    def test_active_subscription_shows_next_renewal_date(self):
        source = Path('index.html').read_text()
        self.assertIn("const renewalDate = formatBillingDate(subscription.current_period_end);", source)
        self.assertIn("subscription-renewal-notice", source)
        self.assertIn("Next renewal:", source)
        self.assertIn("Manage Billing anytime to review or change your plan.", source)


if __name__ == '__main__':
    unittest.main()
