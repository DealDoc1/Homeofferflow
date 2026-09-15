from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / 'assets' / 'pwa-register.js').read_text(encoding='utf-8')
PUBLIC_PAGES = (
    'directory.html', 'buyers.html', 'partners.html', 'sellers.html',
    'agents.html', 'investors.html', 'texas-fsbo-guide.html', 'texas-home-service-partner-guide.html',
    'texas-agent-offer-workflow.html', 'texas-seller-offer-review.html', 'texas-homebuyer-offer-guide.html', 'texas-investor-offer-guide.html', 'texas-seller-financing-guide.html', 'texas-buyer-representation-guide.html', 'texas-flat-fee-mls-guide.html', 'texas-seller-net-proceeds-calculator.html', 'texas-fsbo-closing-checklist.html', 'ondemand.html'
)


class PublicPwaRegistrationTests(unittest.TestCase):
    def test_public_discovery_pages_register_the_shared_low_cost_app_shell(self):
        for filename in PUBLIC_PAGES:
            with self.subTest(filename=filename):
                html = (ROOT / filename).read_text(encoding='utf-8')
                self.assertIn('/assets/pwa-register.js', html)

    def test_registration_uses_root_scope_without_third_party_dependencies(self):
        script = (ROOT / 'assets' / 'pwa-register.js').read_text(encoding='utf-8')
        self.assertIn("navigator.serviceWorker.register('/service-worker.js', { scope: '/', updateViaCache: 'none' })", script)
        self.assertIn("Always revalidate the worker itself", script)
        self.assertIn("beforeinstallprompt", script)
        self.assertIn("isMobileInstallSurface", script)
        self.assertIn("if (!isMobileInstallSurface()) return;", script)
        self.assertIn("showUpdateNotice", script)
        self.assertIn("if (!isStandaloneSurface() || !registration?.waiting || document.getElementById('hofPublicPwaUpdateNotice')) return;", script)
        self.assertIn("HOF_SKIP_WAITING", script)
        self.assertIn("Refresh for latest version", script)
        self.assertIn("Install app", script)
        self.assertIn("sessionStorage", script)
        self.assertNotIn("fetch('http", script)
        self.assertNotIn('fetch("http', script)
        self.assertNotIn(".src = 'http", script)
        self.assertNotIn('.src = "http', script)

    def test_update_refresh_waits_for_the_new_worker_to_take_control(self):
        self.assertIn("const waiting = registration.waiting;", SCRIPT)
        self.assertIn("navigator.serviceWorker.addEventListener('controllerchange', reloadAfterActivation, { once: true });", SCRIPT)
        self.assertIn("waiting.postMessage({ type: 'HOF_SKIP_WAITING' });", SCRIPT)
        update_start = SCRIPT.index("notice.querySelector('#hofPublicPwaUpdateButton')")
        update_end = SCRIPT.index("  const renderInstallCard", update_start)
        update_handler = SCRIPT[update_start:update_end]
        self.assertLess(update_handler.index("controllerchange"), update_handler.index("waiting.postMessage"))

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

    def test_seller_net_proceeds_calculator_has_specific_install_value(self):
        self.assertIn("window.location.pathname === '/texas-seller-net-proceeds-calculator'", SCRIPT)
        self.assertIn("Keep your seller proceeds worksheet one tap away", SCRIPT)
        self.assertIn("private proceeds worksheet and seller planning paths", SCRIPT)

    def test_seller_question_one_has_a_quiet_under_contract_path(self):
        self.assertIn("window.location.pathname === '/sellers'", SCRIPT)
        self.assertIn("hofSellerClosingChecklistCta", SCRIPT)
        self.assertIn("Already under contract?", SCRIPT)
        self.assertIn("/texas-fsbo-closing-checklist?utm_source=seller_question_one", SCRIPT)

    def test_buyer_representation_guide_surfaces_the_current_official_workflow_reminder(self):
        self.assertIn("window.location.pathname === '/texas-buyer-representation-guide'", SCRIPT)
        self.assertIn("hofWrittenAgreementReminder", SCRIPT)
        self.assertIn("written agreement is required before showing residential property", SCRIPT)
        self.assertIn("Written-Agreement-Explainer.pdf", SCRIPT)
        self.assertIn("Follow the required professional process", SCRIPT)

    def test_buyer_representation_guide_has_workflow_specific_install_copy(self):
        self.assertIn("buyerRepresentationGuideSurface", SCRIPT)
        self.assertIn("Keep buyer representation planning one tap away", SCRIPT)
        self.assertIn("buyer-representation workflow and the agent workspace", SCRIPT)

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
        self.assertIn("Question 1, your saved work, and your workspace", SCRIPT)
        self.assertIn("window.location.pathname === '/texas-homebuyer-offer-guide'", SCRIPT)
        self.assertIn("Keep your buyer offer plan one tap away", SCRIPT)
        self.assertIn("buyer checklist and offer workflow", SCRIPT)
        self.assertIn("window.location.pathname === '/texas-investor-offer-guide'", SCRIPT)
        self.assertIn("Keep your investor offer plan one tap away", SCRIPT)
        self.assertIn("investor checklist and repeat-offer workflow", SCRIPT)

    def test_agent_trial_link_normalizer_preserves_existing_campaign_attribution(self):
        self.assertIn("document.querySelectorAll('a[href^=\"/ondemand\"]')", SCRIPT)
        self.assertIn("if (!link.href.includes('utm_source='))", SCRIPT)

    def test_agent_workflow_guides_have_workflow_specific_install_copy(self):
        self.assertIn("Keep your listing workflow one tap away", SCRIPT)
        self.assertIn("listing plan, offer comparison, and next action", SCRIPT)
        self.assertIn("Keep your lease workflow one tap away", SCRIPT)
        self.assertIn("lease workflow and next client step", SCRIPT)
        self.assertIn("Keep your offer workflow one tap away", SCRIPT)
        self.assertIn("offer workflow and Question 1", SCRIPT)

    def test_consumer_and_provider_surfaces_have_contextual_install_copy(self):
        self.assertIn("Keep your investor workspace one tap away", SCRIPT)
        self.assertIn("saved investor defaults and repeat-offer tools", SCRIPT)
        self.assertIn("Keep the provider directory one tap away", SCRIPT)
        self.assertIn("provider search and partner placement paths", SCRIPT)
        self.assertIn("Keep your FSBO plan one tap away", SCRIPT)
        self.assertIn("seller plan and support paths", SCRIPT)

    def test_public_install_prompt_records_privacy_safe_aggregate_funnel_events(self):
        self.assertIn("trackPublicInstall('Shown')", SCRIPT)
        self.assertIn("trackPublicInstall('CtaClicked')", SCRIPT)
        self.assertIn("choice?.outcome === 'accepted' ? 'Accepted' : 'Dismissed'", SCRIPT)
        self.assertIn("trackPublicInstall('Installed')", SCRIPT)
        self.assertIn("surface: window.location.pathname", SCRIPT)
        self.assertIn("public_pwa_install_event", SCRIPT)
        self.assertIn("NativeAvailable: 'native_available'", SCRIPT)
        self.assertIn("hof_public_pwa_install_", SCRIPT)
        self.assertIn("trackPublicInstall('NativeAvailable')", SCRIPT)

    def test_install_prompt_waits_for_returning_engagement_and_respects_a_quiet_period(self):
        self.assertIn("const installEligibleKey = 'hof_public_pwa_install_eligible_v2'", SCRIPT)
        self.assertIn("const installEngagementCountKey = 'hof_public_pwa_install_engagement_count_v1'", SCRIPT)
        self.assertIn("Only offer it after a second engaged visit", SCRIPT)
        self.assertIn("const installDismissedUntilKey = 'hof_public_pwa_install_dismissed_until_v1'", SCRIPT)
        self.assertIn("const installDismissalDays = 14", SCRIPT)
        self.assertIn("const installShownUntilKey = 'hof_public_pwa_install_shown_until_v1'", SCRIPT)
        self.assertIn("const installShownDays = 30", SCRIPT)
        self.assertIn("!isInstallEligible() || isInstallDismissed() || isInstallRecentlyShown()", SCRIPT)
        self.assertIn("same promotion on every public guide or landing page", SCRIPT)
        self.assertIn("['pointerdown', 'keydown', 'scroll'].forEach", SCRIPT)
        self.assertIn("The remembered eligibility makes the install offer", SCRIPT)

    def test_ios_public_pages_explain_home_screen_install_without_native_prompt(self):
        self.assertIn("isIosInstallSurface", SCRIPT)
        self.assertIn("Add to Home Screen", SCRIPT)
        self.assertIn("trackPublicInstall('InstructionsOpened')", SCRIPT)
        self.assertIn("window.addEventListener('load', () => { if (isIosInstallSurface()) renderInstallCard(); }", SCRIPT)

    def test_public_cached_pages_explain_offline_scope_and_recover_on_reconnect(self):
        self.assertIn("id = 'hofPublicPwaOfflineNotice'", SCRIPT)
        self.assertIn('This saved public page remains available', SCRIPT)
        self.assertIn("window.addEventListener('offline', renderOfflineNotice)", SCRIPT)
        self.assertIn("window.addEventListener('online', renderOfflineNotice)", SCRIPT)


if __name__ == '__main__':
    unittest.main()
