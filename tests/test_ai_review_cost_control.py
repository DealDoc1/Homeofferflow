import unittest
from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
API = (Path(__file__).resolve().parents[1] / "api" / "ai-offer-review.py").read_text(encoding="utf-8")


class AiReviewCostControlTests(unittest.TestCase):
    def test_unchanged_offer_reuses_a_recent_review_before_requesting_ai_or_mls_context(self):
        self.assertIn("const AI_REVIEW_REUSE_WINDOW_MS = 10 * 60 * 1000;", HTML)
        self.assertIn("function aiReviewFingerprint(payload)", HTML)
        self.assertIn("function hasReusableAiReview(payload)", HTML)

        start = HTML.index("async function runLiveAiOfferReview()")
        end = HTML.index("function openAiCalibrationFeedback", start)
        review = HTML[start:end]
        self.assertIn("if (hasReusableAiReview(offer))", review)
        self.assertLess(
            review.index("if (hasReusableAiReview(offer))"),
            review.index("fetch('/api/ai-offer-review'"),
        )
        self.assertIn("Change any term to run a new review.", review)
        self.assertIn("state.data._lastAiReviewFingerprint = aiReviewFingerprint(offer);", review)
        self.assertIn("state.data._lastAiReviewCompletedAt = Date.now();", review)

    def test_current_review_button_uses_clear_customer_language(self):
        self.assertIn("reviewIsCurrent ? 'Review is current'", HTML)

    def test_live_ai_review_has_a_schema_appropriate_output_ceiling(self):
        self.assertIn('"maxOutputTokens": 1200,', API)
        self.assertNotIn('"maxOutputTokens": 1500,', API)


if __name__ == "__main__":
    unittest.main()
