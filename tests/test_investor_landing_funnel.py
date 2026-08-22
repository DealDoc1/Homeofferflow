from pathlib import Path
import importlib.util
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
API_PATH = ROOT / "api" / "fsbo-lead.py"
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
INVESTORS = (ROOT / "investors.html").read_text(encoding="utf-8")
INVESTOR_GUIDE = (ROOT / "texas-investor-offer-guide.html").read_text(encoding="utf-8")
INVESTOR_GUIDE_METRICS = (ROOT / "assets" / "investor-offer-guide-metrics.js").read_text(encoding="utf-8")
VERCEL = (ROOT / "vercel.json").read_text(encoding="utf-8")


class InvestorLandingFunnelTests(unittest.TestCase):
    def test_searchable_investor_route_and_passwordless_entry_reuse_existing_workspace(self):
        self.assertIn('"source": "/investors"', VERCEL)
        self.assertIn('"destination": "/investors.html"', VERCEL)
        self.assertIn('href="/?investor=1"', INVESTORS)
        self.assertIn('href="/investors"', INDEX)
        self.assertIn("if (params().get('investor') === '1')", INDEX)
        self.assertIn("cleanUrl.searchParams.delete('investor')", INDEX)
        self.assertIn("window.openAuthModal?.('investor')", INDEX)
        self.assertIn("if (window.hofAuth?.session)", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'dashboard' })", INDEX)
        self.assertIn("hof_investor_landing_workspace", INDEX)
        self.assertIn("investor_landing_workspace_handoff", INDEX)
        self.assertIn("const investorLandingSource = investorRouteParams.get('utm_source') === 'texas_investor_offer_guide'", INDEX)
        self.assertIn("localStorage.setItem('hof_investor_landing_source', investorLandingSource)", INDEX)
        self.assertIn("localStorage.getItem('hof_investor_landing_source') === 'texas_investor_offer_guide'", INDEX)

    def test_public_endpoint_and_page_record_only_aggregate_investor_landing_events(self):
        self.assertIn("INVESTOR_LANDING_EVENT_TYPES", API)
        self.assertIn("def _record_investor_landing_event(data):", API)
        self.assertIn('"investor_landing_viewed": "viewed"', API)
        self.assertIn('"investor_landing_cta_selected": "selected"', API)
        self.assertIn('"investor_offer_guide_viewed": "viewed"', API)
        self.assertIn('"investor_offer_guide_cta_selected": "selected"', API)
        self.assertIn("INVESTOR_LANDING_CHANNELS", API)
        self.assertIn("Unsupported investor landing channel.", API)
        self.assertIn('"channel": channel', API)
        self.assertIn("Unsupported investor landing event.", API)
        self.assertIn("'investor_landing_event'", API)
        self.assertIn('"investor_offer_guide" if event_type.startswith("investor_offer_guide_") else "investor_landing"', API)
        self.assertIn("sessionStorage.getItem(k)", INVESTORS)
        self.assertIn("request_type:'investor_landing_event'", INVESTORS)
        self.assertIn("investor_landing_viewed", INVESTORS)
        self.assertIn("investor_landing_cta_selected", INVESTORS)
        self.assertIn("new URLSearchParams(window.location.search).get('utm_source')", INVESTORS)
        self.assertIn("'direct_outreach','email','social','referral','local_event','print'", INVESTORS)

    def test_investor_landing_channel_is_allowlisted_without_visitor_identity(self):
        spec = importlib.util.spec_from_file_location("investor_landing_channel", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        captured = []
        with patch.object(api, "_record_partner_checkout_event", side_effect=lambda *args: captured.append(args)):
            api._record_investor_landing_event({"event_type": "investor_landing_cta_selected", "channel": "referral"})
            with self.assertRaisesRegex(ValueError, "Unsupported investor landing channel"):
                api._record_investor_landing_event({"event_type": "investor_landing_viewed", "channel": "untrusted"})
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0][0], "investor_landing_cta_selected")
        self.assertEqual(captured[0][3], {"surface": "investor_landing", "role": "investor", "channel": "referral"})

    def test_investor_guide_tracks_only_aggregate_workspace_intent(self):
        self.assertIn('/assets/investor-offer-guide-metrics.js', INVESTOR_GUIDE)
        self.assertIn("record('investor_offer_guide_viewed')", INVESTOR_GUIDE_METRICS)
        self.assertIn("record('investor_offer_guide_cta_selected')", INVESTOR_GUIDE_METRICS)
        self.assertIn("request_type: 'investor_landing_event'", INVESTOR_GUIDE_METRICS)
        self.assertNotIn('location.href', INVESTOR_GUIDE_METRICS)
        self.assertNotIn('utm_source', INVESTOR_GUIDE_METRICS)

    def test_admin_reports_investor_workspace_landing_conversion(self):
        for expected in (
            '"investorLandingViewCount"', '"investorLandingCtaCount"', '"investorLandingCtaRate"',
            '"investorLandingWorkspaceHandoffUserCount"', '"investorLandingWorkspaceHandoffRate"',
            '"investorOfferGuideViewCount"', '"investorOfferGuideCtaCount"', '"investorOfferGuideCtaRate"',
            '"investorLandingViewCountsByChannel"', '"investorLandingCtaCountsByChannel"',
            'investor_landing_workspace_handoff',
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("Investor Workspace Funnel", INDEX)
        self.assertIn("investorLandingCtaRate", INDEX)
        self.assertIn("investorLandingWorkspaceHandoffUserCount", INDEX)
        self.assertIn("investorLandingWorkspaceHandoffRate", INDEX)
        self.assertIn("Investor offer guide:", INDEX)
        self.assertIn("Channel views / sign-ins", INDEX)
        self.assertIn("investorLandingViewCountsByChannel?.referral", INDEX)


if __name__ == "__main__":
    unittest.main()
