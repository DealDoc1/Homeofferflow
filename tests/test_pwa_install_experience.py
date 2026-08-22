from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class PwaInstallExperienceTests(unittest.TestCase):
    def test_every_live_address_input_uses_the_shared_google_selection_feedback(self):
        self.assertIn("function addressAutocompleteInputs()", INDEX)
        self.assertIn("/(?:address|addr)/i.test(`${input.id} ${input.name}`)", INDEX)
        self.assertIn("function markGoogleAddressSelected(input)", INDEX)
        self.assertIn("input.classList.add('hof-address-selected');", INDEX)
        self.assertIn("input.setAttribute('aria-description', 'Address selected from Google. You can edit it if needed.');", INDEX)
        self.assertIn("markGoogleAddressSelected(input);", INDEX)
        self.assertIn("input.classList.remove('hof-address-selected');", INDEX)

    def test_install_prompt_is_reserved_for_meaningful_mobile_return_work(self):
        self.assertIn('id="hof-pwa-install-v1"', INDEX)
        self.assertIn("beforeinstallprompt", INDEX)
        self.assertIn("deferredInstallPrompt.prompt()", INDEX)
        self.assertIn("Install HomeOfferFlow", INDEX)
        self.assertIn("function installCtaLabel(surface)", INDEX)
        self.assertIn("function installHelpLabel(surface)", INDEX)
        self.assertIn("Install Offer Workspace App", INDEX)
        self.assertIn("Install Seller Plan App", INDEX)
        self.assertIn("Show the 2 steps", INDEX)
        self.assertIn("no App Store download or separate account is needed.", INDEX)
        self.assertIn("pwa-install-benefits", INDEX)
        self.assertIn("offers and client details stay protected online", INDEX)
        self.assertIn("if (!isIos() && !isAndroid()) return;", INDEX)
        self.assertIn("Do not interrupt a clean signed-in dashboard with a generic install", INDEX)
        self.assertNotIn("surface: 'account_dashboard'", INDEX[INDEX.index('function installTarget()'):INDEX.index('function renderInstallCard()')])

    def test_completed_homebuyer_review_can_offer_install_without_account_login(self):
        self.assertIn("function installTarget()", INDEX)
        self.assertIn("surface: 'buyer_review'", INDEX)
        self.assertIn("setTimeout(() => window.renderPwaInstallCard?.(), 0);", INDEX)
        self.assertIn("root.renderPwaInstallCard = renderInstallCard;", INDEX)
        self.assertIn("(root.state?.data?.userType || 'homebuyer') === 'homebuyer'", INDEX)
        self.assertIn("target.panel.prepend(card)", INDEX)

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

    def test_saved_agent_offer_can_offer_install_for_meaningful_repeat_work(self):
        self.assertIn("surface: 'agent_saved_offer'", INDEX)
        self.assertIn("Array.isArray(root.hofAuth?.myOffers)", INDEX)
        self.assertIn("root.hofAuth.myOffers.length > 0", INDEX)
        self.assertIn("Install Agent Workspace App", INDEX)
        self.assertIn("Add Agent Workspace to Home Screen", INDEX)
        self.assertIn('Save this agent workspace to your Home Screen', INDEX)

    def test_ios_uses_home_screen_guidance_and_install_prompt_can_be_dismissed(self):
        self.assertIn("Add to Home Screen", INDEX)
        self.assertIn("hof_pwa_install_dismissed_until", INDEX)
        self.assertIn("1000 * 60 * 60 * 24 * 30", INDEX)
        self.assertIn("appinstalled", INDEX)
        self.assertIn("pwa_install_", INDEX)
        self.assertIn("pwa_install_prompt_shown", INDEX)
        self.assertIn("function isAndroid()", INDEX)
        self.assertIn("function installPlatform()", INDEX)
        self.assertIn("if (isAndroid()) return 'android';", INDEX)
        self.assertIn('In Chrome, open the ⋮ menu', INDEX)
        self.assertIn("choice?.outcome === 'accepted' ? 'accepted' : 'dismissed'", INDEX)
        self.assertIn("const installSurfaceKey = 'hof_pwa_install_surface';", INDEX)
        self.assertIn("function installSurface", INDEX)
        self.assertIn("trackInstall('installed', { platform: installPlatform(), surface: installSurface() })", INDEX)
        self.assertIn("trackInstall('cta_clicked'", INDEX)
        self.assertIn("copy_version: 'install_explicit_v2'", INDEX)
        self.assertIn("cta: 'native_prompt'", INDEX)
        self.assertIn("card.dataset.surface = target.surface", INDEX)
        self.assertIn("surface: target.surface", INDEX)
        self.assertIn("surface: installSurface(card)", INDEX)

    def test_install_funnel_distinguishes_android_from_generic_web_traffic(self):
        self.assertIn("trackInstall('shown', { platform: installPlatform(), surface: target.surface })", INDEX)
        self.assertIn("trackInstall('dismissed', { platform: installPlatform(), surface: installSurface(card) })", INDEX)
        self.assertIn("platform: installPlatform(), surface: target.surface, cta: 'native_prompt'", INDEX)

    def test_install_funnel_measures_native_install_availability_separately_from_manual_guidance(self):
        self.assertIn("trackInstall('native_available'", INDEX)
        self.assertIn("surface: installTarget()?.surface || 'unavailable'", INDEX)
        api = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"native_available": 0', api)
        self.assertIn('"pwaInstallNativeAvailableCount"', api)
        self.assertIn('"pwaInstallNativeAvailableRate"', api)
        self.assertIn("pwaInstallNativeAvailableCount", INDEX)

    def test_admin_dashboard_can_measure_the_privacy_safe_install_funnel(self):
        api = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        for expected in (
            '"pwaInstallEventCounts"',
            '"pwaInstallShownSurfaceCounts"',
            '"pwaInstallShownCount"',
            '"pwaInstallCtaClickCount"',
            '"pwaInstallCtaClickRate"',
            '"pwaInstallPromptOpenCount"',
            '"pwaInstallInstructionsOpenCount"',
            '"pwaInstallGuidanceOpenRate"',
            '"pwaInstallCompletionRate"',
            '"pwaInstallAcceptedRate"',
            '"pwaInstallAcceptedSurfaceCounts"',
            '"pwaAuthenticatedShortcutCounts"',
            "pwa_install_event_counts",
            "pwa_install_surfaces",
            "pwa_authenticated_shortcut_counts",
        ):
            self.assertIn(expected, api)
        self.assertIn("Mobile App Install Funnel", INDEX)
        self.assertIn("pwaInstallPromptOpenRate", INDEX)
        self.assertIn("pwaInstallCtaClickRate", INDEX)
        self.assertIn("pwaInstallInstructionsOpenCount", INDEX)
        self.assertIn("pwaInstallShownSurfaceCounts", INDEX)
        self.assertIn("pwaInstallAcceptedSurfaceCounts", INDEX)
        self.assertIn("pwaInstallAcceptedRate", INDEX)
        self.assertIn("Shown on:", INDEX)
        self.assertIn("Authenticated workspace shortcuts:", INDEX)
        self.assertIn("PWA only: app-like mobile access", INDEX)

    def test_offline_shell_cache_is_versioned_for_the_new_install_surface(self):
        self.assertIn("homeofferflow-shell-v19", WORKER)
        self.assertIn("caches.delete", WORKER)

    def test_signed_out_shortcuts_resume_the_requested_agent_action_after_authentication(self):
        self.assertIn('hof_pwa_shortcut_pending_action', INDEX)
        self.assertIn("sessionStorage.setItem(pendingActionKey, action)", INDEX)
        self.assertIn("async function resumePendingShortcutAfterSignIn()", INDEX)
        self.assertIn("window.startAccountOffer?.();", INDEX)
        self.assertIn("resumed_after_sign_in: Boolean(resumedAfterSignIn)", INDEX)
        self.assertIn("window.openAccountDashboard = async function openAccountDashboardWithPendingPwaShortcut()", INDEX)

    def test_only_safe_declared_shortcuts_can_be_saved_or_routed_after_authentication(self):
        self.assertIn("const validActions = new Set(['workspace', 'listing_tools', 'relationship_drafts', 'offer_review', 'new_offer', 'signing_queue', 'attention_queue', 'seller_plan', 'buyer_offer']);", INDEX)
        self.assertIn("if (!validActions.has(action)) return;", INDEX)
        self.assertIn("sessionStorage.removeItem(pendingActionKey)", INDEX)
        self.assertIn("else if (action === 'relationship_drafts') await openRelationshipDrafts();", INDEX)
        self.assertIn("else if (action === 'offer_review') await openOfferReviewShortcut(role);", INDEX)
        self.assertIn("pwa_authenticated_shortcut_opened", INDEX)
        self.assertIn("surface: 'pwa_shortcut'", INDEX)

    def test_clean_signed_in_standalone_launch_opens_only_the_private_workspace(self):
        self.assertIn("function isStandalonePwa()", INDEX)
        self.assertIn("function canOpenDefaultWorkspace()", INDEX)
        self.assertIn("window.location.pathname === '/'", INDEX)
        self.assertIn("!window.location.search", INDEX)
        self.assertIn("!window.location.hash", INDEX)
        self.assertIn("!window.hofAuth?.routedAfterLogin", INDEX)
        self.assertIn("async function openDefaultWorkspaceAfterAuth()", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'dashboard' })", INDEX)
        self.assertIn("PWA Default Workspace Opened", INDEX)
        self.assertIn("window.addEventListener('hof-auth-ready'", INDEX)
        self.assertIn("window.dispatchEvent(new Event('hof-auth-ready'))", INDEX)

    def test_listing_tools_shortcut_reuses_the_property_first_listing_interview(self):
        self.assertIn("async function openListingTools()", INDEX)
        self.assertIn("window.hofAgentWorkflowContext = 'sale_listing';", INDEX)
        self.assertEqual(INDEX.count("else if (action === 'listing_tools') await openListingTools();"), 2)

    def test_workspace_shortcut_explicitly_resumes_the_private_dashboard_after_sign_in(self):
        resume_start = INDEX.index("async function resumePendingShortcutAfterSignIn()")
        resume_end = INDEX.index("async function openDefaultWorkspaceAfterAuth()", resume_start)
        resume = INDEX[resume_start:resume_end]
        self.assertIn("else if (action === 'workspace')", resume)
        self.assertIn("await window.openAccountDashboard?.({ tab: 'dashboard' });", resume)


if __name__ == "__main__":
    unittest.main()
