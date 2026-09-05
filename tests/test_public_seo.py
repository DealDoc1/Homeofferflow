import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
ROBOTS = (ROOT / "robots.txt").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
SELLER_PAGE = (ROOT / "sell-your-home.html").read_text(encoding="utf-8")
AGENT_PAGE = (ROOT / "texas-real-estate-agents.html").read_text(encoding="utf-8")
PARTNER_PAGE = (ROOT / "home-services-partners.html").read_text(encoding="utf-8")


class PublicSeoTests(unittest.TestCase):
    def test_homepage_declares_its_canonical_url_and_description(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/" />', HTML)
        self.assertIn('<meta name="description"', HTML)

    def test_homepage_uses_visible_website_structured_data(self):
        self.assertIn('type="application/ld+json"', HTML)
        self.assertIn('"@type": "WebSite"', HTML)
        self.assertIn('"name": "HomeOfferFlow"', HTML)

    def test_robots_points_crawlers_to_the_root_sitemap(self):
        self.assertIn('User-agent: *', ROBOTS)
        self.assertIn('Sitemap: https://www.homeofferflow.com/sitemap.xml', ROBOTS)

    def test_sitemap_lists_absolute_public_urls(self):
        for url in (
            'https://www.homeofferflow.com/',
            'https://www.homeofferflow.com/sell-your-home.html',
            'https://www.homeofferflow.com/texas-real-estate-agents.html',
            'https://www.homeofferflow.com/home-services-partners.html',
            'https://www.homeofferflow.com/terms.html',
            'https://www.homeofferflow.com/privacy.html',
            'https://www.homeofferflow.com/disclaimer.html',
        ):
            with self.subTest(url=url):
                self.assertIn(f'<loc>{url}</loc>', SITEMAP)

    def test_seller_landing_page_is_canonical_and_routes_to_existing_intake(self):
        self.assertIn('rel="canonical" href="https://www.homeofferflow.com/sell-your-home.html"', SELLER_PAGE)
        self.assertIn('href="/?fsbo=1"', SELLER_PAGE)
        self.assertIn('function openFsboIntakeFromUrl()', HTML)
        self.assertIn("params.get('fsbo') !== '1'", HTML)

    def test_homepage_links_humans_to_the_seller_landing_page(self):
        self.assertIn('href="/sell-your-home.html"', HTML)
        self.assertIn('aria-label="Explore HomeOfferFlow FSBO seller support"', HTML)

    def test_agent_landing_page_is_canonical_and_routes_to_the_existing_signup_path(self):
        self.assertIn('rel="canonical" href="https://www.homeofferflow.com/texas-real-estate-agents.html"', AGENT_PAGE)
        self.assertIn('href="/?launch=ondemand"', AGENT_PAGE)
        self.assertIn('Texas real estate agents and brokers', AGENT_PAGE)
        self.assertIn('aria-label="Explore HomeOfferFlow for Texas real estate agents and brokers"', HTML)

    def test_partner_landing_page_is_canonical_and_routes_to_the_existing_application(self):
        self.assertIn('rel="canonical" href="https://www.homeofferflow.com/home-services-partners.html"', PARTNER_PAGE)
        self.assertIn('href="/?partner=1"', PARTNER_PAGE)
        self.assertIn('Texas home-service providers', PARTNER_PAGE)
        self.assertIn('href="/home-services-partners.html"', HTML)


if __name__ == "__main__":
    unittest.main()
