import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PartnerConversionMetricTests(unittest.TestCase):
    def test_admin_payload_counts_paid_partner_funnel(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"paidPartnerLeadCount"', source)
        self.assertIn('"partnerOnboardingReadyCount"', source)
        self.assertIn('"partnerActivationRate"', source)

    def test_admin_dashboard_surfaces_paid_partner_funnel(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('paidPartnerLeadCount', source)
        self.assertIn('onboarding-ready', source)
        self.assertIn('Partner Leads', source)


if __name__ == "__main__":
    unittest.main()
