from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ONDEMAND = (ROOT / "ondemand.html").read_text(encoding="utf-8")


class OnDemandLandingFunnelTests(unittest.TestCase):
    def test_public_endpoint_accepts_only_fixed_trial_funnel_events(self):
        self.assertIn("ONDEMAND_LANDING_EVENT_TYPES", API)
        self.assertIn("def _record_ondemand_landing_event(data):", API)
        self.assertIn('"ondemand_landing_viewed": "viewed"', API)
        self.assertIn('"ondemand_trial_entry_selected": "entry_selected"', API)
        self.assertIn('"ondemand_email_started": "email_started"', API)
        self.assertIn('"ondemand_magic_link_requested": "magic_link_requested"', API)
        self.assertIn('"ondemand_trial_terms_accepted": "terms_accepted"', API)
        self.assertIn("Unsupported OnDemand landing event.", API)
        self.assertIn("'ondemand_landing_event'", API)
        self.assertIn('"surface": "ondemand_landing"', API)
        self.assertIn("ONDEMAND_LANDING_CAMPAIGNS", API)
        self.assertIn('"agent_acquisition", "ondemand_trial"', API)
        self.assertIn("Unsupported OnDemand landing campaign.", API)

    def test_landing_page_records_each_stage_once_per_session(self):
        self.assertIn("recordAggregateLandingEvent", ONDEMAND)
        self.assertIn("sessionStorage.getItem(key)", ONDEMAND)
        self.assertIn('request_type: "ondemand_landing_event"', ONDEMAND)
        self.assertIn('recordAggregateLandingEvent("ondemand_landing_viewed", channel, campaign)', ONDEMAND)
        self.assertIn('utm_campaign: attributionCampaign', ONDEMAND)
        self.assertIn('hof_ondemand_landing_campaign', ONDEMAND)
        self.assertIn('const campaign = new Set(["agent_acquisition", "ondemand_trial"])', ONDEMAND)
        self.assertIn('sessionStorage.getItem("hof_ondemand_landing_channel")', ONDEMAND)
        self.assertIn('sessionStorage.setItem("hof_ondemand_landing_channel", channel)', ONDEMAND)
        self.assertIn('metadata: { source: "ondemand", plan: "agent", billing: "monthly", channel, ...(campaign ? {utmCampaign: campaign} : {}) }', ONDEMAND)
        self.assertIn('recordAggregateLandingEvent("ondemand_magic_link_requested")', ONDEMAND)
        self.assertIn('recordAggregateLandingEvent("ondemand_email_started")', ONDEMAND)
        self.assertIn('recordAggregateLandingEvent("ondemand_trial_terms_accepted")', ONDEMAND)
        self.assertIn("open it in this browser to finish starting your 60-day trial", ONDEMAND)
        self.assertIn("keepalive: true", ONDEMAND)

    def test_mobile_enrollment_card_precedes_supporting_copy(self):
        self.assertIn('<div class="hero-copy">', ONDEMAND)
        self.assertIn(".hero .card { order:1; width:100%; }", ONDEMAND)
        self.assertIn(".hero-copy { order:2; }", ONDEMAND)
        self.assertLess(
            ONDEMAND.index(".hero .card { order:1; width:100%; }"),
            ONDEMAND.index("@media (max-width:520px)"),
        )

    def test_checkout_return_owns_one_quiet_install_prompt_with_aggregate_outcomes(self):
        public_pwa = (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8")
        self.assertIn("if (window.location.pathname === '/ondemand') return;", public_pwa)
        self.assertIn('function recordInstallEvent(eventType)', ONDEMAND)
        for event in ('"cta_clicked"', '"prompt_opened"', '"accepted"', '"dismissed"'):
            self.assertIn(event, ONDEMAND)
        self.assertIn('request_type: "public_pwa_install_event"', ONDEMAND)
        self.assertIn('surface: "/ondemand"', ONDEMAND)
        self.assertIn('recordInstallEvent(choice.outcome);', ONDEMAND)
        self.assertIn('await prompt.prompt();', ONDEMAND)

    def test_email_intent_captures_focus_and_autofill_safe_input_once(self):
        self.assertIn(
            'const recordEmailIntent = () => recordAggregateLandingEvent("ondemand_email_started");',
            ONDEMAND,
        )
        self.assertIn(
            '$("email").addEventListener("focus", recordEmailIntent, { once: true });',
            ONDEMAND,
        )
        self.assertIn(
            '$("email").addEventListener("input", recordEmailIntent, { once: true });',
            ONDEMAND,
        )
        self.assertIn("if (sessionStorage.getItem(key) === \"1\") return;", ONDEMAND)

    def test_enrollment_script_declares_the_legal_policy_version_once(self):
        self.assertEqual(ONDEMAND.count('const LEGAL_POLICY_VERSION = "2026-09-21";'), 1)

    def test_organic_guide_sources_are_allowlisted_for_ondemand_attribution(self):
        self.assertIn("ONDEMAND_LANDING_CHANNELS", API)
        self.assertIn('"organic_listing_workflow"', API)
        self.assertIn('"organic_lease_workflow"', API)
        self.assertIn('"agent_workspace"', API)
        self.assertIn('"agent_form_library"', API)
        self.assertIn('"organic_offer_workflow"', API)
        self.assertIn('"organic", "pwa_shortcut"', API)
        self.assertIn('medium === "installed_app"', ONDEMAND)
        self.assertIn('medium === "organic_content"', ONDEMAND)
        self.assertIn('agent_form_library', ONDEMAND)
        self.assertIn('Unsupported OnDemand landing channel.', API)
        self.assertIn('"channel": channel', API)
        self.assertIn('onDemandCheckoutStartCountsByChannel', ADMIN)
        self.assertIn('onDemandCheckoutReturnCountsByChannel', ADMIN)
        self.assertIn('onDemandCheckoutStartRatesByChannel', ADMIN)
        self.assertIn('onDemandCheckoutReturnRatesByChannel', ADMIN)
        self.assertIn('OnDemand conversion:', INDEX)
        self.assertIn('onDemandMagicLinkCountsByChannel', ADMIN)
        self.assertIn('onDemandTermsAcceptedCountsByChannel', ADMIN)
        self.assertIn('onDemandLandingViewCountsByCampaign', ADMIN)
        self.assertIn('onDemandCheckoutStartRatesByCampaign', ADMIN)
        self.assertIn('onDemandTermsAcceptedCountsByCampaign', ADMIN)
        self.assertIn('OnDemand paid-funnel sources:', INDEX)
        self.assertIn('OnDemand campaign conversion:', INDEX)
        self.assertIn('OnDemand activation sources:', INDEX)

    def test_magic_link_entry_validates_and_focuses_email_before_requesting_auth(self):
        self.assertIn('id="email" type="email" inputmode="email" autocomplete="email"', ONDEMAND)
        start = ONDEMAND.index("async function sendMagicLink()")
        end = ONDEMAND.index("setBusy(button, true", start)
        entry = ONDEMAND[start:end]
        self.assertIn("emailInput.checkValidity()", entry)
        self.assertIn("Enter a valid OnDemand agent email address.", entry)
        self.assertIn('emailInput.focus();', entry)

    def test_public_errors_use_clear_recovery_language_instead_of_raw_service_errors(self):
        self.assertIn("function customerErrorMessage(error, fallback)", ONDEMAND)
        self.assertIn("We couldn’t send a secure sign-in link right now.", ONDEMAND)
        self.assertIn("We couldn’t open secure checkout. Please try again.", ONDEMAND)
        self.assertNotIn('showStatus(error.message, "err")', ONDEMAND)

    def test_magic_link_network_rejection_restores_the_enrollment_button(self):
        start = ONDEMAND.index("async function sendMagicLink()")
        end = ONDEMAND.index("async function startCheckout()", start)
        request = ONDEMAND[start:end]
        self.assertIn("try {", request)
        self.assertIn("catch (requestError)", request)
        self.assertIn("error = requestError;", request)
        self.assertIn(
            'setBusy(button, false, "Sending…", "Email my secure sign-in link");',
            request,
        )
        self.assertLess(
            request.index("catch (requestError)"),
            request.index('setBusy(button, false, "Sending…", "Email my secure sign-in link");'),
        )
        self.assertLess(
            request.index('setBusy(button, false, "Sending…", "Email my secure sign-in link");'),
            request.index("if (error)"),
        )

    def test_optional_brokerage_config_never_blocks_sign_in_or_measurement(self):
        init_start = ONDEMAND.index("async function init()")
        init_end = ONDEMAND.index('$("signInButton").addEventListener', init_start)
        init = ONDEMAND[init_start:init_end]
        self.assertNotIn("await loadConfig();", init)
        self.assertIn('recordAggregateLandingEvent("ondemand_landing_viewed", channel, campaign);', init)
        self.assertIn("void loadConfig();", init)
        self.assertLess(
            init.index('recordAggregateLandingEvent("ondemand_landing_viewed", channel, campaign);'),
            init.index("void loadConfig();"),
        )
        self.assertIn("You can still request your secure sign-in link", ONDEMAND)
        self.assertIn('showStatus(customerErrorMessage(error, "We couldn’t refresh the brokerage details.', ONDEMAND)
        self.assertIn('").textContent.trim())', ONDEMAND)
        self.assertIn(".status.note", ONDEMAND)

    def test_auth_listener_precedes_saved_session_read_and_survives_bootstrap_failure(self):
        start = ONDEMAND.index("async function init()")
        end = ONDEMAND.index('$("signInButton").addEventListener', start)
        init = ONDEMAND[start:end]
        self.assertIn("client.auth.onAuthStateChange", init)
        self.assertIn("await client.auth.getSession()", init)
        self.assertLess(
            init.index("client.auth.onAuthStateChange"),
            init.index("await client.auth.getSession()"),
        )
        self.assertIn("if (error) throw error;", init)
        self.assertIn("catch (error)", init)
        self.assertIn("We couldn’t confirm your saved sign-in.", init)
        self.assertIn("const activeSession = state.session || initialSession;", init)
        self.assertIn("await acceptBrokerageInvite(activeSession);", init)
        self.assertNotIn("await acceptBrokerageInvite(data.session);", init)

    def test_session_bootstrap_runtime_keeps_auth_recovery_listener_after_read_failure(self):
        script = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('async function init()');
const end = html.indexOf('$("signInButton").addEventListener', start);
if (start < 0 || end < 0) throw new Error('init not found');
const state = {session: null};
const window = {location: {search: ''}};
const document = {referrer: '', title: 'HomeOfferFlow'};
let listener = null;
let statusMessage = '';
let rendered = null;
const accepted = [];
const client = {auth: {
  onAuthStateChange(callback) { listener = callback; },
  async getSession() { throw new Error('temporary read failure'); }
}};
const recordAggregateLandingEvent = () => {};
const loadConfig = async () => {};
const showStatus = message => { statusMessage = message; };
const customerErrorMessage = (_error, fallback) => fallback;
const renderSession = session => { rendered = session; state.session = session; };
const acceptBrokerageInvite = async session => { accepted.push(session); };
const recordCheckoutFunnelEvent = async () => {};
const confirmActivatedWorkspace = async () => {};
eval(html.slice(start, end));
(async () => {
  await init();
  if (typeof listener !== 'function') throw new Error('auth listener was not retained');
  if (!statusMessage.includes('request a new secure link')) throw new Error('recovery message missing');
  const recovered = {user: {id: 'agent-1', email: 'agent@example.com'}};
  listener('SIGNED_IN', recovered);
  await new Promise(resolve => setTimeout(resolve, 0));
  if (rendered !== recovered) throw new Error('recovered session was not rendered');
  if (!accepted.includes(recovered)) throw new Error('recovered invite path did not continue');
})().catch(error => { console.error(error); process.exit(1); });
"""
        result = subprocess.run(
            ["node", "-e", script, str(ROOT / "ondemand.html")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_trial_renewal_date_refreshes_when_authenticated_enrollment_renders(self):
        self.assertIn("function refreshRenewalDate()", ONDEMAND)
        self.assertIn("refreshRenewalDate();\n        const signedIn", ONDEMAND)
        self.assertIn("same 60-day window checkout uses", ONDEMAND)

    def test_same_account_token_refresh_preserves_visible_trial_consent(self):
        start = ONDEMAND.index("function renderSession(session)")
        end = ONDEMAND.index("async function acceptBrokerageInvite", start)
        render = ONDEMAND[start:end]
        self.assertIn('const previousUserId = state.session?.user?.id || "";', render)
        self.assertIn('const nextUserId = session?.user?.id || "";', render)
        self.assertIn("const identityChanged = previousUserId !== nextUserId;", render)
        self.assertIn("if (identityChanged) {", render)
        self.assertIn('$("terms").checked = false;', render)
        self.assertIn('$("checkoutButton").disabled = true;', render)
        self.assertLess(render.index("if (identityChanged) {"), render.index('$("terms").checked = false;'))
        self.assertIn("TOKEN_REFRESHED", render)

    def test_session_render_runtime_resets_consent_only_for_a_new_identity(self):
        script = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('function renderSession(session)');
const end = html.indexOf('async function acceptBrokerageInvite', start);
if (start < 0 || end < 0) throw new Error('renderSession not found');
const state = {session: null};
const elements = {};
for (const id of ['signedOut', 'signedIn', 'signedInEmail', 'terms', 'checkoutButton', 'workspaceButton', 'firstOfferButton', 'checkoutRecovery', 'enrollmentDetails']) {
  elements[id] = {style: {}, textContent: '', checked: false, disabled: true};
}
const $ = id => elements[id];
const refreshRenewalDate = () => {};
const renderInstallHint = () => {};
const window = {location: {search: ''}};
eval(html.slice(start, end));

renderSession({user: {id: 'agent-1', email: 'agent@example.com'}, access_token: 'first'});
if (elements.terms.checked || !elements.checkoutButton.disabled) throw new Error('new identity was not reset');
if (!elements.enrollmentDetails.hidden) throw new Error('signed-in enrollment still showed pre-sign-in steps');
elements.terms.checked = true;
elements.checkoutButton.disabled = false;
renderSession({user: {id: 'agent-1', email: 'agent@example.com'}, access_token: 'refreshed'});
if (!elements.terms.checked || elements.checkoutButton.disabled) throw new Error('same identity lost consent');
renderSession({user: {id: 'agent-2', email: 'other@example.com'}, access_token: 'other'});
if (elements.terms.checked || !elements.checkoutButton.disabled) throw new Error('new identity retained prior consent');
"""
        result = subprocess.run(
            ["node", "-e", script, str(ROOT / "ondemand.html")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_trial_page_summarizes_scope_without_repeating_checkout_friction(self):
        self.assertIn("Your plan at a glance", ONDEMAND)
        self.assertIn("Start a transaction today. Keep every next step clear.", ONDEMAND)
        self.assertIn("Review before sending", ONDEMAND)
        self.assertNotIn("Please read before enrolling", ONDEMAND)

    def test_trial_page_puts_the_email_action_before_optional_enrollment_details(self):
        for text in (
            'aria-label="How enrollment works"',
            "Use your OnDemand email.",
            "Open the link in this browser.",
            "Confirm your card at Stripe.",
            "Step 1 of 3:",
            "Email my secure sign-in link",
            "What happens next?",
        ):
            self.assertIn(text, ONDEMAND)
        self.assertLess(ONDEMAND.index('id="signedOut"'), ONDEMAND.index('id="enrollmentDetails"'))
        self.assertIn('$("enrollmentDetails").hidden = signedIn;', ONDEMAND)
        self.assertNotIn("Start my 60-day free trial", ONDEMAND)

    def test_landing_attribution_keeps_referrers_private_but_distinguishes_direct_and_referral_visits(self):
        self.assertIn('const referrerIsExternal = (() => {', ONDEMAND)
        self.assertIn('new URL(document.referrer).origin !== window.location.origin', ONDEMAND)
        self.assertIn('referrerIsExternal ? "referral" : "direct"', ONDEMAND)
        self.assertNotIn('metadata: { referrer', ONDEMAND)

    def test_all_public_ondemand_trial_links_share_the_same_aggregate_entry_signal(self):
        self.assertIn("function recordOnDemandTrialEntry", INDEX)
        self.assertIn("agent_hero_secondary_cta", INDEX)
        self.assertIn("hof_ondemand_trial_entry_selected", INDEX)

    def test_admin_reports_the_trial_conversion_ladder(self):
        for expected in (
            '"onDemandLandingViewCount"',
            '"onDemandTrialEntryCount"',
            '"onDemandEmailStartedCount"',
            '"onDemandEmailStartRate"',
            '"onDemandMagicLinkRequestedCount"',
            '"onDemandMagicLinkRequestRate"',
            '"onDemandTermsAcceptedCount"',
            '"onDemandTermsAcceptedRate"',
            '"onDemandTransactionWorkflowSelectedCounts"',
            "ondemand_landing_view_count",
            "ondemand_terms_accepted_count",
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("onDemandLandingViewCount", INDEX)
        self.assertIn("onDemandEmailStartedCount", INDEX)
        self.assertIn("onDemandEmailStartRate", INDEX)
        self.assertIn("onDemandMagicLinkRequestedCount", INDEX)
        self.assertIn("onDemandMagicLinkRequestRate", INDEX)
        self.assertIn("onDemandTermsAcceptedRate", INDEX)
        self.assertIn("onDemandTransactionWorkflowSelectedCounts", INDEX)


if __name__ == "__main__":
    unittest.main()
