from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class DashboardInteractionIdTests(unittest.TestCase):
    def test_dashboard_ai_status_is_distinct_from_the_offer_review_status(self):
        # The inline offer review and account dashboard can both be present in
        # one page. Their save/error messages must never target a shared ID.
        self.assertEqual(HTML.count('id="aiFoundationStatus"'), 1)
        self.assertEqual(HTML.count('id="aiDashboardStatus"'), 1)
        self.assertIn("platformStatus('aiDashboardStatus'", HTML)
        self.assertNotIn("platformStatus('aiFoundationStatus'", HTML)


if __name__ == "__main__":
    unittest.main()
