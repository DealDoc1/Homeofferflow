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

    def test_landing_page_records_each_stage_once_per_session(self):
        self.assertIn("recordAggregateLandingEvent", ONDEMAND)
        self.assertIn("sessionStorage.getItem(key)", ONDEMAND)
        self.assertIn('request_type: "ondemand_landing_event"', ONDEMAND)
        self.assertIn('recordAggregateLandingEvent("ondemand_landing_viewed")', ONDEMAND)
        self.assertIn('recordAggregateLandingEvent("ondemand_magic_link_requested")', ONDEMAND)
        self.assertIn('recordAggregateLandingEvent("ondemand_trial_terms_accepted")', ONDEMAND)
        self.assertIn("open it in this browser to return here", ONDEMAND)
        self.assertIn("keepalive: true", ONDEMAND)

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
            "ondemand_landing_view_count",
            "ondemand_terms_accepted_count",
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("onDemandLandingViewCount", INDEX)
        self.assertIn("onDemandMagicLinkRequestedCount", INDEX)
        self.assertIn("onDemandMagicLinkRequestRate", INDEX)
        self.assertIn("onDemandTermsAcceptedRate", INDEX)


if __name__ == "__main__":
    unittest.main()
