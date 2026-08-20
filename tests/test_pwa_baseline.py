import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
VERCEL = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))


class PwaBaselineTests(unittest.TestCase):
    def test_html_exposes_install_metadata_and_registers_the_worker(self):
        self.assertIn('rel="manifest" href="/manifest.webmanifest"', INDEX)
        self.assertIn('name="theme-color" content="#173f35"', INDEX)
        self.assertIn('viewport-fit=cover', INDEX)
        self.assertIn("navigator.serviceWorker.register('/service-worker.js'", INDEX)

    def test_manifest_has_a_standalone_secure_app_shell_configuration(self):
        self.assertEqual(MANIFEST["lang"], "en-US")
        self.assertEqual(MANIFEST["dir"], "ltr")
        self.assertEqual(MANIFEST["display"], "standalone")
        self.assertEqual(MANIFEST["orientation"], "portrait-primary")
        self.assertFalse(MANIFEST["prefer_related_applications"])
        self.assertEqual(MANIFEST["start_url"], "/")
        self.assertEqual(MANIFEST["scope"], "/")
        self.assertEqual(MANIFEST["launch_handler"]["client_mode"], ["navigate-existing", "auto"])
        self.assertEqual(MANIFEST["theme_color"], "#173f35")
        self.assertEqual(
            [(item["name"], item["url"]) for item in MANIFEST["shortcuts"]],
            [
                ("My Workspace", "/?pwa_action=workspace"),
                ("New Offer", "/?pwa_action=new_offer"),
                ("Buyer Offer", "/?pwa_action=buyer_offer"),
                ("Signing Queue", "/?pwa_action=signing_queue"),
                ("Seller Plan", "/?pwa_action=seller_plan"),
                ("Find a Provider", "/directory?utm_source=pwa_shortcut&utm_medium=installed_app&utm_campaign=provider_directory"),
            ],
        )
        self.assertTrue(any(icon["src"] == "/assets/homeofferflow-app-icon.svg" for icon in MANIFEST["icons"]))
        self.assertTrue(any(icon["src"] == "/assets/homeofferflow-app-icon-192.png" and icon["sizes"] == "192x192" for icon in MANIFEST["icons"]))
        provider_shortcut = next(item for item in MANIFEST["shortcuts"] if item["name"] == "Find a Provider")
        self.assertEqual(provider_shortcut["icons"][0]["src"], "/assets/homeofferflow-app-icon-192.png")
        self.assertTrue(any(icon["src"] == "/assets/homeofferflow-app-icon-512.png" and icon["sizes"] == "512x512" for icon in MANIFEST["icons"]))
        self.assertIn('rel="apple-touch-icon" href="/assets/homeofferflow-apple-touch-icon.png" sizes="180x180"', INDEX)
        for filename in (
            "homeofferflow-app-icon-192.png",
            "homeofferflow-app-icon-512.png",
            "homeofferflow-apple-touch-icon.png",
        ):
            self.assertTrue((ROOT / "assets" / filename).is_file(), filename)

    def test_worker_does_not_cache_apis_or_authenticated_data(self):
        self.assertIn("requestUrl.pathname.startsWith('/api/')", WORKER)
        self.assertIn("event.request.mode === 'navigate'", WORKER)
        self.assertIn("const PUBLIC_PAGE_PATHS = new Set", WORKER)
        self.assertIn("requestUrl.pathname.startsWith('/api/')", WORKER)
        self.assertIn("contentType.includes('text/html')", WORKER)
        self.assertIn("cache.put(cacheKey, response.clone())", WORKER)
        self.assertNotIn("caches.match(event.request)", WORKER)

    def test_worker_refreshes_only_the_public_html_offline_shell(self):
        self.assertIn("if (!cacheKey || !response.ok || !contentType.includes('text/html')) return;", WORKER)
        self.assertIn("event.waitUntil", WORKER)
        self.assertIn("? caches.match(cacheKey).then(response => response || caches.match('/index.html'))", WORKER)
        self.assertIn("cache.put(cacheKey, response.clone())", WORKER)
        self.assertNotIn("cache.put(event.request", WORKER)

    def test_worker_keeps_public_pages_separate_in_the_offline_cache(self):
        for path in ("'/buyers'", "'/agents'", "'/investors'", "'/sellers'", "'/partners'", "'/directory'", "'/ondemand'", "'/texas-fsbo-guide'", "'/texas-agent-offer-workflow'"):
            self.assertIn(path, WORKER)
        self.assertIn("const cacheKey = PUBLIC_PAGE_PATHS.has(requestUrl.pathname) ? requestUrl.pathname : '';", WORKER)
        self.assertIn("caches.match(cacheKey).then(response => response || caches.match('/index.html'))", WORKER)

    def test_installed_app_shortcuts_use_existing_authenticated_workflows(self):
        self.assertIn('id="hof-pwa-shortcuts-v1"', INDEX)
        shortcut_module = INDEX.split('<script id="hof-pwa-shortcuts-v1">', 1)[1].split('</script>', 1)[0]
        self.assertIn('const root = window;', shortcut_module)
        self.assertIn("root.logOfferEvent?.(", shortcut_module)
        self.assertIn("const validActions = new Set(['workspace', 'new_offer', 'signing_queue', 'seller_plan', 'buyer_offer']);", INDEX)
        self.assertIn("if (!validActions.has(action)) return;", INDEX)
        self.assertIn("window.openAuthModal?.(role)", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'dashboard' })", INDEX)
        self.assertIn("window.startAccountOffer?.()", INDEX)
        self.assertIn("async function openSigningQueue()", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'offers' })", INDEX)
        self.assertIn("window.hofSetOfferWorkspaceFilter?.('signing')", INDEX)
        self.assertIn("window.openFsboSellerModal?.()", INDEX)
        self.assertIn("if (action === 'seller_plan') {", INDEX)
        self.assertIn("trackShortcut(action, 'seller', resumedAfterSignIn);", INDEX)
        self.assertIn("pwa_seller_plan_opened", INDEX)
        self.assertIn("pwa_buyer_offer_opened", INDEX)
        self.assertIn("if (action === 'buyer_offer') {", INDEX)
        self.assertIn("PWA Shortcut Used", INDEX)

    def test_csp_allows_same_origin_service_worker_registration(self):
        csp = next(
            header["value"]
            for entry in VERCEL["headers"]
            for header in entry["headers"]
            if header["key"] == "Content-Security-Policy"
        )
        self.assertIn("worker-src 'self' blob:", csp)


if __name__ == "__main__":
    unittest.main()
