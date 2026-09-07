from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class PurchaseLanguageTests(unittest.TestCase):
    def test_buyer_intake_uses_consistent_purchase_language(self):
        self.assertIn("Who is making this purchase?", HTML)
        self.assertIn("If purchasing with a spouse, partner, or co-investor", HTML)
        self.assertNotIn("Who's buying?", HTML)


if __name__ == "__main__":
    unittest.main()
