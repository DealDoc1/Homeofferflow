from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class AiOfferReviewClientGuardTests(unittest.TestCase):
    def test_browser_renderer_uses_fixed_product_disclaimer(self):
        start = INDEX.index("function normalizeAiReviewResult(result)")
        end = INDEX.index("function renderAiCleanList", start)
        block = INDEX[start:end]
        self.assertIn("approvedEducationalDisclaimer", block)
        self.assertIn("disclaimer: approvedEducationalDisclaimer", block)
        self.assertNotIn("disclaimer: result.disclaimer ||", block)


if __name__ == "__main__":
    unittest.main()
