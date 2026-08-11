import importlib.util
import os
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
SPEC = importlib.util.spec_from_file_location("fsbo_campaign", ROOT / "api" / "fsbo-lead.py")
fsbo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fsbo)


class SellerLeadCampaignAttributionTests(unittest.TestCase):
    def test_campaign_values_are_normalized_and_mark_the_tracked_source(self):
        campaign = fsbo._seller_campaign_payload({
            "utm_source": "google%20ads",
            "utm_medium": "cpc",
            "utm_campaign": "north-texas",
            "utm_content": "seller-card",
        })
        self.assertEqual(campaign["source"], "tracked_seller_landing")
        self.assertEqual(campaign["utm_source"], "google20ads")
        self.assertEqual(campaign["utm_medium"], "cpc")

    def test_untracked_request_has_no_caller_controlled_source(self):
        campaign = fsbo._seller_campaign_payload({"source": "anything", "landing_page": "https://example.test/private"})
        self.assertEqual(campaign, {
            "utm_source": None,
            "utm_medium": None,
            "utm_campaign": None,
            "utm_content": None,
            "source": "website_fsbo_intake",
        })


if __name__ == "__main__":
    unittest.main()
