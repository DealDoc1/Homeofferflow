import unittest
from pathlib import Path


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AdminDashboardTimeoutTests(unittest.TestCase):
    def test_stalled_admin_data_request_exits_loading_state_without_mutating_data(self):
        self.assertIn("const controller = new AbortController();", INDEX)
        self.assertIn("window.setTimeout(() => controller.abort(), 15000)", INDEX)
        self.assertIn("signal: controller.signal", INDEX)
        self.assertIn("window.clearTimeout(requestTimeout)", INDEX)
        self.assertIn("Admin dashboard timed out. Refresh to try again; no data was changed.", INDEX)
