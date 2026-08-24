from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / 'assets' / 'pwa-register.js').read_text(encoding='utf-8')
PUBLIC_PAGES = (
    'directory.html', 'buyers.html', 'partners.html', 'sellers.html',
    'agents.html', 'investors.html', 'texas-fsbo-guide.html',
    'texas-agent-offer-workflow.html', 'texas-seller-offer-review.html', 'texas-homebuyer-offer-guide.html', 'ondemand.html'
)


class PublicPwaRegistrationTests(unittest.TestCase):
    def test_public_discovery_pages_register_the_shared_low_cost_app_shell(self):
        for filename in PUBLIC_PAGES:
            with self.subTest(filename=filename):
                html = (ROOT / filename).read_text(encoding='utf-8')
                self.assertIn('/assets/pwa-register.js', html)

    def test_registration_uses_root_scope_without_third_party_dependencies(self):
        script = (ROOT / 'assets' / 'pwa-register.js').read_text(encoding='utf-8')
        self.assertIn("navigator.serviceWorker.register('/service-worker.js', { scope: '/' })", script)
        self.assertIn("beforeinstallprompt", script)
        self.assertIn("isMobileInstallSurface", script)
        self.assertIn("if (!isMobileInstallSurface()) return;", script)
        self.assertIn("showUpdateNotice", script)
        self.assertIn("HOF_SKIP_WAITING", script)
        self.assertIn("Refresh for latest version", script)
        self.assertIn("Install app", script)
        self.assertIn("sessionStorage", script)
        self.assertNotIn('http', script)

    def test_shell_caches_the_registration_helper(self):
        worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        self.assertIn("'/assets/pwa-register.js'", worker)

    def test_form_library_install_prompt_explains_its_app_value(self):
        self.assertIn("/texas-agent-form-library", SCRIPT)
        self.assertIn("Keep the Texas form library one tap away", SCRIPT)
        self.assertIn("shared form guide and Question 1", SCRIPT)
        self.assertIn("Keep partner placements one tap away", SCRIPT)
        self.assertIn("partner pricing, your application, and setup details", SCRIPT)

    def test_seller_offer_review_install_prompt_explains_its_app_value(self):
        self.assertIn("window.location.pathname === '/texas-seller-offer-review'", SCRIPT)
        self.assertIn("Keep seller offer review one tap away", SCRIPT)
        self.assertIn("seller offer-review checklist and next conversation", SCRIPT)

    def test_ondemand_install_prompt_explains_its_app_value(self):
        self.assertIn("window.location.pathname === '/ondemand'", SCRIPT)
        self.assertIn("Keep your agent workspace one tap away", SCRIPT)
        self.assertIn("OnDemand agent workspace and first saved offer", SCRIPT)

    def test_core_conversion_pages_have_workflow_specific_install_copy(self):
        self.assertIn("window.location.pathname === '/buyers'", SCRIPT)
        self.assertIn("saved offer and review summary", SCRIPT)
        self.assertIn("window.location.pathname === '/sellers'", SCRIPT)
        self.assertIn("seller plan and support paths", SCRIPT)
        self.assertIn("window.location.pathname === '/agents'", SCRIPT)
        self.assertIn("Question 1, drafts, and your workspace", SCRIPT)
        self.assertIn("window.location.pathname === '/texas-homebuyer-offer-guide'", SCRIPT)
        self.assertIn("Keep your buyer offer plan one tap away", SCRIPT)
        self.assertIn("buyer checklist and offer workflow", SCRIPT)


if __name__ == '__main__':
    unittest.main()
