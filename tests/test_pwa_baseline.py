import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class PwaBaselineTests(unittest.TestCase):
    def test_html_exposes_install_metadata_and_registers_the_worker(self):
        self.assertIn('rel="manifest" href="/manifest.webmanifest"', INDEX)
        self.assertIn('name="theme-color" content="#173f35"', INDEX)
        self.assertIn("navigator.serviceWorker.register('/service-worker.js'", INDEX)

    def test_manifest_has_a_standalone_secure_app_shell_configuration(self):
        self.assertEqual(MANIFEST["lang"], "en-US")
        self.assertEqual(MANIFEST["dir"], "ltr")
        self.assertEqual(MANIFEST["display"], "standalone")
        self.assertEqual(MANIFEST["orientation"], "portrait-primary")
        self.assertFalse(MANIFEST["prefer_related_applications"])
        self.assertEqual(MANIFEST["start_url"], "/")
        self.assertEqual(MANIFEST["scope"], "/")
        self.assertEqual(MANIFEST["theme_color"], "#173f35")
        self.assertEqual(MANIFEST["icons"][0]["src"], "/assets/homeofferflow-app-icon.svg")

    def test_worker_does_not_cache_apis_or_authenticated_data(self):
        self.assertIn("requestUrl.pathname.startsWith('/api/')", WORKER)
        self.assertIn("event.request.mode === 'navigate'", WORKER)
        self.assertIn("caches.match('/index.html')", WORKER)
        self.assertNotIn("caches.match(event.request)", WORKER)


if __name__ == "__main__":
    unittest.main()
