import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
VERCEL = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))


class PwaBaselineTests(unittest.TestCase):
    def test_all_installable_guide_pages_have_consistent_ios_and_worker_support(self):
        for filename in (
            "texas-home-service-partner-guide.html",
            "texas-seller-offer-review.html",
            "texas-lease-offer-workflow.html",
            "texas-listing-workflow.html",
        ):
            with self.subTest(filename=filename):
                html = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn('rel="manifest" href="/manifest.webmanifest"', html)
                self.assertIn('src="/assets/pwa-register.js"', html)
                self.assertIn('name="apple-mobile-web-app-capable" content="yes"', html)
                self.assertIn('name="apple-mobile-web-app-status-bar-style" content="default"', html)
                self.assertIn('name="apple-mobile-web-app-title" content="HomeOfferFlow"', html)
                self.assertIn("safe-area-inset-top", html)
                self.assertIn("safe-area-inset-bottom", html)

    def test_html_exposes_install_metadata_and_registers_the_worker(self):
        self.assertIn('rel="manifest" href="/manifest.webmanifest"', INDEX)
        self.assertIn('name="theme-color" content="#173f35"', INDEX)
        self.assertIn('viewport-fit=cover', INDEX)
        self.assertIn("navigator.serviceWorker.register('/service-worker.js'", INDEX)

    def test_public_conversion_pages_keep_the_pwa_brand_chrome_color(self):
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html", "texas-seller-financing-guide.html", "texas-buyer-representation-guide.html", "texas-flat-fee-mls-guide.html", "texas-seller-net-proceeds-calculator.html", "texas-fsbo-closing-checklist.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('<meta name="theme-color" content="#173f35"', html)

    def test_public_acquisition_pages_expose_the_installable_manifest(self):
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html", "texas-buyer-representation-guide.html", "texas-flat-fee-mls-guide.html", "texas-seller-net-proceeds-calculator.html", "texas-fsbo-closing-checklist.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('rel="manifest" href="/manifest.webmanifest"', html)

    def test_public_acquisition_pages_opt_into_notched_device_safe_areas(self):
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html", "texas-buyer-representation-guide.html", "texas-flat-fee-mls-guide.html", "texas-seller-net-proceeds-calculator.html", "texas-fsbo-closing-checklist.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("viewport-fit=cover", html, filename)
            self.assertIn("safe-area-inset-top", html, filename)
            self.assertIn("safe-area-inset-bottom", html, filename)

    def test_public_pages_expose_ios_home_screen_metadata(self):
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html", "texas-buyer-representation-guide.html", "texas-flat-fee-mls-guide.html", "404.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('name="apple-mobile-web-app-capable" content="yes"', html, filename)
            self.assertIn('name="apple-mobile-web-app-status-bar-style" content="default"', html, filename)
            self.assertIn('name="apple-mobile-web-app-title" content="HomeOfferFlow"', html, filename)

    def test_public_pages_expose_the_branded_ios_touch_icon(self):
        icon = ROOT / "assets" / "homeofferflow-apple-touch-icon.png"
        self.assertTrue(icon.is_file())
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html", "texas-buyer-representation-guide.html", "texas-flat-fee-mls-guide.html", "404.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('rel="apple-touch-icon" href="/assets/homeofferflow-apple-touch-icon.png"', html, filename)

    def test_manifest_has_a_standalone_secure_app_shell_configuration(self):
        self.assertEqual(MANIFEST["lang"], "en-US")
        self.assertEqual(MANIFEST["dir"], "ltr")
        self.assertEqual(MANIFEST["display"], "standalone")
        self.assertEqual(MANIFEST["display_override"], ["window-controls-overlay", "standalone", "browser"])
        self.assertEqual(MANIFEST["orientation"], "any")
        self.assertFalse(MANIFEST["prefer_related_applications"])
        self.assertEqual(MANIFEST["start_url"], "/")
        self.assertEqual(MANIFEST["scope"], "/")
        self.assertEqual(MANIFEST["launch_handler"]["client_mode"], ["navigate-existing", "auto"])
        self.assertEqual(MANIFEST["theme_color"], "#173f35")
        self.assertEqual(
            [(item["name"], item["url"]) for item in MANIFEST["shortcuts"][:4]],
            [
                ("Start a Transaction", "/?pwa_action=transaction_start"),
                ("Investor Workspace", "/?pwa_action=investor_workspace"),
                ("Start Seller Plan", "/?pwa_action=seller_plan"),
                ("Start Buyer Offer", "/?pwa_action=buyer_offer"),
            ],
        )
        self.assertEqual(len(MANIFEST["shortcuts"]), 4)
        self.assertTrue(any(icon["src"] == "/assets/homeofferflow-app-icon.svg" for icon in MANIFEST["icons"]))
        self.assertTrue(any(icon["src"] == "/assets/homeofferflow-app-icon-192.png" and icon["sizes"] == "192x192" for icon in MANIFEST["icons"]))
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

    def test_install_precaches_only_low_cost_app_essentials(self):
        self.assertIn("const SHELL_CACHE = 'homeofferflow-shell-v65';", WORKER)
        shell_assets = WORKER.split('const SHELL_ASSETS = [', 1)[1].split('];', 1)[0]
        self.assertIn("'/manifest.webmanifest'", shell_assets)
        self.assertIn("'/assets/pwa-register.js'", shell_assets)
        self.assertIn("'/assets/pwa-share-target.js'", shell_assets)
        self.assertNotIn("'/agents'", shell_assets)
        self.assertNotIn("'/texas-fsbo-guide'", shell_assets)
        self.assertIn('Public pages cache after the visitor has', WORKER)

    def test_worker_refreshes_only_the_public_html_offline_shell(self):
        self.assertIn("if (!cacheKey || !response.ok || !contentType.includes('text/html')) return;", WORKER)
        self.assertIn("event.waitUntil", WORKER)
        self.assertIn("? caches.match(cacheKey).then(response => response || caches.match('/index.html'))", WORKER)
        self.assertIn("cache.put(cacheKey, response.clone())", WORKER)
        self.assertNotIn("cache.put(event.request", WORKER)

    def test_worker_keeps_public_pages_separate_in_the_offline_cache(self):
        for path in ("'/buyers'", "'/agents'", "'/investors'", "'/sellers'", "'/partners'", "'/directory'", "'/ondemand'", "'/texas-fsbo-guide'", "'/texas-agent-offer-workflow'", "'/texas-homebuyer-offer-guide'", "'/texas-investor-offer-guide'", "'/texas-home-service-partner-guide'", "'/texas-agent-form-library'", "'/texas-seller-financing-guide'", "'/texas-buyer-representation-guide'", "'/texas-flat-fee-mls-guide'", "'/texas-seller-net-proceeds-calculator'", "'/texas-fsbo-closing-checklist'"):
            self.assertIn(path, WORKER)
        self.assertIn("const cacheKey = PUBLIC_PAGE_PATHS.has(requestUrl.pathname) ? requestUrl.pathname : '';", WORKER)
        self.assertIn("caches.match(cacheKey).then(response => response || caches.match('/index.html'))", WORKER)

    def test_every_installable_rewritten_page_is_available_to_the_offline_shell(self):
        for rewrite in VERCEL["rewrites"]:
            source = rewrite["source"]
            destination = rewrite["destination"].lstrip("/")
            html = (ROOT / destination).read_text(encoding="utf-8")
            if "/assets/pwa-register.js" not in html:
                continue
            with self.subTest(path=source):
                self.assertIn(f"'{source}'", WORKER)

    def test_installed_app_shortcuts_use_existing_authenticated_workflows(self):
        self.assertIn('id="hof-pwa-shortcuts-v1"', INDEX)
        shortcut_module = INDEX.split('<script id="hof-pwa-shortcuts-v1">', 1)[1].split('</script>', 1)[0]
        self.assertIn('const root = window;', shortcut_module)
        self.assertIn("root.logOfferEvent?.(", shortcut_module)

    def test_manifest_describes_workspace_and_icons_buyer_offer_shortcut(self):
        self.assertIn("shared agent form drafts", MANIFEST["description"])
        self.assertIn("business", MANIFEST.get("categories", []))
        self.assertIn("productivity", MANIFEST.get("categories", []))
        buyer_offer = next(item for item in MANIFEST["shortcuts"] if item["name"] == "Start Buyer Offer")
        self.assertEqual(buyer_offer["url"], "/?pwa_action=buyer_offer")
        self.assertIn("No payment to begin", buyer_offer["description"])
        self.assertEqual(buyer_offer["icons"][0]["src"], "/assets/homeofferflow-app-icon-192.png")
        self.assertIn("const validActions = new Set(['workspace', 'brokerage_setup', 'transaction_start', 'listing_tools', 'relationship_drafts', 'offer_review', 'new_offer', 'signing_queue', 'attention_queue', 'seller_plan', 'investor_workspace', 'partner_marketplace', 'buyer_offer']);", INDEX)
        self.assertIn("const validTransactionWorkflows = new Set(['purchase', 'sale_listing', 'lease_listing', 'lease_representation']);", INDEX)
        self.assertIn("sessionStorage.setItem('hof_agent_workflow_choice', workflow)", INDEX)
        self.assertIn("if (action === 'transaction_start')", INDEX)
        self.assertIn("if (action === 'buyer_offer')", INDEX)
        self.assertIn("window.beginOfferFrom?.('pwa_buyer_offer');", INDEX)
        self.assertIn("if (!validActions.has(action)) return;", INDEX)
        self.assertIn("window.openAuthModal?.(role)", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'dashboard' })", INDEX)
        self.assertNotIn("Brokerage Setup", [item["name"] for item in MANIFEST["shortcuts"][:4]])

        seller_plan = next(item for item in MANIFEST["shortcuts"] if item["name"] == "Start Seller Plan")
        self.assertEqual(seller_plan["url"], "/?pwa_action=seller_plan")
        self.assertIn("no checkout required", seller_plan["description"])

        investor_workspace = next(item for item in MANIFEST["shortcuts"] if item["name"] == "Investor Workspace")
        self.assertEqual(investor_workspace["url"], "/?pwa_action=investor_workspace")
        self.assertIn("repeat-offer defaults", investor_workspace["description"])

    def test_shortcuts_use_the_branded_app_icon_for_consistent_mobile_launching(self):
        for shortcut in MANIFEST["shortcuts"]:
            with self.subTest(shortcut=shortcut["name"]):
                self.assertTrue(shortcut.get("icons"))
                self.assertEqual(shortcut["icons"][0]["src"], "/assets/homeofferflow-app-icon-192.png")
        self.assertIn("else if (action === 'brokerage_setup') await openBrokerageSetup();", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'brokerage' })", INDEX)
        self.assertIn("'brokerage_setup'", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'seller' })", INDEX)
        self.assertIn("async function openRelationshipDrafts()", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'relationships' })", INDEX)
        self.assertIn("async function openOfferReviewShortcut(role)", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'ai' })", INDEX)
        self.assertIn("else if (action === 'offer_review') await openOfferReviewShortcut(role);", INDEX)
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

    def test_csp_allows_private_pdf_previews_without_arbitrary_frames(self):
        csp = next(
            header["value"]
            for entry in VERCEL["headers"]
            for header in entry["headers"]
            if header["key"] == "Content-Security-Policy"
        )
        directives = {parts[0]: parts[1:] for item in csp.split(";") if (parts := item.split())}
        self.assertEqual(set(directives["frame-src"]), {"'self'", "blob:", "https://js.stripe.com"})


if __name__ == "__main__":
    unittest.main()
