import re
import unittest
from pathlib import Path


INDEX_PATH = Path(__file__).resolve().parents[1] / "index.html"


class PartnerTierUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX_PATH.read_text(encoding="utf-8")

    def test_three_public_tiers_and_rates_are_present(self):
        expected = (
            ("Core Partner", "$149"),
            ("Featured Partner", "$399"),
            ("Premier Partner", "$799"),
        )
        for label, rate in expected:
            with self.subTest(label=label):
                self.assertIn(label, self.html)
                self.assertIn(rate, self.html)

    def test_founder_offer_is_a_clear_nonrenewing_90_day_pilot(self):
        required_copy = (
            "first 90 days for the price of one standard month",
            "first 10 approved partners",
            "no setup fee",
            "then renews monthly at the standard rate after 90 days unless cancelled",
            "Then $149/month after 90 days, unless cancelled",
            "Then $399/month after 90 days, unless cancelled",
            "Then $799/month after 90 days, unless cancelled",
        )
        for copy in required_copy:
            with self.subTest(copy=copy):
                self.assertIn(copy, self.html)

    def test_public_tiers_keep_existing_server_safe_model_values(self):
        for value in ("founding_pilot", "monthly_placement", "market_exclusive"):
            with self.subTest(value=value):
                self.assertRegex(
                    self.html,
                    rf'data-partner-tier="{re.escape(value)}"',
                )

    def test_consumer_choice_and_neutral_selection_are_explicit(self):
        required_copy = (
            "never preselects a paid provider",
            "users may choose any provider or none",
            "neutral provider selector",
            "Sponsored",
        )
        for copy in required_copy:
            with self.subTest(copy=copy):
                self.assertIn(copy, self.html)

    def test_partner_form_still_posts_to_existing_function(self):
        self.assertIn("fetch('/api/fsbo-lead'", self.html)
        self.assertIn("request_type: 'founding_partner'", self.html)

    def test_checkout_intake_keeps_required_details_short_and_defers_preferences(self):
        self.assertIn("Start with the essentials.", self.html)
        self.assertIn("Everything else can be added during onboarding.", self.html)

    def test_checkout_intake_validates_and_focuses_the_first_invalid_essential(self):
        self.assertIn('id="foundingPartnerType" required aria-required="true"', self.html)
        self.assertIn('Choose your service category', self.html)
        self.assertIn('id="foundingPartnerEmail" type="email" inputmode="email" autocomplete="email"', self.html)
        start = self.html.index("window.submitFoundingPartnerLead")
        end = self.html.index("if (!hasSavedPartnerApplication && !document.getElementById('foundingPartnerConsent')", start)
        submit = self.html[start:end]
        self.assertIn("emailInput?.checkValidity()", submit)
        self.assertIn("typeInput?.checkValidity()", submit)
        self.assertIn("Choose your service category to continue to secure checkout.", submit)
        self.assertIn("Enter a valid business email to continue to secure checkout.", submit)
        self.assertIn("firstInvalid?.focus();", submit)
        self.assertIn("setAttribute('aria-invalid'", submit)
        self.assertIn("Add optional placement preferences now", self.html)
        required_end = self.html.index('<div aria-hidden="true"', self.html.index('Start with the essentials.'))
        required_start = self.html.index('Start with the essentials.')
        required_area = self.html[required_start:required_end]
        self.assertLess(required_area.index('foundingPartnerMarket'), required_area.index('partner-optional-details'))
        self.assertGreater(required_area.index('foundingPartnerPhone'), required_area.index('partner-optional-details'))

    def test_checkout_handoff_unlocks_only_after_essentials_and_consent(self):
        self.assertIn('id="foundingPartnerSubmit" onclick="submitFoundingPartnerLead()" disabled aria-disabled="true"', self.html)
        self.assertIn('id="foundingPartnerRequiredCue"', self.html)
        self.assertIn("function partnerEssentialProgress()", self.html)
        self.assertIn("Complete the five essentials (${progress.complete} of 5 complete)", self.html)
        self.assertIn("Review and acknowledge the founding-partner terms below, then continue to secure checkout.", self.html)
        self.assertIn("document.getElementById('foundingPartnerConsent')?.addEventListener('change', () => { savePartnerApplicationDraft(); renderFoundingPartnerCheckoutAvailability(); });", self.html)
        self.assertIn("Complete the next step to continue", self.html)

    def test_checkout_submit_exposes_busy_state_and_restores_after_failure(self):
        start = self.html.index("window.submitFoundingPartnerLead")
        end = self.html.index("function setupPartnerOnboardingModal", start)
        submit = self.html[start:end]
        self.assertIn("submit.setAttribute('aria-busy', 'true')", submit)
        self.assertIn("submit.textContent = hasSavedPartnerApplication ? 'Opening secure checkout…' : 'Saving application…'", submit)
        self.assertIn("submit.setAttribute('aria-busy', 'false')", submit)
        self.assertIn("renderFoundingPartnerCheckoutAvailability();", submit)

    def test_checkout_failure_metrics_distinguish_save_from_checkout_handoff(self):
        start = self.html.index("window.submitFoundingPartnerLead")
        end = self.html.index("function setupPartnerOnboardingModal", start)
        submit = self.html[start:end]
        self.assertIn("let applicationSavedNow = false;", submit)
        self.assertIn("applicationSavedNow = true;", submit)
        self.assertIn("partner_application_save_failed", submit)
        self.assertIn("partner_checkout_start_failed", submit)

    def test_checkout_status_is_announced_atomically(self):
        self.assertIn('id="foundingPartnerStatus" class="platform-status" role="status" aria-live="polite" aria-atomic="true"', self.html)

    def test_missing_consent_returns_focus_to_the_required_acknowledgement(self):
        start = self.html.index("if (!hasSavedPartnerApplication && !document.getElementById('foundingPartnerConsent')?.checked)")
        end = self.html.index("trackPartnerFunnel('Founding Partner Checkout Started'", start)
        self.assertIn("document.getElementById('foundingPartnerConsent')?.focus();", self.html[start:end])

    def test_checkout_retry_reuses_saved_partner_lead(self):
        self.assertIn("window.__hofFoundingPartnerLeadId", self.html)
        self.assertIn("if (!partnerLeadId)", self.html)
        self.assertIn("partner_lead_id: partnerLeadId", self.html)

    def test_unfinished_partner_application_is_saved_privately_before_submission(self):
        self.assertIn("const partnerDraftStorageKey = 'hof_founding_partner_application_draft_v1'", self.html)
        self.assertIn("function savePartnerApplicationDraft()", self.html)
        self.assertIn("function restorePartnerApplicationDraft()", self.html)
        self.assertIn("Your application draft was restored in this browser session.", self.html)
        self.assertIn("It has not been submitted or shared.", self.html)
        self.assertIn("clearPartnerApplicationDraft();", self.html)
        self.assertIn("savePartnerApplicationDraft(); renderFoundingPartnerCheckoutAvailability();", self.html)
        self.assertIn("clearPartnerApplicationDraft();", self.html[self.html.index("partnerLeadId = result.partner_lead_id;"):])

    def test_partner_lead_retry_state_survives_refresh_and_clears_after_checkout(self):
        self.assertIn("hof_founding_partner_lead_id", self.html)
        self.assertIn("sessionStorage.setItem", self.html)
        self.assertIn("sessionStorage.removeItem", self.html)
        self.assertIn("partner_checkout') === 'success'", self.html)

    def test_cancelled_checkout_has_a_saved_application_resume_state(self):
        self.assertIn('id="foundingPartnerCheckoutResume"', self.html)
        self.assertIn("partner_checkout') === 'cancelled'", self.html)
        self.assertIn('Resume Secure Checkout', self.html)
        self.assertIn('No second application is created on this device.', self.html)
        self.assertIn("founding_partner_checkout_returned", self.html)
        self.assertIn("partner_resume_token", self.html)

    def test_checkout_return_identifiers_are_removed_from_browser_history_after_capture(self):
        self.assertIn("__hofFoundingPartnerCheckoutState", self.html)
        self.assertIn("cleanUrl.searchParams.delete(key)", self.html)
        self.assertIn("['partner_checkout', 'partner_lead_id', 'partner_resume_token']", self.html)
        self.assertIn("['partner_checkout', 'session_id']", self.html)

    def test_partner_checkout_funnel_is_measured_without_contact_data(self):
        self.assertIn("function trackPartnerFunnel(name, data = {})", self.html)
        for event in (
            "Founding Partner Intake Opened",
            "Founding Partner Tier Selected",
            "Founding Partner Checkout Started",
            "Founding Partner Application Saved",
            "Founding Partner Stripe Checkout Opened",
            "Founding Partner Checkout Cancelled",
            "Founding Partner Checkout Completed",
            "Founding Partner Checkout Failed",
        ):
            self.assertIn(event, self.html)
        self.assertIn("partner_application_essentials_ready", self.html)
        self.assertIn("partner_application_checkout_ready", self.html)
        self.assertIn("partner_application_save_failed", self.html)
        self.assertIn("partner_checkout_start_failed", self.html)
        self.assertIn("window.selectFoundingPartnerTier('founding_pilot', false)", self.html)

    def test_selected_tier_makes_the_secure_checkout_handoff_explicit(self):
        self.assertIn('id="foundingPartnerCheckoutNote"', self.html)
        self.assertIn('Continue to Secure Checkout — ', self.html)

    def test_custom_multi_market_request_never_opens_price_based_checkout(self):
        self.assertIn("if (payload.preferred_model === 'discuss')", self.html)
        self.assertIn("Custom Request Saved", self.html)
        self.assertIn("before any checkout or charge", self.html)
        self.assertIn('review the selected Founding Partner price and payment details in secure Stripe Checkout', self.html)
        self.assertIn('placement stays private until onboarding and written-agreement review are complete', self.html)

    def test_short_required_checkout_intake_precedes_the_optional_tier_comparison(self):
        essentials = self.html.index('id="foundingPartnerEssentials"')
        comparison = self.html.index('id="foundingPartnerTierComparison"')
        placement = self.html.index('class="partner-placement-wrap"')
        self.assertLess(essentials, comparison)
        self.assertLess(comparison, placement)
        self.assertIn('Compare or change your placement tier', self.html)
        self.assertIn("window.jumpToFoundingPartnerEssentials", self.html)
        self.assertIn("essentials.scrollIntoView({ behavior: 'smooth', block: 'start' })", self.html)
        self.assertIn("Founding Partner Essentials Jumped", self.html)
        self.assertIn("partner_application_tier_selected", self.html)
        self.assertIn("partner_application_essentials_opened", self.html)

    def test_admin_partner_leads_have_privacy_limited_follow_up_action(self):
        self.assertIn("partnerLeadFollowUpAction", self.html)
        self.assertIn("Email partner", self.html)
        self.assertIn("HomeOfferFlow partner onboarding next step", self.html)
        self.assertIn("contact_email", self.html)

    def test_homepage_audience_grid_links_to_partner_offer(self):
        self.assertIn("<h3>Service Partners</h3>", self.html)
        self.assertIn("Founding partner placements from $149", self.html)
        self.assertRegex(
            self.html,
            r'class="audience-card audience-card-link"[^>]+href="\?partner=1&amp;partner_quick_start=1"',
        )
        self.assertIn("openFoundingPartnerModal({ quickStart: true });", self.html)

    def test_partner_category_list_includes_roofing_and_home_services(self):
        expected_categories = (
            ('roofing', 'Roofing contractor'),
            ('hvac', 'HVAC / heating and air'),
            ('plumbing', 'Plumbing'),
            ('electrical', 'Electrical'),
            ('foundation_structural', 'Foundation / structural repair'),
            ('general_contractor', 'General contractor / remodeling'),
            ('pest_termite', 'Pest control / termite'),
            ('septic_well', 'Septic / well service'),
            ('restoration', 'Water / fire restoration'),
            ('surveyor', 'Property surveyor'),
            ('security_smart_home', 'Security / smart home'),
        )
        for value, label in expected_categories:
            with self.subTest(value=value):
                self.assertIn(
                    f'<option value="{value}">{label}</option>',
                    self.html,
                )

    def test_campaign_links_can_preselect_only_existing_partner_categories(self):
        self.assertIn("const partnerCampaignCategories = new Set", self.html)
        self.assertIn("params().get('partner_category')", self.html)
        self.assertIn("return partnerCampaignCategories.has(category) ? category : '';", self.html)
        self.assertIn("function applyCampaignPartnerChoices()", self.html)
        self.assertIn("if (window.__hofFoundingPartnerLeadId) return { category:'', tier:'', channel:'' };", self.html)
        self.assertIn("campaignCategory: campaign.category || null", self.html)

    def test_campaign_links_can_preselect_only_paid_existing_tiers(self):
        self.assertIn("const partnerCampaignTiers = new Set(['founding_pilot','monthly_placement','market_exclusive']);", self.html)
        self.assertIn("const partnerCampaignChannels = new Set(['direct_outreach','email','social','referral','local_event','print']);", self.html)
        self.assertIn("function campaignPartnerChannel()", self.html)
        self.assertIn("if (partnerCampaignChannels.has(source)) return source;", self.html)
        self.assertIn("source === 'homeofferflow_admin' && partnerCampaignChannels.has(medium)", self.html)
        self.assertIn("campaignChannel: campaign.channel || null", self.html)
        self.assertIn("params().get('partner_tier')", self.html)
        self.assertIn("return partnerCampaignTiers.has(tier) ? tier : '';", self.html)
        self.assertIn("window.selectFoundingPartnerTier?.(tier, false);", self.html)
        self.assertIn("campaignTier: campaign.tier || null", self.html)


if __name__ == "__main__":
    unittest.main()
