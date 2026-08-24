from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SELLERS = (ROOT / "sellers.html").read_text(encoding="utf-8")
FSBO_GUIDE = (ROOT / "texas-fsbo-guide.html").read_text(encoding="utf-8")
FSBO_GUIDE_METRICS = (ROOT / "assets" / "fsbo-guide-metrics.js").read_text(encoding="utf-8")


class FsboLandingFunnelTests(unittest.TestCase):
    def test_private_fsbo_intake_progress_is_available_as_aggregate_only(self):
        self.assertIn('"fsbo_intake_opened": "opened"', API)
        self.assertIn('"fsbo_package_selected": "selected"', API)
        self.assertIn('"fsbo_request_saved": "saved"', API)
        self.assertIn("FSBO Seller Request Submission Started", INDEX)
        self.assertIn("sellerIntakeEventCounts", ADMIN)
        self.assertIn("sellerPackageSelectionCounts", ADMIN)
    def test_public_endpoint_only_accepts_allowlisted_aggregate_events(self):
        self.assertIn("FSBO_LANDING_EVENT_TYPES", API)
        self.assertIn("def _record_fsbo_landing_event(data):", API)
        self.assertIn('"fsbo_landing_viewed": "viewed"', API)
        self.assertIn('"fsbo_landing_cta_selected": "selected"', API)
        self.assertIn('"fsbo_support_paths_expanded": "expanded"', API)
        self.assertIn('"fsbo_guide_viewed": "viewed"', API)
        self.assertIn('"fsbo_guide_cta_selected": "selected"', API)
        self.assertIn('"pwa_seller_plan_opened": "opened"', API)
        self.assertIn('"fsbo_provider_directory_opened": "opened"', API)
        self.assertIn("Unsupported seller landing event.", API)
        self.assertIn("Unsupported seller package.", API)
        self.assertIn("'fsbo_landing_event'", API)
        self.assertIn('else "seller_landing"', API)
        self.assertIn('"pwa_seller_plan"', API)
        self.assertIn('"fsbo_guide"', API)

    def test_fsbo_guide_records_aggregate_views_and_free_plan_clicks_only(self):
        self.assertIn('/assets/fsbo-guide-metrics.js', FSBO_GUIDE)
        self.assertIn("record('fsbo_guide_viewed')", FSBO_GUIDE_METRICS)
        self.assertIn("record('fsbo_guide_cta_selected')", FSBO_GUIDE_METRICS)
        self.assertIn('data-fsbo-package-cta', FSBO_GUIDE)
        self.assertIn("new URL(link.href, window.location.origin).searchParams.get('seller_package')", FSBO_GUIDE_METRICS)
        self.assertIn("service_level: packageKey", FSBO_GUIDE_METRICS)
        self.assertIn("'launch_kit'", FSBO_GUIDE_METRICS)
        self.assertIn("'offer_review'", FSBO_GUIDE_METRICS)
        self.assertIn("sessionStorage.getItem(key)", FSBO_GUIDE_METRICS)
        self.assertIn("request_type: 'fsbo_landing_event'", FSBO_GUIDE_METRICS)
        self.assertIn("service_level: 'free_intake'", FSBO_GUIDE_METRICS)
        self.assertNotIn("utm_source", FSBO_GUIDE_METRICS)
        self.assertNotIn("location.href", FSBO_GUIDE_METRICS)

    def test_seller_page_records_each_aggregate_stage_once_per_browser_session(self):
        self.assertIn("Get my free seller plan", SELLERS)
        self.assertIn("Two details to begin: your property address and email.", SELLERS)
        self.assertIn("You receive the free seller plan immediately after submitting.", SELLERS)
        self.assertIn("recordAggregateFunnelEvent", SELLERS)
        self.assertIn("sessionStorage.getItem(key)", SELLERS)
        self.assertIn("request_type: 'fsbo_landing_event'", SELLERS)
        self.assertIn("event_type: eventType", SELLERS)
        self.assertIn("fsbo_landing_viewed", SELLERS)
        self.assertIn("fsbo_landing_cta_selected", SELLERS)
        self.assertIn("fsbo_support_paths_expanded", SELLERS)
        self.assertIn("sellerLandingSupportPathsExpandedCount", ADMIN)
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
        self.assertIn('"fsboGuideViewCount"', ADMIN)
        self.assertIn('"fsboGuideCtaCount"', ADMIN)
        self.assertIn('"fsboGuideCtaRate"', ADMIN)
        self.assertIn("Texas FSBO Guide Funnel", INDEX)

    def test_seller_pwa_shortcut_is_aggregate_only_and_admin_measurable(self):
        self.assertIn("hof_pwa_seller_plan_shortcut_recorded", INDEX)
        self.assertIn("event_type: 'pwa_seller_plan_opened'", INDEX)
        self.assertIn('"pwaSellerPlanShortcutCount"', ADMIN)
        self.assertIn("pwa_seller_plan_shortcut_count", ADMIN)

    def test_saved_seller_plan_can_offer_neutral_provider_discovery_without_tracking_personal_data(self):
        self.assertIn("window.openFsboProviderDirectory = function openFsboProviderDirectory()", INDEX)
        self.assertIn("event_type: 'fsbo_provider_directory_opened'", INDEX)
        self.assertIn("window.location.assign('/directory?' + query.toString())", INDEX)
        self.assertIn("Browse available providers", INDEX)
        self.assertIn('"fsboProviderDirectoryOpenCount"', ADMIN)


if __name__ == "__main__":
    unittest.main()
