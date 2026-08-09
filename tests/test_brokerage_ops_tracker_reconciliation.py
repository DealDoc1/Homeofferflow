import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_brokerage_ops_tracker_reconciliation.sql").read_text(encoding="utf-8")


class BrokerageOpsTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_covers_team_support_and_broker_dashboard(self):
        self.assertIn("where slug in ('team-support', 'broker-dashboard')", SQL)

    def test_team_usage_is_aggregated_without_offer_details(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("hof_usage_events?", source)
        self.assertIn("teamPacketUsage", source)
        self.assertIn("usageBillingMonth", source)
        self.assertIn("Team packets this month", frontend)
        self.assertIn("agent.usage", frontend)
        self.assertIn("privacy-limited roster activity", SQL)

    def test_tracker_keeps_authenticated_qa_gate(self):
        self.assertIn("Authenticated production QA", SQL)
        self.assertIn("packet/signing-message propagation", SQL)


if __name__ == "__main__":
    unittest.main()
