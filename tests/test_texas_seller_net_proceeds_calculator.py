from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "texas-seller-net-proceeds-calculator.html").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class TexasSellerNetProceedsCalculatorTests(unittest.TestCase):
    def test_page_is_private_and_does_not_collect_seller_identity(self):
        self.assertIn("this tool runs in your browser", PAGE)
        self.assertIn("No address, email, login", PAGE)
        self.assertNotIn("fetch(", PAGE)

    def test_calculation_uses_only_seller_entered_estimates(self):
        self.assertIn("const deductions=fields.slice(1).reduce", PAGE)
        self.assertIn("const net=salePrice-deductions", PAGE)
        self.assertIn("transaction-specific and negotiable", PAGE)
        self.assertIn("Planning estimate only", PAGE)

    def test_public_calculator_is_discoverable_and_available_offline(self):
        path = "/texas-seller-net-proceeds-calculator"
        self.assertIn(f"https://www.homeofferflow.com{path}", SITEMAP)
        self.assertIn(f"'{path}',", WORKER)
        self.assertIn("homeofferflow-shell-v46", WORKER)


if __name__ == "__main__":
    unittest.main()
