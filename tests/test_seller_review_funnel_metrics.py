import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SellerReviewFunnelMetricTests(unittest.TestCase):
    def test_authenticated_seller_review_request_logs_aggregate_event(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("seller_review_request_sent", source)
        self.assertIn("sellerCount", source)

    def test_admin_payload_and_card_surface_review_request_count(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"sellerReviewRequestCount"', backend)
        self.assertIn("sellerReviewRequestCount", frontend)
        self.assertIn("seller disclosure review requests initiated", frontend)


if __name__ == "__main__":
    unittest.main()
