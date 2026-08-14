from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
BUYERS = (ROOT / "buyers.html").read_text(encoding="utf-8")


class HomebuyerLandingFunnelTests(unittest.TestCase):
    def test_public_endpoint_only_accepts_allowlisted_aggregate_events_and_channels(self):
        self.assertIn("HOMEBUYER_LANDING_EVENT_TYPES", API)
        self.assertIn("HOMEBUYER_LANDING_CHANNELS", API)
        self.assertIn("def _record_homebuyer_landing_event(data):", API)
        self.assertIn('"homebuyer_landing_viewed": "viewed"', API)
        self.assertIn('"homebuyer_landing_cta_selected": "selected"', API)
        self.assertIn("Unsupported homebuyer landing event.", API)
        self.assertIn("Unsupported homebuyer landing channel.", API)
        self.assertIn("'homebuyer_landing_event'", API)
        self.assertIn('"surface": "homebuyer_landing"', API)

    def test_buyer_landing_records_each_stage_once_without_buyer_or_offer_details(self):
        self.assertIn("recordAggregateFunnelEvent", BUYERS)
        self.assertIn("sessionStorage.getItem(key)", BUYERS)
        self.assertIn("request_type: 'homebuyer_landing_event'", BUYERS)
        self.assertIn("homebuyer_landing_viewed", BUYERS)
        self.assertIn("homebuyer_landing_cta_selected", BUYERS)
        self.assertIn("channel: safeChannel", BUYERS)
        self.assertIn("keepalive: true", BUYERS)

    def test_public_buyer_cta_opens_the_guided_offer_workflow_on_a_fresh_visit(self):
        self.assertIn('href="/?buyer=1"', BUYERS)
        self.assertIn("if (params().get('buyer') === '1') setTimeout(() =>", INDEX)
        self.assertIn("cleanUrl.searchParams.delete('buyer')", INDEX)
        self.assertIn("setAudience('homebuyer')", INDEX)
        self.assertIn("window.beginOfferFrom?.('buyer_landing')", INDEX)
        self.assertNotIn("function consumeHomebuyerLandingEntry()", INDEX)

    def test_admin_reports_aggregate_buyer_landing_conversion(self):
        for expected in (
            '"homebuyerLandingViewCount"',
            '"homebuyerLandingCtaCount"',
            '"homebuyerLandingCtaRate"',
            "homebuyer_landing_view_count",
            "homebuyer_landing_cta_count",
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("Homebuyer $99 Funnel", INDEX)
        self.assertIn("homebuyerLandingCtaRate", INDEX)


if __name__ == "__main__":
    unittest.main()
