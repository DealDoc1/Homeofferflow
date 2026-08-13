from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class AdminSellerFollowUpTests(unittest.TestCase):
    def test_seller_follow_up_uses_package_context_without_exposing_new_data(self):
        self.assertIn("sellerLeadFollowUpAction", INDEX)
        self.assertIn("HomeOfferFlow seller follow-up", INDEX)
        self.assertIn("Package interest: ${packageName}.", INDEX)
        self.assertIn("Partner interests: ${partners}.", INDEX)
        self.assertIn("seller_follow_up_email_started", INDEX)
        self.assertIn("sellerFollowUpEmailStartCount", INDEX)
        self.assertIn("sellerFollowUpEmailStartRate", INDEX)
        self.assertIn("sellerCampaignLeadCount", INDEX)
        self.assertIn("sellerCampaignMediumCounts", INDEX)
        self.assertIn("Tracked campaign leads:", INDEX)
        self.assertIn("sellerReviewAttestationGapCount", INDEX)
        self.assertIn("sellerReviewAttestationGapRate", INDEX)
        self.assertIn("function adminEventMetadata", INDEX)
        self.assertIn('>Follow up</a>', INDEX)

    def test_paid_partner_queue_reuses_tracked_follow_up_action(self):
        queue_start = INDEX.index("if (type === 'paid-partner-activation')")
        queue_end = INDEX.index("if (type === 'seller-leads')", queue_start)
        queue = INDEX[queue_start:queue_end]
        self.assertIn("partnerLeadFollowUpAction(row)", queue)


if __name__ == "__main__":
    unittest.main()
