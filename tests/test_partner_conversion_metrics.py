import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PartnerConversionMetricTests(unittest.TestCase):
    def test_admin_payload_counts_paid_partner_funnel(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"paidPartnerLeadCount"', source)
        self.assertIn('"sandboxPartnerLeadCount"', source)
        self.assertIn('_is_sandbox_partner_lead', source)
        self.assertIn('"partnerOnboardingReadyCount"', source)
        self.assertIn('"partnerOnboardingAccessMissingCount"', source)
        self.assertIn('"partnerActivationRate"', source)
        self.assertIn('"paidPartnerAgreementConfirmedCount"', source)
        self.assertIn('"paidPartnerAgreementConfirmationRate"', source)
        self.assertIn('"paidPartnerActivationQueueAgedCount"', source)
        self.assertIn('"partnerActivationAvgDays"', source)
        self.assertIn('"partnerCheckoutEventCounts"', source)
        self.assertIn('"partnerCheckoutStripeOpenRate"', source)
        self.assertIn('"partnerCheckoutCompletionRate"', source)
        self.assertIn('"partnerCampaignCategoryCounts"', source)
        self.assertIn('"partnerCampaignTierCounts"', source)
        self.assertIn('partner_campaign_categories', source)
        self.assertIn('partner_campaign_tiers', source)
        self.assertIn('founding_partner_stripe_checkout_opened', source)

    def test_admin_dashboard_surfaces_paid_partner_funnel(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('paidPartnerLeadCount', source)
        self.assertIn('onboarding-ready', source)
        self.assertIn('partnerOnboardingAccessMissingCount', source)
        self.assertIn('need a fresh secure setup link', source)
        self.assertIn('Live Partner Leads', source)
        self.assertIn('sandboxPartnerLeadCount', source)
        self.assertIn('paidPartnerAgreementConfirmationRate', source)
        self.assertIn('paidPartnerActivationQueueAgedCount', source)
        self.assertIn('time to activation', source)
        self.assertIn('partnerCheckoutStripeOpenRate', source)
        self.assertIn('Public checkout:', source)
        self.assertIn('Campaign category opens:', source)
        self.assertIn('Campaign tier opens:', source)


if __name__ == "__main__":
    unittest.main()
