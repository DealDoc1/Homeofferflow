import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "index.html").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
VERCEL = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))


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
        self.assertEqual(website["publisher"]["@id"], organization["@id"])

    def test_sitemap_keeps_revenue_landing_pages_discoverable(self):
        for path in ("/buyers", "/agents", "/investors", "/sellers", "/partners", "/directory"):
            self.assertIn(f"https://www.homeofferflow.com{path}", SITEMAP)

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
