import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "SUPABASE_GRAPHQL_EXPOSURE_REVIEW.md").read_text(encoding="utf-8")


class SupabaseGraphqlExposureReviewTests(unittest.TestCase):
    def test_feedback_and_ai_review_are_server_only(self):
        self.assertIn("hof_feedback", DOC)
        self.assertIn("hof_ai_offer_reviews", DOC)
        self.assertIn("server-only", DOC)

    def test_review_preserves_hobby_route_limit(self):
        self.assertIn("Do not deploy this documentation-only review as a Vercel preview", DOC)


if __name__ == "__main__":
    unittest.main()
