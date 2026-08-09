import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ActivationMilestoneMetricTests(unittest.TestCase):
    def test_admin_payload_counts_privacy_safe_activation_milestones(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('agent_activation_milestone_reached', source)
        self.assertIn('activationMilestoneCounts', source)
        self.assertIn('activationFirstOfferRate', source)
        self.assertIn('activationSubscriptionRate', source)

    def test_activation_dashboard_logs_milestones_once_per_session(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('Agent Activation Milestone Reached', source)
        self.assertIn('hof_activation_milestone_', source)
        self.assertIn('first_offer', source)
        self.assertIn('Milestone conversion', source)
        self.assertIn('activationFirstOfferRate', source)
        self.assertIn('activationSubscriptionRate', source)


if __name__ == "__main__":
    unittest.main()
