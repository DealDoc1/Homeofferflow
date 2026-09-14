import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicLandingSeoTests(unittest.TestCase):
    def test_conversion_pages_keep_their_search_and_share_metadata(self):
        pages = {
            "buyers.html": "https://www.homeofferflow.com/buyers",
            "sellers.html": "https://www.homeofferflow.com/sellers",
            "agents.html": "https://www.homeofferflow.com/agents",
            "investors.html": "https://www.homeofferflow.com/investors",
            "ondemand.html": "https://www.homeofferflow.com/ondemand",
            "partners.html": "https://www.homeofferflow.com/partners",
            "directory.html": "https://www.homeofferflow.com/directory",
        }
        for filename, canonical_url in pages.items():
            with self.subTest(filename=filename):
                source = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn("<title>", source)
                self.assertIn('name="description"', source)
                self.assertIn(f'rel="canonical" href="{canonical_url}"', source)
                self.assertIn('property="og:title"', source)
                self.assertIn('property="og:description"', source)
                self.assertIn('name="twitter:card"', source)

    def test_conversion_pages_are_discoverable_in_the_canonical_sitemap(self):
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        for path in ("buyers", "sellers", "agents", "investors", "ondemand", "partners", "directory"):
            with self.subTest(path=path):
                self.assertIn(f"<loc>https://www.homeofferflow.com/{path}</loc>", sitemap)

