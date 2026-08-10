import unittest

from scripts.check_production_pwa import validate_manifest, validate_shell, validate_worker


class ProductionPwaCheckTests(unittest.TestCase):
    def test_manifest_requires_installable_shell_metadata(self):
        payload = {
            "display": "standalone",
            "orientation": "portrait-primary",
            "start_url": "/",
            "scope": "/",
            "lang": "en-US",
            "dir": "ltr",
            "prefer_related_applications": False,
            "icons": [
                {"src": "/assets/homeofferflow-app-icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/assets/homeofferflow-app-icon-512.png", "sizes": "512x512", "type": "image/png"},
                {"src": "/assets/homeofferflow-app-icon.svg"},
            ],
        }
        self.assertEqual(validate_manifest(payload), [])

    def test_manifest_reports_missing_or_drifted_values(self):
        failures = validate_manifest({"display": "browser", "icons": []})
        self.assertTrue(any("orientation" in failure for failure in failures))
        self.assertTrue(any("app icon" in failure for failure in failures))

    def test_shell_and_worker_require_safe_entry_points(self):
        self.assertEqual(
            validate_shell('rel="manifest" href="/manifest.webmanifest" navigator.serviceWorker.register(\'/service-worker.js\''),
            [],
        )
        self.assertEqual(
            validate_worker("event.request.mode === 'navigate' caches.match('/index.html') requestUrl.pathname.startsWith('/api/')"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
