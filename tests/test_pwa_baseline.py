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

    def test_public_conversion_pages_keep_the_pwa_brand_chrome_color(self):
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('<meta name="theme-color" content="#173f35"', html)

    def test_public_acquisition_pages_expose_the_installable_manifest(self):
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('rel="manifest" href="/manifest.webmanifest"', html)

    def test_public_acquisition_pages_opt_into_notched_device_safe_areas(self):
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("viewport-fit=cover", html, filename)
            self.assertIn("safe-area-inset-top", html, filename)
            self.assertIn("safe-area-inset-bottom", html, filename)

    def test_public_pages_expose_ios_home_screen_metadata(self):
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html", "404.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('name="apple-mobile-web-app-capable" content="yes"', html, filename)
            self.assertIn('name="apple-mobile-web-app-status-bar-style" content="default"', html, filename)
            self.assertIn('name="apple-mobile-web-app-title" content="HomeOfferFlow"', html, filename)

    def test_public_pages_expose_the_branded_ios_touch_icon(self):
        icon = ROOT / "assets" / "homeofferflow-apple-touch-icon.png"
        self.assertTrue(icon.is_file())
        for filename in ("agents.html", "buyers.html", "sellers.html", "partners.html", "directory.html", "ondemand.html", "investors.html", "texas-fsbo-guide.html", "texas-agent-offer-workflow.html", "texas-homebuyer-offer-guide.html", "texas-investor-offer-guide.html", "texas-agent-form-library.html", "404.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('rel="apple-touch-icon" href="/assets/homeofferflow-apple-touch-icon.png"', html, filename)

    def test_manifest_has_a_standalone_secure_app_shell_configuration(self):
        self.assertEqual(MANIFEST["lang"], "en-US")
        self.assertEqual(MANIFEST["dir"], "ltr")
        self.assertEqual(MANIFEST["display"], "standalone")
        self.assertEqual(MANIFEST["display_override"], ["window-controls-overlay", "standalone", "browser"])
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
                ("Brokerage Setup", "/?pwa_action=brokerage_setup"),
                ("Start a Transaction", "/?pwa_action=transaction_start"),
                ("Lease Workflow", "/?pwa_action=transaction_start&workflow=lease_listing"),
                ("Listing Workflow", "/?pwa_action=transaction_start&workflow=sale_listing"),
                ("Buying Workflow", "/?pwa_action=transaction_start&workflow=purchase"),
                ("Lease Representation", "/?pwa_action=transaction_start&workflow=lease_representation"),
                ("Listing Tools", "/?pwa_action=listing_tools"),
                ("Agent Forms & Drafts", "/?pwa_action=relationship_drafts"),
                ("Texas Form Library", "/texas-agent-form-library?utm_source=pwa_shortcut&utm_medium=installed_app&utm_campaign=agent_form_library"),
                ("Offer Review", "/?pwa_action=offer_review"),
                ("New Offer", "/?pwa_action=new_offer"),
                ("Buyer Offer", "/?pwa_action=buyer_offer"),
                ("Signing Queue", "/?pwa_action=signing_queue"),
                ("Needs Attention", "/?pwa_action=attention_queue"),
                ("Seller Plan", "/?pwa_action=seller_plan"),
                ("FSBO Support Paths", "/sellers?utm_source=pwa_shortcut&utm_medium=installed_app&utm_campaign=fsbo_support_paths"),
                ("Seller Offer Review", "/texas-seller-offer-review?utm_source=pwa_shortcut&utm_medium=installed_app&utm_campaign=seller_offer_review"),
                ("Investor Workspace", "/?pwa_action=investor_workspace"),
                ("Partner Marketplace", "/?pwa_action=partner_marketplace"),
                ("OnDemand Agent Trial", "/ondemand?utm_source=pwa_shortcut&utm_medium=installed_app&utm_campaign=ondemand_agent_trial"),
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

    def test_agent_landing_shell_is_pre_cached_for_agent_first_pwa_resume(self):
        self.assertIn("const SHELL_CACHE = 'homeofferflow-shell-v43';", WORKER)
        self.assertIn("'/agents',", WORKER)
        self.assertIn("'/sellers',", WORKER)
        self.assertIn("'/partners',", WORKER)
        self.assertIn("'/ondemand',", WORKER)
        for path in ("'/buyers',", "'/investors',", "'/directory',", "'/texas-fsbo-guide',", "'/texas-agent-offer-workflow',", "'/texas-homebuyer-offer-guide',", "'/texas-investor-offer-guide',", "'/texas-agent-form-library',"):
            with self.subTest(path=path):
                self.assertIn(path, WORKER)

    def test_worker_refreshes_only_the_public_html_offline_shell(self):
        self.assertIn("if (!cacheKey || !response.ok || !contentType.includes('text/html')) return;", WORKER)
        self.assertIn("event.waitUntil", WORKER)
        self.assertIn("? caches.match(cacheKey).then(response => response || caches.match('/index.html'))", WORKER)
        self.assertIn("cache.put(cacheKey, response.clone())", WORKER)
        self.assertNotIn("cache.put(event.request", WORKER)

    def test_worker_keeps_public_pages_separate_in_the_offline_cache(self):
        for path in ("'/buyers'", "'/agents'", "'/investors'", "'/sellers'", "'/partners'", "'/directory'", "'/ondemand'", "'/texas-fsbo-guide'", "'/texas-agent-offer-workflow'", "'/texas-homebuyer-offer-guide'", "'/texas-investor-offer-guide'", "'/texas-agent-form-library'"):
            self.assertIn(path, WORKER)
        self.assertIn("const cacheKey = PUBLIC_PAGE_PATHS.has(requestUrl.pathname) ? requestUrl.pathname : '';", WORKER)
        self.assertIn("caches.match(cacheKey).then(response => response || caches.match('/index.html'))", WORKER)

    def test_installed_app_shortcuts_use_existing_authenticated_workflows(self):
        self.assertIn('id="hof-pwa-shortcuts-v1"', INDEX)
        shortcut_module = INDEX.split('<script id="hof-pwa-shortcuts-v1">', 1)[1].split('</script>', 1)[0]
        self.assertIn('const root = window;', shortcut_module)
        self.assertIn("root.logOfferEvent?.(", shortcut_module)

    def test_manifest_describes_agent_workspace_and_icons_forms_shortcut(self):
        self.assertIn("shared agent form drafts", MANIFEST["description"])
        self.assertIn("business", MANIFEST.get("categories", []))
        self.assertIn("productivity", MANIFEST.get("categories", []))
        forms = next(item for item in MANIFEST["shortcuts"] if item["name"] == "Agent Forms & Drafts")
        self.assertEqual(forms["icons"][0]["src"], "/assets/homeofferflow-app-icon-192.png")
        self.assertIn("const validActions = new Set(['workspace', 'brokerage_setup', 'transaction_start', 'listing_tools', 'relationship_drafts', 'offer_review', 'new_offer', 'signing_queue', 'attention_queue', 'seller_plan', 'investor_workspace', 'partner_marketplace', 'buyer_offer']);", INDEX)
        self.assertIn("const validTransactionWorkflows = new Set(['purchase', 'sale_listing', 'lease_listing', 'lease_representation']);", INDEX)
        self.assertIn("sessionStorage.setItem('hof_agent_workflow_choice', workflow)", INDEX)
        self.assertIn("if (action === 'transaction_start')", INDEX)
        self.assertIn("if (!validActions.has(action)) return;", INDEX)
        self.assertIn("window.openAuthModal?.(role)", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'dashboard' })", INDEX)
        brokerage = next(item for item in MANIFEST["shortcuts"] if item["name"] == "Brokerage Setup")
        self.assertEqual(brokerage["url"], "/?pwa_action=brokerage_setup")

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


if __name__ == "__main__":
    unittest.main()
