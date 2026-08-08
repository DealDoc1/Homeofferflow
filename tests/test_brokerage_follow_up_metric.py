import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrokerageFollowUpMetricTests(unittest.TestCase):
    def test_dashboard_exposes_follow_up_metric_and_kpi(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"agentsNeedingFollowUp"', backend)
        self.assertIn('agentsNeedingFollowUp || 0', frontend)
        self.assertIn('Needs follow-up', frontend)


if __name__ == "__main__":
    unittest.main()
