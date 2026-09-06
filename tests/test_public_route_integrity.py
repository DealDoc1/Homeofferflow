import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
PUBLIC_FILES = tuple(ROOT.glob("*.html"))


def deployed_routes():
    routes = {"/"}
    for page in PUBLIC_FILES:
        if page.name == "index.html":
            continue
        routes.add(f"/{page.name}")
    for rewrite in CONFIG.get("rewrites", []):
        routes.add(rewrite["source"])
    return routes


class PublicRouteIntegrityTests(unittest.TestCase):
    def test_every_absolute_internal_navigation_link_has_a_deployed_destination(self):
        routes = deployed_routes()
        href_pattern = re.compile(r'<a\\b[^>]*\\bhref=["\'](/[^"\'#?]*)', re.IGNORECASE)
        stale = []

        for page in PUBLIC_FILES:
            content = page.read_text(encoding="utf-8")
            for destination in href_pattern.findall(content):
                if destination.startswith(("/api/", "/assets/")):
                    continue
                if destination not in routes:
                    stale.append(f"{page.name}: {destination}")

        self.assertEqual([], stale, "Public navigation points to missing routes: " + ", ".join(stale))

    def test_all_crawlable_sitemap_pages_have_a_deployed_destination(self):
        routes = deployed_routes()
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        destinations = re.findall(r"https://www\\.homeofferflow\\.com([^<]+)", sitemap)
        missing = [destination for destination in destinations if destination not in routes]

        self.assertEqual([], missing, "Sitemap points to missing routes: " + ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
