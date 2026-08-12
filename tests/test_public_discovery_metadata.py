import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ROBOTS = (ROOT / "robots.txt").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")


class PublicDiscoveryMetadataTests(unittest.TestCase):
    def test_landing_page_has_canonical_share_and_structured_metadata(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/"', INDEX)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/"', INDEX)
        preview_path = ROOT / "assets" / "homeofferflow-social-preview-v1.png"
        preview_url = "https://www.homeofferflow.com/assets/homeofferflow-social-preview-v1.png"
        self.assertTrue(preview_path.is_file())
        self.assertIn(f'property="og:image" content="{preview_url}"', INDEX)
        self.assertIn('property="og:image:width" content="1200"', INDEX)
        self.assertIn('property="og:image:height" content="630"', INDEX)
        self.assertIn('name="twitter:card" content="summary_large_image"', INDEX)
        self.assertIn(f'name="twitter:image" content="{preview_url}"', INDEX)
        self.assertIn('"@type": "SoftwareApplication"', INDEX)
        self.assertIn('"priceCurrency": "USD"', INDEX)

    def test_crawlers_can_discover_the_public_marketing_routes(self):
        self.assertIn('Sitemap: https://www.homeofferflow.com/sitemap.xml', ROBOTS)
        self.assertIn('https://www.homeofferflow.com/', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/ondemand', SITEMAP)


if __name__ == "__main__":
    unittest.main()
