from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SELLERS = (ROOT / "sellers.html").read_text(encoding="utf-8")


class FsboLandingFunnelTests(unittest.TestCase):
    def test_public_endpoint_only_accepts_allowlisted_aggregate_events(self):
        self.assertIn("FSBO_LANDING_EVENT_TYPES", API)
        self.assertIn("def _record_fsbo_landing_event(data):", API)
        self.assertIn('"fsbo_landing_viewed": "viewed"', API)
        self.assertIn('"fsbo_landing_cta_selected": "selected"', API)
        self.assertIn("Unsupported seller landing event.", API)
        self.assertIn("Unsupported seller package.", API)
        self.assertIn("'fsbo_landing_event'", API)
        self.assertIn('"surface": "seller_landing"', API)

    def test_seller_page_records_each_aggregate_stage_once_per_browser_session(self):
        self.assertIn("recordAggregateFunnelEvent", SELLERS)
        self.assertIn("sessionStorage.getItem(key)", SELLERS)
        self.assertIn("request_type: 'fsbo_landing_event'", SELLERS)
        self.assertIn("event_type: eventType", SELLERS)
        self.assertIn("fsbo_landing_viewed", SELLERS)
        self.assertIn("fsbo_landing_cta_selected", SELLERS)
        self.assertIn("keepalive: true", SELLERS)

    def test_admin_returns_aggregate_conversion_without_public_details(self):
        for expected in (
            '"sellerLandingViewCount"',
            '"sellerLandingCtaCount"',
            '"sellerLandingCtaRate"',
            '"sellerLandingPackageCtaCounts"',
            "seller_landing_event_types",
            "seller_landing_package_cta_counts",
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("sellerLandingViewCount", INDEX)
        self.assertIn("sellerLandingCtaRate", INDEX)
        self.assertIn("Landing-path interest:", INDEX)


if __name__ == "__main__":
    unittest.main()
