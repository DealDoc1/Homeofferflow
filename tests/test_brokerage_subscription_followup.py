import unittest
from pathlib import Path


class BrokerageSubscriptionFollowUpTests(unittest.TestCase):
    def test_brokerage_payload_prioritizes_saved_offer_without_access(self):
        source = Path('api/admin-dashboard.py').read_text()
        self.assertIn('needs_subscription', source)
        self.assertIn('Review access before the next offer', source)
        self.assertIn('agentsNeedingSubscription', source)

    def test_brokerage_follow_up_copy_is_revenue_aware(self):
        source = Path('index.html').read_text()
        self.assertIn("Keep your HomeOfferFlow offer workflow active", source)
        self.assertIn('saved HomeOfferFlow offer but no active access', source)
        self.assertIn('Needs access', source)


if __name__ == '__main__':
    unittest.main()
