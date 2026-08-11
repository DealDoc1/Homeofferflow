from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AiReviewSourceAccuracyTests(unittest.TestCase):
    def test_live_label_requires_a_live_model_source_prefix(self):
        self.assertIn("function aiReviewMode(result)", HTML)
        self.assertIn(".startsWith('gemini')", HTML)
        self.assertIn("aiReviewMode(r) === 'live_ai'", HTML)
        self.assertNotIn("String(r.source || '').includes('gemini')", HTML)

    def test_snapshot_persists_aggregate_safe_review_mode(self):
        self.assertGreaterEqual(HTML.count("reviewMode: aiReviewMode(result)"), 2)
        self.assertIn("aiReviewOutputModeCounts", HTML)


if __name__ == "__main__":
    unittest.main()
