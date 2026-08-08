import unittest
from pathlib import Path


class AdminActivationBillingFollowUpTests(unittest.TestCase):
    def test_platform_queue_distinguishes_billing_from_access(self):
        source = Path('api/admin-dashboard.py').read_text()
        self.assertIn('Fix billing before the next offer', source)
        self.assertIn('"category"', source)
        self.assertIn('"billing"', source)
        self.assertIn('"access"', source)

    def test_platform_billing_follow_up_has_manage_billing_guidance(self):
        source = Path('index.html').read_text()
        self.assertIn('Action needed to keep your HomeOfferFlow access active', source)
        self.assertIn('open Manage Billing to update access', source)


if __name__ == '__main__':
    unittest.main()
