import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_brokerage_admin_preflight_tracker_reconciliation.sql").read_text(encoding="utf-8")


class BrokerageAdminPreflightTrackerTests(unittest.TestCase):
    def test_tracker_records_account_preflight_without_claiming_live_qa(self):
        self.assertIn("active brokerage-admin account", SQL)
        self.assertIn("Authenticated browser QA", SQL)
        self.assertIn("packet/signing propagation", SQL)
        self.assertIn("no named broker is a product gate", SQL.lower())

    def test_tracker_covers_all_brokerage_workspace_items(self):
        for slug in ("admin-dashboard", "broker-dashboard", "brokerage-branding", "team-support"):
            self.assertIn(f"'{slug}'", SQL)


if __name__ == "__main__":
    unittest.main()
