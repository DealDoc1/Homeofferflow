from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class PwaInstallExperienceTests(unittest.TestCase):
    def test_authenticated_dashboard_offers_the_supported_install_prompt(self):
        self.assertIn('id="hof-pwa-install-v1"', INDEX)
        self.assertIn("beforeinstallprompt", INDEX)
        self.assertIn("deferredInstallPrompt.prompt()", INDEX)
        self.assertIn("Install HomeOfferFlow", INDEX)

    def test_completed_homebuyer_review_can_offer_install_without_account_login(self):
        self.assertIn("function installTarget()", INDEX)
        self.assertIn("surface: 'buyer_review'", INDEX)
        self.assertIn("setTimeout(() => window.renderPwaInstallCard?.(), 0);", INDEX)
        self.assertIn("root.renderPwaInstallCard = renderInstallCard;", INDEX)
        self.assertIn("(root.state?.data?.userType || 'homebuyer') === 'homebuyer'", INDEX)
        self.assertIn("root.hofAuth?.session", INDEX)

    def test_ios_uses_home_screen_guidance_and_install_prompt_can_be_dismissed(self):
        self.assertIn("Add to Home Screen", INDEX)
        self.assertIn("hof_pwa_install_dismissed_until", INDEX)
        self.assertIn("1000 * 60 * 60 * 24 * 30", INDEX)
        self.assertIn("appinstalled", INDEX)
        self.assertIn("pwa_install_", INDEX)
        self.assertIn("pwa_install_prompt_shown", INDEX)
        self.assertIn("choice?.outcome === 'accepted' ? 'accepted' : 'dismissed'", INDEX)

    def test_offline_shell_cache_is_versioned_for_the_new_install_surface(self):
        self.assertIn("homeofferflow-shell-v7", WORKER)
        self.assertIn("caches.delete", WORKER)


if __name__ == "__main__":
    unittest.main()
