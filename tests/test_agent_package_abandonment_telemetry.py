from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")


class AgentPackageAbandonmentTelemetryTests(unittest.TestCase):
    def test_package_interview_records_only_aggregate_close_context(self):
        self.assertIn("agent_form_package_interview_abandoned", INDEX)
        self.assertIn("agent_form_package_follow_up_abandoned", INDEX)
        self.assertIn("{ workflow: kind, reason }", INDEX)
        self.assertIn("{ workflow: kind, package_type: type, reason }", INDEX)
        self.assertNotIn("property_address", INDEX[INDEX.index("agent_form_package_interview_abandoned"):INDEX.index("agent_form_package_interview_abandoned") + 500])

    def test_dashboard_returns_view_matched_abandonment_counts(self):
        self.assertIn('item.get("event_type") != "agent_form_package_interview_abandoned"', ADMIN)
        self.assertIn('item.get("event_type") != "agent_form_package_follow_up_abandoned"', ADMIN)
        self.assertIn('"agentFormPackageInterviewAbandonedCount": agent_form_package_interview_abandoned_count', ADMIN)
        self.assertIn('"agentFormPackageFollowUpAbandonedCount": agent_form_package_follow_up_abandoned_count', ADMIN)
        self.assertIn("agentFormPackageInterviewAbandonedCount", INDEX)
        self.assertIn("agentFormPackageFollowUpAbandonedCount", INDEX)


if __name__ == "__main__":
    unittest.main()
