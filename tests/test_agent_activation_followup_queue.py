import unittest
from pathlib import Path


class AgentActivationFollowUpQueueTests(unittest.TestCase):
    def test_admin_payload_prioritizes_revenue_and_activation_follow_up(self):
        source = Path('api/admin-dashboard.py').read_text()
        self.assertIn('activation_follow_up_queue', source)
        self.assertIn('Offer created without active access', source)
        self.assertIn('activationFollowUpCount', source)
        self.assertIn('"activationFollowUpQueue": activation_follow_up_queue[:50]', source)
        self.assertIn('activationFollowUpEmailStartCount', source)
        self.assertIn('brokerageActivationFollowUpEmailStartCount', source)
        self.assertIn('partnerFollowUpEmailStartCount', source)

    def test_admin_ui_renders_actionable_queue(self):
        source = Path('index.html').read_text()
        self.assertIn('adminActivationFollowUpAction', source)
        self.assertIn('Activation Follow-up Queue', source)
        self.assertIn('Agent Activation Follow-up', source)
        self.assertIn('Email agent', source)
        self.assertIn('activation_follow_up_email_started', source)
        self.assertIn("surface: 'brokerage'", source)
        self.assertIn('partner_follow_up_email_started', source)


if __name__ == '__main__':
    unittest.main()
