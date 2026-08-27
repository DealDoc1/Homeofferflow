from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "texas-seller-net-proceeds-calculator.html").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
VERCEL = (ROOT / "vercel.json").read_text(encoding="utf-8")
SELLERS = (ROOT / "sellers.html").read_text(encoding="utf-8")
FSBO_GUIDE = (ROOT / "texas-fsbo-guide.html").read_text(encoding="utf-8")


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
        self.assertIn("homeofferflow-shell-v51", WORKER)
        self.assertIn('"source": "/texas-seller-net-proceeds-calculator"', VERCEL)
        self.assertIn('"destination": "/texas-seller-net-proceeds-calculator.html"', VERCEL)

    def test_seller_journey_links_to_the_calculator_without_adding_an_intake_gate(self):
        self.assertIn("Estimate possible proceeds first", SELLERS)
        self.assertIn("private seller proceeds worksheet", FSBO_GUIDE)
        self.assertIn("utm_campaign=seller_planning", SELLERS)
        self.assertIn("utm_campaign=seller_planning", FSBO_GUIDE)

    def test_primary_calculator_cta_preserves_the_free_intake_and_opens_it_directly(self):
        self.assertIn(
            '/?seller=1&amp;seller_package=free_intake&amp;utm_source=texas_seller_net_proceeds_calculator',
            PAGE,
        )
        self.assertNotIn("seller_package=free_seller_intake", PAGE)

    def test_seller_question_one_routes_by_stage_without_commitment(self):
        self.assertIn('id="seller-question-one"', SELLERS)
        for label, package in (
            ("Still getting ready", "free_intake"),
            ("Ready to launch", "launch_kit"),
            ("I need MLS visibility", "flat_fee_mls"),
            ("I have an offer", "offer_review"),
        ):
            self.assertIn(label, SELLERS)
            self.assertIn(f"seller_package={package}", SELLERS)
        self.assertIn("no choice creates a listing, service order, or payment", SELLERS)


if __name__ == "__main__":
    unittest.main()
