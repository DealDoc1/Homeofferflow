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
        self.assertIn("Add to Home Screen", INDEX)
        self.assertIn("No App Store download or separate account is needed.", INDEX)
        self.assertIn("offers and client details stay protected online", INDEX)
        self.assertIn("const workspaceReturnCopy = target.surface === 'account_dashboard'", INDEX)
        self.assertIn('shortcuts for My Workspace and New Agent Offer', INDEX)

    def test_completed_homebuyer_review_can_offer_install_without_account_login(self):
        self.assertIn("function installTarget()", INDEX)
        self.assertIn("surface: 'buyer_review'", INDEX)
        self.assertIn("setTimeout(() => window.renderPwaInstallCard?.(), 0);", INDEX)
        self.assertIn("root.renderPwaInstallCard = renderInstallCard;", INDEX)
        self.assertIn("(root.state?.data?.userType || 'homebuyer') === 'homebuyer'", INDEX)
        self.assertIn("root.hofAuth?.session", INDEX)
        self.assertIn("activationCard.insertAdjacentElement('afterend', card)", INDEX)
        self.assertIn("else target.panel.prepend(card)", INDEX)

    def test_completed_buyer_checkout_can_offer_install_from_the_success_screen(self):
        self.assertIn("surface: 'buyer_success'", INDEX)
        self.assertIn("const isBuyerSuccess = success?.classList.contains('active')", INDEX)
        self.assertIn("window.setTimeout(() => window.renderPwaInstallCard?.(), 0);", INDEX)

    def test_completed_seller_request_can_offer_install_for_returning_mobile_work(self):
        self.assertIn("const sellerStatus = document.getElementById('fsboSellerStatus');", INDEX)
        self.assertIn("sellerModal?.getAttribute('aria-hidden') === 'false'", INDEX)
        self.assertIn("surface: 'seller_success'", INDEX)
        self.assertIn("const sellerReturnCopy = target.surface === 'seller_success'", INDEX)
        self.assertIn('Save this seller plan to your Home Screen', INDEX)

    def test_ios_uses_home_screen_guidance_and_install_prompt_can_be_dismissed(self):
        self.assertIn("Add to Home Screen", INDEX)
        self.assertIn("hof_pwa_install_dismissed_until", INDEX)
        self.assertIn("1000 * 60 * 60 * 24 * 30", INDEX)
        self.assertIn("appinstalled", INDEX)
        self.assertIn("pwa_install_", INDEX)
        self.assertIn("pwa_install_prompt_shown", INDEX)
        self.assertIn("function isAndroid()", INDEX)
        self.assertIn('In Chrome, open the ⋮ menu', INDEX)
        self.assertIn("choice?.outcome === 'accepted' ? 'accepted' : 'dismissed'", INDEX)
        self.assertIn("card.dataset.surface = target.surface", INDEX)
        self.assertIn("surface: target.surface", INDEX)
        self.assertIn("card?.dataset?.surface || 'unknown'", INDEX)

    def test_admin_dashboard_can_measure_the_privacy_safe_install_funnel(self):
        api = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        for expected in (
            '"pwaInstallEventCounts"',
            '"pwaInstallShownCount"',
            '"pwaInstallPromptOpenCount"',
            '"pwaInstallInstructionsOpenCount"',
            '"pwaInstallGuidanceOpenRate"',
            '"pwaInstallCompletionRate"',
            "pwa_install_event_counts",
        ):
            self.assertIn(expected, api)
        self.assertIn("Mobile App Install Funnel", INDEX)
        self.assertIn("pwaInstallPromptOpenRate", INDEX)
        self.assertIn("pwaInstallInstructionsOpenCount", INDEX)
        self.assertIn("PWA only: app-like mobile access", INDEX)

    def test_offline_shell_cache_is_versioned_for_the_new_install_surface(self):
        self.assertIn("homeofferflow-shell-v8", WORKER)
        self.assertIn("caches.delete", WORKER)

    def test_signed_out_shortcuts_resume_the_requested_agent_action_after_authentication(self):
        self.assertIn('hof_pwa_shortcut_pending_action', INDEX)
        self.assertIn("sessionStorage.setItem(pendingActionKey, action)", INDEX)
        self.assertIn("async function resumePendingShortcutAfterSignIn()", INDEX)
        self.assertIn("window.startAccountOffer?.();", INDEX)
        self.assertIn("resumed_after_sign_in: Boolean(resumedAfterSignIn)", INDEX)
        self.assertIn("window.openAccountDashboard = async function openAccountDashboardWithPendingPwaShortcut()", INDEX)

    def test_only_safe_declared_shortcuts_can_be_saved_or_routed_after_authentication(self):
        self.assertIn("const validActions = new Set(['workspace', 'new_offer']);", INDEX)
        self.assertIn("if (!validActions.has(action)) return;", INDEX)
        self.assertIn("sessionStorage.removeItem(pendingActionKey)", INDEX)


if __name__ == "__main__":
    unittest.main()
