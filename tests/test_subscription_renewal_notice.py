import unittest
from pathlib import Path


class SubscriptionRenewalNoticeTests(unittest.TestCase):
    def test_active_subscription_shows_next_renewal_date(self):
        source = Path('index.html').read_text()
        self.assertIn("const renewalDate = formatBillingDate(subscription.current_period_end);", source)
        self.assertIn("subscription-renewal-notice", source)
        self.assertIn("Next renewal:", source)
        self.assertIn("Manage Billing anytime to review or change your plan.", source)

    def test_renewal_urgency_surfaces_billing_cta_with_distinct_telemetry_source(self):
        source = Path('index.html').read_text()
        self.assertIn("const renewalDaysRemaining", source)
        self.assertIn("const renewalUrgent", source)
        self.assertIn("renewal_urgency", source)
        self.assertIn("Renewal is in", source)

    def test_free_admin_access_never_shows_a_customer_renewal_date(self):
        source = Path('index.html').read_text()
        self.assertIn("const renewalUrgent = status === 'active'", source)
        self.assertIn("if (status === 'active' && !subscription.cancel_at_period_end && renewalDate", source)

    def test_scheduled_cancellation_has_a_recovery_path(self):
        source = Path('index.html').read_text()
        self.assertIn("subscription.cancel_at_period_end", source)
        self.assertIn("Cancellation scheduled.", source)
        self.assertIn("Keep my subscription", source)
        self.assertIn("cancellation_recovery", source)


if __name__ == '__main__':
    unittest.main()
