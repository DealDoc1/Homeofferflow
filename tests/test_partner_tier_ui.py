import json
import re
import unittest
from pathlib import Path


INDEX_PATH = Path(__file__).resolve().parents[1] / "index.html"
API_PATH = INDEX_PATH.parent / "api" / "fsbo-lead.py"


class PartnerTierUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX_PATH.read_text(encoding="utf-8")

    def test_three_public_tiers_and_rates_are_present(self):
        for label in ("Founding Partner", "Featured Partner", "Premier Partner"):
            with self.subTest(label=label):
                self.assertIn(label, self.html)
        self.assertEqual(self.html.count('<strong>$0</strong><span>during beta</span>'), 3)

    def test_beta_terms_are_equal_and_have_no_automatic_paid_conversion(self):
        self.assertIn("All partner placements are complimentary during beta", self.html)
        self.assertIn("no automatic paid conversion", self.html)
        self.assertNotIn("$149", self.html)
        self.assertNotIn("$399", self.html)
        self.assertNotIn("$799", self.html)

    def test_public_tiers_keep_existing_server_safe_model_values(self):
        for value in ("founding_pilot", "monthly_placement", "market_exclusive"):
            with self.subTest(value=value):
                self.assertRegex(
                    self.html,
                    rf'data-partner-tier="{re.escape(value)}"',
                )

    def test_consumer_choice_and_neutral_selection_are_explicit(self):
        required_copy = (
            "never preselects a provider",
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

    def test_beta_application_uses_the_server_program_response_before_checkout(self):
        start = self.html.index("window.submitFoundingPartnerLead = async function")
        end = self.html.index("function setupPartnerOnboardingModal", start)
        submit = self.html[start:end]
        beta_path = submit.index("if (result.partner_program === 'beta')")
        checkout_path = submit.index("request_type: 'founding_partner_checkout'")
        self.assertLess(beta_path, checkout_path)
        self.assertIn("No checkout or payment was started.", submit)
        self.assertIn("partner_program", API_PATH.read_text(encoding="utf-8"))

    def test_beta_intake_keeps_required_details_short_and_defers_preferences(self):
        self.assertIn("Five quick details.", self.html)
        self.assertIn("Complimentary during beta", self.html)
        self.assertIn("no payment or automatic paid conversion", self.html)
        self.assertIn("Add optional placement preferences now", self.html)
        self.assertNotIn("foundingPartnerBudget", self.html)
        self.assertNotIn("monthly_budget_range: value('foundingPartnerBudget')", self.html)
        modal = self.html[self.html.index('id="foundingPartnerModal"'):self.html.index('id="hof-founding-partner-intake-v1"')]
        self.assertNotIn("Founding offer:</strong>", modal)
        self.assertNotIn("foundingPartnerBudget", modal)

    def test_checkout_intake_validates_and_focuses_the_first_invalid_essential(self):
        self.assertIn('id="foundingPartnerType" required aria-required="true"', self.html)
        self.assertIn('Choose your service category', self.html)
        self.assertIn('id="foundingPartnerEmail" type="email" inputmode="email" autocomplete="email"', self.html)
        start = self.html.index("window.submitFoundingPartnerLead")
        end = self.html.index("if (!hasSavedPartnerApplication && !document.getElementById('foundingPartnerConsent')", start)
        submit = self.html[start:end]
        self.assertIn("emailInput?.checkValidity()", submit)
        self.assertIn("typeInput?.checkValidity()", submit)
        self.assertIn("Choose your service category to submit your application.", submit)
        self.assertIn("Enter a valid business email to submit your application.", submit)
        self.assertIn("firstInvalid?.focus();", submit)
        self.assertIn("setAttribute('aria-invalid'", submit)
        self.assertIn("Add optional placement preferences now", self.html)
        required_start = self.html.index('id="foundingPartnerEssentials"')
        required_end = self.html.index('<div aria-hidden="true"', required_start)
        required_area = self.html[required_start:required_end]
        self.assertLess(required_area.index('foundingPartnerMarket'), required_area.index('partner-optional-details'))
        self.assertGreater(required_area.index('foundingPartnerPhone'), required_area.index('partner-optional-details'))

    def test_checkout_action_guides_incomplete_applicants_without_bypassing_validation(self):
        self.assertIn('id="foundingPartnerSubmit" onclick="submitFoundingPartnerLead()" aria-disabled="false"', self.html)
        self.assertNotIn('id="foundingPartnerSubmit" onclick="submitFoundingPartnerLead()" disabled', self.html)
        self.assertIn('id="foundingPartnerRequiredCue"', self.html)
        self.assertIn("function partnerEssentialProgress()", self.html)
        self.assertIn("Complete the five essentials (${progress.complete} of 5 complete)", self.html)
        self.assertIn("Review and acknowledge the complimentary beta terms before submitting", self.html)
        self.assertIn("document.getElementById('foundingPartnerConsent')?.addEventListener('change', () => { savePartnerApplicationDraft(); renderFoundingPartnerCheckoutAvailability(); });", self.html)
        self.assertIn("Continue application — ${progress.complete} of 5 details added", self.html)
        self.assertIn("Review beta terms to continue", self.html)
        self.assertIn("Keep the primary action operable while the application is incomplete.", self.html)
        self.assertIn("submit.disabled = false;", self.html)
        start = self.html.index("window.submitFoundingPartnerLead")
        validation_end = self.html.index("if (!hasSavedPartnerApplication && !document.getElementById('foundingPartnerConsent')", start)
        validation = self.html[start:validation_end]
        self.assertIn("firstInvalid?.focus();", validation)
        self.assertIn("return;", validation)

    def test_required_acknowledgement_is_visible_before_optional_preferences(self):
        essentials = self.html.index('id="foundingPartnerEssentials"')
        consent = self.html.index('id="foundingPartnerConsent"')
        optional = self.html.index('id="foundingPartnerTierComparison"')
        self.assertLess(essentials, consent)
        self.assertLess(consent, optional)

    def test_checkout_submit_exposes_busy_state_and_restores_after_failure(self):
        start = self.html.index("window.submitFoundingPartnerLead")
        end = self.html.index("function setupPartnerOnboardingModal", start)
        submit = self.html[start:end]
        self.assertIn("submit.setAttribute('aria-busy', 'true')", submit)
        self.assertIn("submit.textContent = hasSavedPartnerApplication ? 'Application already saved' : 'Saving application…'", submit)
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
        end = self.html.index("trackPartnerFunnel('Founding Partner Paid Checkout Started'", start)
        self.assertIn("document.getElementById('foundingPartnerConsent')?.focus();", self.html[start:end])

    def test_checkout_retry_reuses_saved_partner_lead(self):
        self.assertIn("window.__hofFoundingPartnerLeadId", self.html)
        self.assertIn("if (!partnerLeadId)", self.html)
        self.assertIn("partner_lead_id: partnerLeadId", self.html)

    def test_unfinished_partner_application_is_saved_privately_before_submission(self):
        self.assertIn("const partnerDraftStorageKey = 'hof_founding_partner_application_draft_v1'", self.html)
        self.assertIn("function savePartnerApplicationDraft()", self.html)
        self.assertIn("function restorePartnerApplicationDraft()", self.html)
        self.assertIn("Your saved application was restored in this browser session.", self.html)
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
        self.assertIn('Application already saved', self.html)
        self.assertIn('No checkout or payment is available during beta.', self.html)
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
            "Founding Partner Beta Application Saved",
            "Founding Partner Application Saved",
            "Founding Partner Paid Stripe Checkout Opened",
            "Founding Partner Checkout Cancelled",
            "Founding Partner Checkout Completed",
            "Founding Partner Paid Checkout Failed",
        ):
            self.assertIn(event, self.html)
        self.assertIn("partner_application_essentials_ready", self.html)
        self.assertIn("partner_application_beta_terms_acknowledged", self.html)
        self.assertIn("partner_application_save_failed", self.html)
        self.assertIn("partner_checkout_start_failed", self.html)
        self.assertIn("window.selectFoundingPartnerTier('founding_pilot', false)", self.html)

    def test_selected_tier_explains_complimentary_beta_terms(self):
        self.assertIn('id="foundingPartnerCheckoutNote"', self.html)
        self.assertIn("All partner placements are complimentary during beta. No checkout, payment, or automatic paid conversion applies.", self.html)

    def test_selected_tier_stays_accurately_named_in_the_application(self):
        self.assertIn('id="foundingPartnerTierLabel"', self.html)
        self.assertIn("'Selected placement preference'", self.html)
        self.assertIn("'Please acknowledge the ' + selectedTier.label + ' terms before submitting.'", self.html)

    def test_custom_multi_market_request_never_opens_price_based_checkout(self):
        start = self.html.index("window.submitFoundingPartnerLead = async function")
        end = self.html.index("function setupPartnerOnboardingModal", start)
        submit = self.html[start:end]
        self.assertIn("if (PARTNER_BETA_ACTIVE)", submit)
        self.assertLess(submit.index("if (PARTNER_BETA_ACTIVE)"), submit.index("if (payload.preferred_model === 'discuss')"))
        self.assertIn("No checkout or payment is available during beta.", submit)

    def test_short_required_checkout_intake_precedes_the_optional_tier_comparison(self):
        essentials = self.html.index('id="foundingPartnerEssentials"')
        comparison = self.html.index('id="foundingPartnerTierComparison"')
        placement = self.html.index('class="partner-placement-wrap"')
        self.assertLess(essentials, comparison)
        self.assertLess(comparison, placement)
        self.assertIn('Compare or change your placement preference', self.html)
        self.assertIn("window.jumpToFoundingPartnerEssentials", self.html)
        self.assertIn("essentials.scrollIntoView({ behavior: 'smooth', block: 'start' })", self.html)
        self.assertIn("Founding Partner Essentials Jumped", self.html)
        self.assertIn("partner_application_tier_selected", self.html)
        self.assertIn("partner_application_essentials_opened", self.html)

    def test_admin_partner_leads_have_privacy_limited_follow_up_action(self):
        self.assertIn("partnerLeadFollowUpAction", self.html)
        self.assertIn("Email partner", self.html)
        self.assertIn("partner onboarding next step:", self.html)
        self.assertIn("contact_email", self.html)

    def test_homepage_audience_grid_links_to_partner_offer(self):
        self.assertIn("<h3>Service Partners</h3>", self.html)
        self.assertIn("Complimentary beta · no payment or automatic conversion", self.html)
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

    def test_campaign_links_can_preselect_only_existing_placement_levels(self):
        self.assertIn("const partnerCampaignTiers = new Set(['founding_pilot','monthly_placement','market_exclusive']);", self.html)
        self.assertIn("const partnerCampaignChannels = new Set(['direct_outreach','email','social','referral','local_event','print','organic','pwa_shortcut','partner_receipt','owned_directory']);", self.html)
        self.assertIn("function campaignPartnerChannel()", self.html)
        self.assertIn("const partnerCampaignChannelKey = 'hof_partner_landing_channel';", self.html)
        self.assertIn("sessionStorage.getItem(partnerCampaignChannelKey)", self.html)
        self.assertIn("acquisition_channel: campaignPartnerChannel()", self.html)
        self.assertIn("if (partnerCampaignChannels.has(source)) return source;", self.html)
        self.assertIn("source === 'homeofferflow_admin' && partnerCampaignChannels.has(medium)", self.html)
        self.assertIn("campaignChannel: campaign.channel || null", self.html)
        self.assertIn("params().get('partner_tier')", self.html)
        self.assertIn("return partnerCampaignTiers.has(tier) ? tier : '';", self.html)
        self.assertIn("window.selectFoundingPartnerTier?.(tier, false);", self.html)
        self.assertIn("campaignTier: campaign.tier || null", self.html)

    def test_server_marks_beta_applications_and_returns_the_program_contract(self):
        api = API_PATH.read_text(encoding="utf-8")
        self.assertIn("PARTNER_BETA_ACTIVE = True", api)
        self.assertIn('"partner_program": "beta" if PARTNER_BETA_ACTIVE else "commercial"', api)
        self.assertIn("'partner_program': payload['partner_program']", api)
        checkout = api[api.index("def _create_partner_checkout("):api.index("def _create_partner_checkout(") + 500]
        self.assertIn("if PARTNER_BETA_ACTIVE", checkout)
        self.assertLess(checkout.index("if PARTNER_BETA_ACTIVE"), checkout.index("stripe_secret_key = STRIPE_SECRET_KEY"))

    def test_beta_admin_and_campaign_materials_use_zero_dollar_terms(self):
        self.assertIn('id="partnerMonthlyFee" type="number" min="0" max="0" value="0" readonly', self.html)
        self.assertIn("All partner placements have the same $0 beta fee.", self.html)
        self.assertIn("All partners receive the same no-charge beta terms", self.html)
        self.assertIn("$0 · complimentary during beta", self.html)
        invitation_start = self.html.index("function partnerCampaignInvitation()")
        invitation_end = self.html.index("window.copyPartnerCampaignLink", invitation_start)
        self.assertNotIn("application and checkout", self.html[invitation_start:invitation_end])

    def test_homepage_partner_offer_structured_data_is_valid(self):
        blocks = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', self.html, re.S)
        structured_data = [json.loads(block) for block in blocks]
        def walk(value):
            if isinstance(value, dict):
                yield value
                for child in value.values():
                    yield from walk(child)
            elif isinstance(value, list):
                for child in value:
                    yield from walk(child)
        offers = [item for value in structured_data for item in walk(value)
                  if item.get("@type") == "Offer" and item.get("name") == "Founding Partner Placement"]
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["price"], "0")
        self.assertIn("no payment or automatic paid conversion", offers[0]["description"])


if __name__ == "__main__":
    unittest.main()
