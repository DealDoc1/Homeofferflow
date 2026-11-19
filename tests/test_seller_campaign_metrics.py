import unittest

from lib.seller_campaign_metrics import build_seller_campaign_channel_counts


class SellerCampaignMetricsTests(unittest.TestCase):
    def test_build_readiness_lead_uses_fixed_source_bucket(self):
        counts = build_seller_campaign_channel_counts([{
            "source": "tracked_seller_landing",
            "utm_source": "build_readiness",
            "utm_medium": "owned_navigation",
            "utm_campaign": "equity_to_keys",
        }])
        self.assertEqual(counts["build_readiness"], 1)
        self.assertEqual(counts["other_tracked"], 0)

    def test_known_channels_are_normalized_without_exposing_campaign_values(self):
        counts = build_seller_campaign_channel_counts([
            {"source": "tracked_seller_landing", "utm_source": "homeofferflow_admin", "utm_medium": "Email"},
            {"source": "tracked_seller_landing", "utm_source": "organic"},
            {"source": "tracked_seller_landing", "utm_source": "private-customer-name", "utm_medium": "one-off-link"},
            {"source": "website_fsbo_intake", "utm_source": "build_readiness"},
        ])
        self.assertEqual(counts["email"], 1)
        self.assertEqual(counts["organic"], 1)
        self.assertEqual(counts["other_tracked"], 1)
        self.assertNotIn("private-customer-name", counts)
        self.assertNotIn("one-off-link", counts)


if __name__ == "__main__":
    unittest.main()
