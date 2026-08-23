import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "index.html").read_text(encoding="utf-8")
SELLERS = (ROOT / "sellers.html").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
VERCEL = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
SEO_GUIDES = {
    "texas-fsbo-guide.html": (
        "Texas FSBO Support",
        "Texas FSBO Planning Guide",
        "https://www.homeofferflow.com/sellers",
    ),
    "texas-agent-offer-workflow.html": (
        "Texas Agent and Broker Workspace",
        "Texas Agent Offer Workflow Guide",
        "https://www.homeofferflow.com/agents",
    ),
    "texas-homebuyer-offer-guide.html": (
        "Texas Homebuyer Offer",
        "Texas Homebuyer Offer Planning Guide",
        "https://www.homeofferflow.com/buyers",
    ),
    "ondemand.html": (
        "Texas Agent and Broker Workspace",
        "OnDemand Realty Agent Launch",
        "https://www.homeofferflow.com/agents",
    ),
    "partners.html": (
        "HomeOfferFlow",
        "Founding Partner Placements",
        "https://www.homeofferflow.com/",
    ),
    "investors.html": (
        "HomeOfferFlow",
        "Texas Investor Offer Workspace",
        "https://www.homeofferflow.com/",
    ),
    "texas-investor-offer-guide.html": (
        "Texas Investor Workspace",
        "Texas Investor Offer Checklist",
        "https://www.homeofferflow.com/investors",
    ),
}


class TechnicalSeoTests(unittest.TestCase):

    def test_homepage_describes_the_brand_and_site_with_valid_structured_data(self):
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', HOME, re.DOTALL
        )
        payloads = [json.loads(block) for block in blocks]
        entries = [entry for payload in payloads for entry in (payload if isinstance(payload, list) else [payload])]
        organization = next(entry for entry in entries if entry.get("@type") == "Organization")
        website = next(entry for entry in entries if entry.get("@type") == "WebSite")
        self.assertEqual(organization["name"], "HomeOfferFlow")
        self.assertEqual(organization["url"], "https://www.homeofferflow.com/")
        self.assertEqual(organization["areaServed"], {"@type": "State", "name": "Texas"})
        self.assertEqual(organization["email"], "support@homeofferflow.com")
        self.assertEqual(organization["contactPoint"]["contactType"], "customer support")
        self.assertEqual(organization["contactPoint"]["email"], "support@homeofferflow.com")
        self.assertEqual(website["publisher"]["@id"], organization["@id"])

    def test_homepage_keeps_google_search_console_verification_available(self):
        self.assertIn(
            '<meta name="google-site-verification" content="ffYNHLPyXQYYPeJLcE-F4KlHlToBu6hMkB23lsYVXSg"',
            HOME,
        )

    def test_sitemap_keeps_revenue_landing_pages_discoverable(self):
        for path in ("/buyers", "/agents", "/investors", "/sellers", "/partners", "/directory"):
            self.assertIn(f"https://www.homeofferflow.com{path}", SITEMAP)

    def test_seller_revenue_paths_expose_a_truthful_offer_catalog(self):
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', SELLERS, re.DOTALL
        )
        catalogs = [json.loads(block) for block in blocks if 'OfferCatalog' in block]
        self.assertEqual(len(catalogs), 1)
        catalog = catalogs[0]
        self.assertEqual(catalog["name"], "HomeOfferFlow Texas FSBO Support Paths")
        offers = {item["name"]: item for item in catalog["itemListElement"]}
        for name, price in (("Free Seller Intake", "0"), ("Seller Prep Plan", "299"), ("FSBO Launch Kit", "499"), ("Flat-Fee MLS Interest", "1299"), ("Seller Offer Review", "599"), ("Contract-to-Close Support", "1999"), ("Premium FSBO Bundle", "2999")):
            with self.subTest(name=name):
                self.assertEqual(offers[name]["price"], price)
                self.assertEqual(offers[name]["priceCurrency"], "USD")
                self.assertIn("scope", offers[name]["description"].lower())

    def test_seller_free_intake_exposes_a_three_step_how_to_path(self):
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>', SELLERS, re.DOTALL
        )
        how_to = next(json.loads(block) for block in blocks if '"HowTo"' in block)
        self.assertEqual(how_to["name"], "Start a Texas FSBO seller plan")
        self.assertEqual([step["position"] for step in how_to["step"]], [1, 2, 3])
        self.assertIn("scope", how_to["step"][-1]["text"].lower())

    def test_sitemap_supplies_verified_lastmod_dates_for_indexable_pages(self):
        entries = re.findall(
            r"<url>\s*<loc>(https://www\.homeofferflow\.com/[^<]*)</loc>\s*<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>\s*</url>",
            SITEMAP,
        )
        self.assertEqual(len(entries), 12)
        self.assertEqual(dict(entries)["https://www.homeofferflow.com/"], "2026-08-22")
        for path in ("/agents", "/ondemand", "/partners", "/buyers", "/sellers", "/texas-fsbo-guide", "/texas-agent-offer-workflow", "/texas-homebuyer-offer-guide", "/texas-investor-offer-guide", "/investors", "/directory"):
            self.assertEqual(dict(entries)[f"https://www.homeofferflow.com{path}"], "2026-08-23")

    def test_revenue_guides_show_and_describe_their_real_site_hierarchy(self):
        for filename, (parent_name, current_name, parent_url) in SEO_GUIDES.items():
            guide = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('aria-label="Breadcrumb"', guide)
            self.assertIn(parent_name, guide)
            self.assertIn(current_name, guide)
            blocks = re.findall(
                r'<script type="application/ld\+json">\s*(.*?)\s*</script>', guide, re.DOTALL
            )
            breadcrumb = next(json.loads(block) for block in blocks if '"BreadcrumbList"' in block)
            items = breadcrumb["itemListElement"]
            self.assertEqual([item["position"] for item in items], list(range(1, len(items) + 1)))
            self.assertGreaterEqual(len(items), 2)
            self.assertEqual(items[-2]["name"], parent_name)
            self.assertEqual(items[-2]["item"], parent_url)
            self.assertEqual(items[-1]["name"], current_name)

    def test_operational_and_private_review_pages_are_not_indexable(self):
        field_mapper = (ROOT / "field-mapper.html").read_text(encoding="utf-8")
        seller_review = (ROOT / "seller-review.html").read_text(encoding="utf-8")
        self.assertIn('<meta name="robots" content="noindex, nofollow, noarchive"', field_mapper)
        self.assertIn('<meta name="robots" content="noindex, nofollow, noarchive, nosnippet"', seller_review)

    def test_api_and_signed_workflow_endpoints_cannot_be_indexed(self):
        api_headers = next(item for item in VERCEL["headers"] if item["source"] == "/api/(.*)")
        self.assertIn(
            {"key": "X-Robots-Tag", "value": "noindex, nofollow, noarchive, nosnippet"},
            api_headers["headers"],
        )


if __name__ == "__main__":
    unittest.main()
