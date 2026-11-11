import unittest
from pathlib import Path


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AdminDashboardTimeoutTests(unittest.TestCase):
    def test_stalled_admin_data_request_exits_loading_state_without_mutating_data(self):
        self.assertIn("const controller = new AbortController();", INDEX)
        self.assertIn("window.setTimeout(() => controller.abort(), 30000)", INDEX)
        self.assertIn("signal: controller.signal", INDEX)
        self.assertIn("window.clearTimeout(requestTimeout)", INDEX)
        self.assertIn("Admin dashboard timed out. Refresh to try again; no data was changed.", INDEX)

    def test_timeout_covers_reading_the_dashboard_response_body(self):
        start = INDEX.index("  async function loadAdminDashboard(")
        end = INDEX.index("  async function sendMagicLink(", start)
        loader = INDEX[start:end]
        self.assertLess(loader.index("await response.json()"), loader.index("window.clearTimeout(requestTimeout)"))
        self.assertLess(loader.index("if (controller.signal.aborted)"), loader.index("window.clearTimeout(requestTimeout)"))
