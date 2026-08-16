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
        self.assertIn("agreement_confirmed_source_lead_ids", source)
        self.assertIn('"paidPartnerAgreementConfirmationRate"', source)
        self.assertIn('"paidPartnerActivationQueueAgedCount"', source)
        self.assertIn('"partnerActivationAvgDays"', source)
        self.assertIn('"partnerCheckoutEventCounts"', source)
        self.assertIn('"partnerCheckoutStripeOpenRate"', source)
        self.assertIn('"partnerCheckoutCompletionRate"', source)
        self.assertIn('"partnerCheckoutRecoveryAvailableCount"', source)
        self.assertIn('"partnerCheckoutRecoveryStripeOpenCount"', source)
        self.assertIn('partner_checkout_recovery_stripe_open_count', source)
        self.assertIn('"partnerCampaignCategoryCounts"', source)
        self.assertIn('"partnerCampaignTierCounts"', source)
        self.assertIn('"partnerCampaignChannelCounts"', source)
        self.assertIn('partner_campaign_categories', source)
        self.assertIn('partner_campaign_tiers', source)
        self.assertIn('partner_campaign_channels', source)
        self.assertIn('founding_partner_stripe_checkout_opened', source)

    def test_admin_payload_counts_only_allowlisted_seller_package_requests(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"sellerPackageRequestCounts"', source)
        self.assertIn('"sellerCampaignLeadCount"', source)
        self.assertIn('"sellerCampaignMediumCounts"', source)
        self.assertIn('seller_campaign_medium_counts', source)
        self.assertIn('tracked_seller_campaign_leads', source)
        self.assertIn('seller_package_catalog', source)
        self.assertIn('package_key in seller_package_catalog', source)
        self.assertIn('lead.get("service_level")', source)

    def test_admin_dashboard_surfaces_paid_partner_funnel(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('paidPartnerLeadCount', source)
        self.assertIn('onboarding-ready', source)
        self.assertIn('partnerOnboardingAccessMissingCount', source)
        self.assertIn('need secure setup access', source)
        self.assertIn('Restore setup access', source)
        self.assertIn('Live Partner Leads', source)
        self.assertIn('sandboxPartnerLeadCount', source)
        self.assertIn('paidPartnerAgreementConfirmationRate', source)
        self.assertIn('paidPartnerActivationQueueAgedCount', source)
        self.assertIn('time to activation', source)
        self.assertIn('partnerCheckoutStripeOpenRate', source)
        self.assertIn('Public checkout:', source)
        self.assertIn('Canceled-checkout recovery:', source)
        self.assertIn('Campaign category opens:', source)
        self.assertIn('Campaign tier opens:', source)
        self.assertIn('Campaign channel opens:', source)
        self.assertIn('Submitted package demand:', source)
        self.assertIn('Tracked campaign leads:', source)
        self.assertIn('sellerPackageRequestCounts', source)

    def test_partner_workspace_can_create_allowlisted_campaign_links(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('Partner Campaign Link Toolkit', source)
        self.assertIn('copyPartnerCampaignLink()', source)
        self.assertIn('copyPartnerCampaignInvitation()', source)
        self.assertIn('previewPartnerCampaignLink()', source)
        self.assertIn("const partnerCampaignCategories = new Set", source)
        self.assertIn("const partnerCampaignTiers = new Set", source)
        self.assertIn("const partnerCampaignChannels = new Set", source)
        self.assertIn("https://www.homeofferflow.com/partners?${params.toString()}", source)
        self.assertIn("new URLSearchParams({", source)
        self.assertIn("partnerCampaignCategories.has(category)", source)
        self.assertIn("partnerCampaignTiers.has(tier)", source)
        self.assertIn("partnerCampaignChannels.has(channel)", source)
        self.assertIn('id="partnerCampaignChannel"', source)
        self.assertIn('id="partnerCampaignName"', source)
        self.assertIn("params.set('utm_medium', channel)", source)
        self.assertIn("Partner Campaign Link Copied", source)
        self.assertIn("Partner Campaign Invitation Copied", source)
        self.assertIn("not referrals, required provider selection, transactions, or closings", source)


if __name__ == "__main__":
    unittest.main()
