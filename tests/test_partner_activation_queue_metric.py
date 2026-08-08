import unittest
from pathlib import Path


class PartnerActivationQueueMetricTests(unittest.TestCase):
    def test_paid_partner_activation_queue_is_server_derived(self):
        source = Path('api/admin-dashboard.py').read_text()
        self.assertIn('paid_partner_activation_queue', source)
        self.assertIn('paidPartnerActivationQueueCount', source)
        self.assertIn('source_lead_id', source)

    def test_admin_dashboard_surfaces_paid_partner_queue(self):
        source = Path('index.html').read_text()
        self.assertIn('Paid Partner Activation Queue', source)
        self.assertIn('paidPartnerActivationQueueCount', source)


if __name__ == '__main__':
    unittest.main()
