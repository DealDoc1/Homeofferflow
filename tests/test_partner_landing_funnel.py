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
        self.assertIn('"partner_directory_application_selected": "application_selected"', API)
        self.assertIn("Unsupported partner landing event.", API)
        self.assertIn("Unsupported partner tier.", API)
        self.assertIn("Unsupported partner category.", API)
        self.assertIn("'partner_landing_event'", API)
        self.assertIn('"partner_directory" if event_type == "partner_directory_application_selected" else "partner_landing"', API)

    def test_partner_page_records_one_aggregate_stage_per_session_and_selection(self):
        self.assertIn("recordAggregateFunnelEvent", PARTNERS)
        self.assertIn("sessionStorage.getItem(key)", PARTNERS)
        self.assertIn("request_type: 'partner_landing_event'", PARTNERS)
        self.assertIn("event_type: eventType", PARTNERS)
        self.assertIn("partner_landing_viewed", PARTNERS)
        self.assertIn("partner_landing_cta_selected", PARTNERS)
        self.assertIn("keepalive: true", PARTNERS)

    def test_partner_page_reduces_checkout_uncertainty_without_changing_price_or_claims(self):
        self.assertIn("Start no-charge application", PARTNERS)
        self.assertIn("Start with a no-charge application", PARTNERS)
        self.assertIn("before any payment", PARTNERS)
        self.assertIn("Apply for Core — no charge yet", PARTNERS)
        self.assertIn("First 90 days, then $149/month", PARTNERS)
        self.assertIn("not a referral program", PARTNERS)

    def test_admin_returns_aggregate_partner_conversion(self):
        for expected in (
            '"partnerLandingViewCount"',
            '"partnerLandingCtaCount"',
            '"partnerLandingCtaRate"',
            '"partnerLandingTierCtaCounts"',
            '"partnerDirectoryApplicationStartCount"',
            "partner_landing_event_types",
            "partner_landing_tier_cta_counts",
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("partnerLandingViewCount", INDEX)
        self.assertIn("partnerLandingCtaRate", INDEX)
        self.assertIn("partnerDirectoryApplicationStartCount", INDEX)
        self.assertIn("Landing-tier interest:", INDEX)


if __name__ == "__main__":
    unittest.main()
