import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ROBOTS = (ROOT / "robots.txt").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
PARTNERS = (ROOT / "partners.html").read_text(encoding="utf-8")
SELLERS = (ROOT / "sellers.html").read_text(encoding="utf-8")
DIRECTORY = (ROOT / "directory.html").read_text(encoding="utf-8")


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
        self.assertIn('https://www.homeofferflow.com/partners.html', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/sellers.html', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/directory.html', SITEMAP)

    def test_partner_acquisition_page_has_share_metadata_and_a_direct_application_path(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/partners.html"', PARTNERS)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/partners.html"', PARTNERS)
        self.assertIn('"@type":"Service"', PARTNERS)
        self.assertIn('href="/?partner=1"', PARTNERS)
        self.assertIn("const allowed = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content'];", PARTNERS)
        self.assertIn("link.href = '/?partner=1&' + campaign.toString();", PARTNERS)
        self.assertIn('not a referral or a required provider choice', PARTNERS)
        self.assertIn('href="/partners.html">Become a Founding Partner</a>', INDEX)

    def test_seller_acquisition_page_is_indexable_and_routes_to_the_existing_safe_intake(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/sellers.html"', SELLERS)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/sellers.html"', SELLERS)
        self.assertIn('"@type":"Service"', SELLERS)
        self.assertIn('href="/?seller=1"', SELLERS)
        self.assertIn("const allowed = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content'];", SELLERS)
        self.assertIn("link.href = '/?seller=1&' + campaign.toString();", SELLERS)
        self.assertIn('This is an intake—not checkout or a service order.', SELLERS)
        self.assertIn('href="/sellers.html">FSBO Seller Support</a>', INDEX)

    def test_public_directory_uses_only_the_existing_safe_directory_endpoint(self):
        self.assertIn('href="https://www.homeofferflow.com/directory.html"', DIRECTORY)
        self.assertIn("fetch('/api/fsbo-lead?'+q)", DIRECTORY)
        self.assertIn("partner_directory:'1'", DIRECTORY)
        self.assertIn('No active HomeOfferFlow provider profiles', DIRECTORY)
        self.assertIn('href="/directory.html">Find a Provider</a>', INDEX)


if __name__ == "__main__":
    unittest.main()
