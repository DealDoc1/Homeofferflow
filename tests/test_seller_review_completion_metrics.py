import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SellerReviewCompletionMetricTests(unittest.TestCase):
    def test_server_records_privacy_safe_review_completion_events(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        for event in ("seller_review_viewed", "seller_review_verified", "seller_review_attested"):
            self.assertIn(event, source)
        self.assertIn("_record_offer_event", source)
        self.assertIn("sellerIndex", source)

    def test_admin_payload_and_card_surface_completion_cohorts(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        for metric in ("sellerReviewViewedCount", "sellerReviewVerifiedCount", "sellerReviewAttestationCount"):
            self.assertIn(f'"{metric}"', backend)
            self.assertIn(metric, frontend)
        for metric in ("sellerReviewViewRate", "sellerReviewVerificationRate", "sellerReviewAttestationRate"):
            self.assertIn(f'"{metric}"', backend)
            self.assertIn(metric, frontend)
        self.assertIn("verified", frontend)
        self.assertIn("attested", frontend)
        self.assertIn("Stage conversion", frontend)


if __name__ == "__main__":
    unittest.main()
