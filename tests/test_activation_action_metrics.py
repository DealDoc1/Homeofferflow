import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ActivationActionMetricTests(unittest.TestCase):
    def test_admin_payload_counts_activation_views_and_actions(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"activationDashboardViewCount"', source)
        self.assertIn('"activationActionCount"', source)
        self.assertIn('"activationActionRate"', source)

    def test_admin_dashboard_surfaces_activation_action_rate(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('Activation Action Rate', source)
        self.assertIn('activationActionCount', source)
        self.assertIn('activationDashboardViewCount', source)


if __name__ == "__main__":
    unittest.main()
