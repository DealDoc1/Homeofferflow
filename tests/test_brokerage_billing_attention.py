import unittest
from pathlib import Path


class BrokerageBillingAttentionTests(unittest.TestCase):
    def test_billing_attention_is_prioritized_for_active_offer_users(self):
        source = Path('api/admin-dashboard.py').read_text()
        self.assertIn('billing_attention', source)
        self.assertIn('needs_billing', source)
        self.assertIn('Fix billing before the next offer', source)
        self.assertIn('agentsNeedingBilling', source)

    def test_billing_attention_follow_up_is_actionable(self):
        source = Path('index.html').read_text()
        self.assertIn('Action needed to keep your HomeOfferFlow workflow active', source)
        self.assertIn('billing needs attention while you still have offer activity', source)
        self.assertIn('Billing attention', source)


if __name__ == '__main__':
    unittest.main()
