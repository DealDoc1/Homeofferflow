import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_brokerage_ops_tracker_reconciliation.sql").read_text(encoding="utf-8")


class BrokerageOpsTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_covers_team_support_and_broker_dashboard(self):
        self.assertIn("where slug in ('team-support', 'broker-dashboard')", SQL)
        self.assertIn("privacy-limited roster activity", SQL)

    def test_tracker_keeps_authenticated_qa_gate(self):
        self.assertIn("Authenticated production QA", SQL)
        self.assertIn("packet/signing-message propagation", SQL)


if __name__ == "__main__":
    unittest.main()
