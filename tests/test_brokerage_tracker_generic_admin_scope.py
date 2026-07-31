import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_brokerage_tracker_generic_admin_scope.sql").read_text(encoding="utf-8")


class BrokerageTrackerGenericAdminScopeTests(unittest.TestCase):
    def test_tracker_uses_generic_brokerage_admin_language(self):
        self.assertIn("any brokerage administrator", SQL)
        self.assertIn("No named broker is a product gate or platform authority", SQL)
        self.assertIn("brokerage administrator", SQL)
        self.assertNotIn("Tyler", SQL)

    def test_tracker_covers_all_brokerage_workspace_items(self):
        for slug in ("admin-dashboard", "broker-dashboard", "brokerage-branding", "team-support"):
            self.assertIn(f"'{slug}'", SQL)


if __name__ == "__main__":
    unittest.main()
