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
        self.assertIn("Add optional placement preferences now", self.html)
        required_end = self.html.index('<div aria-hidden="true"', self.html.index('Start with the essentials.'))
        required_start = self.html.index('Start with the essentials.')
        required_area = self.html[required_start:required_end]
        self.assertLess(required_area.index('foundingPartnerMarket'), required_area.index('partner-optional-details'))
        self.assertGreater(required_area.index('foundingPartnerPhone'), required_area.index('partner-optional-details'))

    def test_checkout_retry_reuses_saved_partner_lead(self):
        self.assertIn("window.__hofFoundingPartnerLeadId", self.html)
        self.assertIn("if (!partnerLeadId)", self.html)
        self.assertIn("partner_lead_id: partnerLeadId", self.html)

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
        self.assertIn("window.selectFoundingPartnerTier('monthly_placement', false)", self.html)

    def test_selected_tier_makes_the_secure_checkout_handoff_explicit(self):
        self.assertIn('id="foundingPartnerCheckoutNote"', self.html)
        self.assertIn('Continue to Secure Checkout — ', self.html)
        self.assertIn('review the selected Founding Partner price and payment details in secure Stripe Checkout', self.html)
        self.assertIn('placement stays private until onboarding and written-agreement review are complete', self.html)

    def test_selected_tier_can_jump_to_the_short_required_checkout_intake(self):
        jump = self.html.index('id="foundingPartnerEssentialsJump"')
        comparison = self.html.index('class="partner-placement-wrap"')
        essentials = self.html.index('id="foundingPartnerEssentials"')
        self.assertLess(jump, comparison)
        self.assertLess(comparison, essentials)
        self.assertIn("window.jumpToFoundingPartnerEssentials", self.html)
        self.assertIn("essentials.scrollIntoView({ behavior: 'smooth', block: 'start' })", self.html)
        self.assertIn("Founding Partner Essentials Jumped", self.html)

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
            r'class="audience-card audience-card-link"[^>]+href="\?partner=1"',
        )
        self.assertIn("openFoundingPartnerModal();", self.html)

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
        self.assertIn("campaignChannel: campaign.channel || null", self.html)
        self.assertIn("params().get('partner_tier')", self.html)
        self.assertIn("return partnerCampaignTiers.has(tier) ? tier : '';", self.html)
        self.assertIn("window.selectFoundingPartnerTier?.(tier, false);", self.html)
        self.assertIn("campaignTier: campaign.tier || null", self.html)


if __name__ == "__main__":
    unittest.main()
