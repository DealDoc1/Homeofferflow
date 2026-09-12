import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicFormGuideLanguageTests(unittest.TestCase):
    def test_buyer_representation_guide_uses_review_then_send_language(self):
        guide = (ROOT / "texas-buyer-representation-guide.html").read_text(encoding="utf-8")
        self.assertNotIn("private-review", guide)
        self.assertNotIn("private review draft", guide)
        self.assertNotIn("private ", guide.lower())
        self.assertIn("confirm recipients before sending it for signature", guide)

    def test_seller_financing_guide_uses_review_then_send_language(self):
        guide = (ROOT / "texas-seller-financing-guide.html").read_text(encoding="utf-8")
        self.assertNotIn("private-review", guide)
        self.assertNotIn("private review draft", guide)
        self.assertNotIn("private ", guide.lower())
        self.assertIn("confirm recipients before sending it for signature", guide)
        self.assertIn("does not create loan documents", guide)


if __name__ == "__main__":
    unittest.main()
