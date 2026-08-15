from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class AdminDashboardLayoutTests(unittest.TestCase):
    def test_desktop_account_workspace_has_room_for_operational_views(self):
        self.assertIn(".account-shell { width:min(1120px, 100%);", INDEX)
        self.assertNotIn(".account-shell { width:min(860px, 100%);", INDEX)

    def test_metric_grid_gives_operational_cards_a_readable_minimum_width(self):
        self.assertIn(
            ".admin-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(min(100%, 250px), 1fr));",
            INDEX,
        )
        self.assertNotIn(".admin-grid { display:grid; grid-template-columns:repeat(4, minmax(0,1fr));", INDEX)
        self.assertIn("align-items:start;", INDEX)


if __name__ == "__main__":
    unittest.main()
