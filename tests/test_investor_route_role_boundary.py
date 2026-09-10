"""Regression coverage for preserving an intentional investor entry path."""

from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class InvestorRouteRoleBoundaryTests(unittest.TestCase):
    def test_agent_session_does_not_replace_investor_route_with_agent_dashboard(self):
        start = HTML.index("if (params().get('investor') === '1')")
        end = HTML.index("if (params().get('partner_onboarding'))", start)
        route = HTML[start:end]

        self.assertIn("window.hofAuth?.session && window.hofAuth?.role === 'investor'", route)
        self.assertIn("else if (window.hofAuth?.session)", route)
        self.assertIn("showInvestorAccountRouteNotice();", route)

    def test_role_mismatch_notice_preserves_separate_saved_details_boundary(self):
        self.assertIn("const showInvestorAccountRouteNotice = () =>", HTML)
        self.assertIn("id = 'investorAccountRouteNotice'", HTML)
        self.assertIn("You’re signed in to an Agent Account.", HTML)
        self.assertIn("Investor workspaces keep saved deal details separate.", HTML)


if __name__ == "__main__":
    unittest.main()
