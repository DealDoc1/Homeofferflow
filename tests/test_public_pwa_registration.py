from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PAGES = (
    'directory.html', 'buyers.html', 'partners.html', 'sellers.html',
    'agents.html', 'investors.html', 'texas-fsbo-guide.html',
    'texas-agent-offer-workflow.html'
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
        self.assertIn("Install app", script)
        self.assertIn("sessionStorage", script)
        self.assertNotIn('http', script)

    def test_shell_caches_the_registration_helper(self):
        worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        self.assertIn("'/assets/pwa-register.js'", worker)


if __name__ == '__main__':
    unittest.main()
