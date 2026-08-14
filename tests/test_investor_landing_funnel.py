from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
INVESTORS = (ROOT / "investors.html").read_text(encoding="utf-8")
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

    def test_public_endpoint_and_page_record_only_aggregate_investor_landing_events(self):
        self.assertIn("INVESTOR_LANDING_EVENT_TYPES", API)
        self.assertIn("def _record_investor_landing_event(data):", API)
        self.assertIn('"investor_landing_viewed": "viewed"', API)
        self.assertIn('"investor_landing_cta_selected": "selected"', API)
        self.assertIn("Unsupported investor landing event.", API)
        self.assertIn("'investor_landing_event'", API)
        self.assertIn('"surface": "investor_landing"', API)
        self.assertIn("sessionStorage.getItem(k)", INVESTORS)
        self.assertIn("request_type:'investor_landing_event'", INVESTORS)
        self.assertIn("investor_landing_viewed", INVESTORS)
        self.assertIn("investor_landing_cta_selected", INVESTORS)

    def test_admin_reports_investor_workspace_landing_conversion(self):
        for expected in ('"investorLandingViewCount"', '"investorLandingCtaCount"', '"investorLandingCtaRate"'):
            self.assertIn(expected, ADMIN)
        self.assertIn("Investor Workspace Funnel", INDEX)
        self.assertIn("investorLandingCtaRate", INDEX)


if __name__ == "__main__":
    unittest.main()
