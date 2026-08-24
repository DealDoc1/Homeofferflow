from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "texas-fsbo-closing-checklist.html").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
VERCEL = (ROOT / "vercel.json").read_text(encoding="utf-8")


class TexasFsboClosingChecklistTests(unittest.TestCase):
    def test_page_is_a_clear_under_contract_path_without_overstating_scope(self):
        self.assertIn("Under contract?", PAGE)
        self.assertIn("five-part closing checklist", PAGE)
        self.assertIn("organization aid only", PAGE)
        self.assertIn("brokerage relationship", PAGE)

    def test_checklist_routes_to_the_existing_contract_to_close_interest_path(self):
        self.assertIn("seller_package=contract_help", PAGE)
        self.assertIn("utm_campaign=seller_acquisition", PAGE)
        self.assertIn("Estimate possible proceeds", PAGE)

    def test_page_is_publicly_discoverable_and_available_offline(self):
        path = "/texas-fsbo-closing-checklist"
        self.assertIn(f"https://www.homeofferflow.com{path}", SITEMAP)
        self.assertIn(f"'{path}',", WORKER)
        self.assertIn("homeofferflow-shell-v47", WORKER)
        self.assertIn('"source": "/texas-fsbo-closing-checklist"', VERCEL)
        self.assertIn('"destination": "/texas-fsbo-closing-checklist.html"', VERCEL)


if __name__ == "__main__":
    unittest.main()
