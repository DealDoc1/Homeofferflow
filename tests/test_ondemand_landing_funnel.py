from pathlib import Path
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
        self.assertIn('recordAggregateLandingEvent("ondemand_trial_terms_accepted")', ONDEMAND)
        self.assertIn("open it in this browser to return here", ONDEMAND)
        self.assertIn("keepalive: true", ONDEMAND)

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

    def test_trial_renewal_date_refreshes_when_authenticated_enrollment_renders(self):
        self.assertIn("function refreshRenewalDate()", ONDEMAND)
        self.assertIn("refreshRenewalDate();\n        const signedIn", ONDEMAND)
        self.assertIn("same 60-day window checkout uses", ONDEMAND)

    def test_all_public_ondemand_trial_links_share_the_same_aggregate_entry_signal(self):
        self.assertIn("function recordOnDemandTrialEntry", INDEX)
        self.assertIn("agent_hero_secondary_cta", INDEX)
        self.assertIn("agent_hero_inline", INDEX)
        self.assertIn("hof_ondemand_trial_entry_selected", INDEX)

    def test_admin_reports_the_trial_conversion_ladder(self):
        for expected in (
            '"onDemandLandingViewCount"',
            '"onDemandTrialEntryCount"',
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
        self.assertIn("onDemandMagicLinkRequestedCount", INDEX)
        self.assertIn("onDemandMagicLinkRequestRate", INDEX)
        self.assertIn("onDemandTermsAcceptedRate", INDEX)
        self.assertIn("onDemandTransactionWorkflowSelectedCounts", INDEX)


if __name__ == "__main__":
    unittest.main()
