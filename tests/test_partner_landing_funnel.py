from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
PARTNERS = (ROOT / "partners.html").read_text(encoding="utf-8")


class PartnerLandingFunnelTests(unittest.TestCase):
    def test_public_endpoint_only_accepts_allowlisted_aggregate_events(self):
        self.assertIn("PARTNER_LANDING_EVENT_TYPES", API)
        self.assertIn("def _record_partner_landing_event(data):", API)
        self.assertIn('"partner_landing_viewed": "viewed"', API)
        self.assertIn('"partner_landing_cta_selected": "selected"', API)
        self.assertIn('"partner_application_opened": "application_opened"', API)
        self.assertIn('"partner_application_essentials_focused": "essentials_focused"', API)
        self.assertIn('"partner_directory_application_selected": "application_selected"', API)
        self.assertIn('"partner_directory_pricing_selected": "pricing_selected"', API)
        self.assertIn("Unsupported partner landing event.", API)
        self.assertIn("Unsupported partner tier.", API)
        self.assertIn("Unsupported partner category.", API)
        self.assertIn("'partner_landing_event'", API)
        self.assertIn('event_type in {"partner_directory_application_selected", "partner_directory_pricing_selected"}', API)

    def test_partner_page_records_one_aggregate_stage_per_session_and_selection(self):
        self.assertIn("recordAggregateFunnelEvent", PARTNERS)
        self.assertIn("sessionStorage.getItem(key)", PARTNERS)
        self.assertIn("request_type: 'partner_landing_event'", PARTNERS)
        self.assertIn("event_type: eventType", PARTNERS)
        self.assertIn("partner_landing_viewed", PARTNERS)
        self.assertIn("partner_landing_cta_selected", PARTNERS)
        self.assertIn("keepalive: true", PARTNERS)
        self.assertIn("const campaignChannel = medium === 'installed_app' ? 'pwa_shortcut' : medium || 'direct';", PARTNERS)
        self.assertIn("channel: campaignChannel", PARTNERS)
        self.assertIn("channel: channelValue", PARTNERS)
        self.assertIn("PARTNER_LANDING_CHANNELS", API)

    def test_partner_page_respects_notched_mobile_safe_areas(self):
        self.assertIn('viewport-fit=cover', PARTNERS)
        self.assertIn('env(safe-area-inset-top)', PARTNERS)
        self.assertIn('env(safe-area-inset-bottom)', PARTNERS)

    def test_partner_page_reduces_checkout_uncertainty_without_changing_price_or_claims(self):
        self.assertIn("Start no-charge application", PARTNERS)
        self.assertIn("Start with a no-charge application", PARTNERS)
        self.assertIn("No need to finish in one sitting", PARTNERS)
        guide = (ROOT / "texas-home-service-partner-guide.html").read_text(encoding="utf-8")
        self.assertIn("Texas home-service partner placement guide", guide)
        self.assertIn("/partners?utm_source=texas_home_service_partner_guide", guide)
        self.assertIn("before any payment", PARTNERS)
        self.assertIn("Apply for Core — no charge yet", PARTNERS)
        self.assertIn("First 90 days, then $149/month", PARTNERS)
        self.assertIn("not a referral program", PARTNERS)

    def test_partner_page_states_when_the_paid_launch_period_begins(self):
        self.assertIn("When does the 90-day founding launch period begin?", PARTNERS)
        self.assertIn("The 90-day launch period begins when secure Stripe Checkout is completed.", PARTNERS)
        self.assertIn("Payment does not make a placement public", PARTNERS)

    def test_partner_page_can_open_the_existing_essential_fields_without_skipping_disclosures(self):
        self.assertIn("partner_quick_start=1", PARTNERS)
        self.assertIn("it takes about a minute", PARTNERS)
        self.assertIn("function partnerQuickStartRequested()", INDEX)
        self.assertIn("window.jumpToFoundingPartnerEssentials?.()", INDEX)
        self.assertIn("All essentials, consent, and the secure", INDEX)
        self.assertIn("Stripe review remain required", INDEX)
        self.assertIn('id="foundingPartnerEssentials"', INDEX)
        self.assertIn('id="foundingPartnerTierComparison"', INDEX)
        self.assertIn("document.getElementById('foundingPartnerType')?.focus()", INDEX)

    def test_quick_start_begins_at_the_first_unfinished_essential(self):
        start = INDEX.index("window.jumpToFoundingPartnerEssentials = function")
        end = INDEX.index("window.closeFoundingPartnerModal", start)
        quick_start = INDEX[start:end]
        self.assertIn("Always begin at the first unfinished required field", quick_start)
        self.assertIn("['foundingPartnerType'", quick_start)
        self.assertIn("['foundingPartnerCompany'", quick_start)
        self.assertIn("const firstIncomplete", quick_start)
        self.assertIn("document.getElementById(firstIncomplete)?.focus()", quick_start)

    def test_partner_funnel_measures_required_field_reach_without_collecting_applicant_data(self):
        self.assertIn("function recordPartnerEssentialsFocused()", INDEX)
        self.assertIn("partner_application_essentials_focused", INDEX)
        self.assertIn("#foundingPartnerEssentials input, #foundingPartnerEssentials select", INDEX)
        self.assertIn('"partnerApplicationEssentialsFocusCount"', ADMIN)
        self.assertIn('"partnerApplicationEssentialsFocusRate"', ADMIN)
        self.assertIn("partnerApplicationEssentialsFocusRate", INDEX)

    def test_admin_returns_aggregate_partner_conversion(self):
        for expected in (
            '"partnerLandingViewCount"',
            '"partnerLandingCtaCount"',
            '"partnerLandingCtaRate"',
            '"partnerApplicationOpenCount"',
            '"partnerApplicationOpenRate"',
            '"partnerApplicationEssentialsFocusCount"',
            '"partnerApplicationEssentialsFocusRate"',
            '"partnerLandingTierCtaCounts"',
            '"partnerLandingCategoryCtaCounts"',
            '"partnerDirectoryApplicationStartCount"',
            '"partnerDirectoryPricingSelectionCount"',
            "partner_landing_event_types",
            "partner_landing_tier_cta_counts",
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("partnerLandingViewCount", INDEX)
        self.assertIn("partnerLandingCtaRate", INDEX)
        self.assertIn("partnerApplicationOpenCount", INDEX)
        self.assertIn("partnerDirectoryApplicationStartCount", INDEX)
        self.assertIn("Landing-tier interest:", INDEX)
        self.assertIn("Landing-category interest:", INDEX)
        self.assertIn("partnerLandingChannelCounts", INDEX)

    def test_modal_open_is_a_distinct_privacy_safe_partner_funnel_stage(self):
        self.assertIn("function recordPartnerApplicationOpened", INDEX)
        self.assertIn("event_type:'partner_application_opened'", INDEX)
        self.assertIn("hof_partner_application_opened_", INDEX)
        self.assertIn("new application modal open", INDEX)


if __name__ == "__main__":
    unittest.main()
