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

    def test_customer_copy_does_not_require_a_broker_or_mls_connection(self):
        self.assertNotIn("Broker-authorized listing context included.", INDEX)
        self.assertNotIn("When your broker has enabled an approved MLS connection", INDEX)
        self.assertNotIn("includeBrokerMlsContext", INDEX)
        self.assertIn("Confirm live listing facts with the listing side before acting.", INDEX)


if __name__ == "__main__":
    unittest.main()
