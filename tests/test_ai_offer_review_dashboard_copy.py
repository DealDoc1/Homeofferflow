import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AiOfferReviewDashboardCopyTests(unittest.TestCase):
    def test_dashboard_describes_the_available_review_without_overclaiming(self):
        self.assertIn("The offer workspace uses the live review when it is available", INDEX_HTML)
        self.assertIn("automatically falls back to the rules-based review", INDEX_HTML)
        self.assertIn("Neither result is legal advice, broker advice, a valuation opinion, or a guarantee of acceptance.", INDEX_HTML)

    def test_dashboard_no_longer_calls_live_review_a_future_placeholder(self):
        self.assertNotIn("placeholder shell for the future Gemini-powered offer score", INDEX_HTML)
        self.assertNotIn("Placeholder score only. This does not call AI yet", INDEX_HTML)
        self.assertIn(">Save Review Snapshot<", INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
