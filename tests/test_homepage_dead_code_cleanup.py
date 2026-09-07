import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class HomepageDeadCodeCleanupTests(unittest.TestCase):
    def test_dormant_launch_demo_dashboard_markup_is_not_shipped(self):
        self.assertNotIn("function addDashboardDemoCard()", HTML)
        self.assertNotIn("release15-dashboard-card", HTML)
        self.assertNotIn("beta-safe-banner", HTML)

    def test_active_dashboard_and_feedback_enhancements_remain(self):
        self.assertIn("root.renderAccountDashboard = function renderAccountDashboard()", HTML)
        self.assertIn("function enhanceFeedbackModal()", HTML)
        self.assertIn("feedback-fast-row", HTML)


if __name__ == "__main__":
    unittest.main()
