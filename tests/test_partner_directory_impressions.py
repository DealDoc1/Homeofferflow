from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
PUBLIC_DIRECTORY = (ROOT / "directory.html").read_text(encoding="utf-8")


class PartnerDirectoryImpressionTests(unittest.TestCase):
    def test_partner_directory_tracks_privacy_safe_deduplicated_impressions(self):
        self.assertIn("trackPartnerDirectoryImpressions", HTML)
        self.assertIn("Partner Directory Impression", HTML)
        self.assertIn("hof_partner_impression_", HTML)
        self.assertIn("Partner Directory Outbound Click", HTML)
        self.assertIn("sessionStorage", HTML)

    def test_public_directory_uses_the_same_privacy_safe_partner_events(self):
        self.assertIn("Partner Directory Impression", PUBLIC_DIRECTORY)
        self.assertIn("Partner Directory Outbound Click", PUBLIC_DIRECTORY)
        self.assertIn("hof_public_partner_impression_", PUBLIC_DIRECTORY)
        self.assertIn("data-partner-link", PUBLIC_DIRECTORY)
        self.assertIn("request_type:'partner_directory_event'", PUBLIC_DIRECTORY)
        self.assertIn("recordDirectoryEvent('partner_directory_impression'", PUBLIC_DIRECTORY)
        self.assertIn("recordDirectoryEvent('partner_directory_outbound_click'", PUBLIC_DIRECTORY)
        self.assertIn('/_vercel/insights/script.js', PUBLIC_DIRECTORY)

    def test_admin_metrics_can_report_aggregate_paid_directory_value(self):
        api = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"partnerDirectoryImpressionCount"', api)
        self.assertIn('"partnerDirectoryOutboundClickCount"', api)
        self.assertIn('"partnerDirectoryOutboundClickRate"', api)
        self.assertIn('partner_directory_traffic_by_placement', api)
        self.assertIn('"directoryTraffic"', api)
        self.assertIn('Directory value:', HTML)
        self.assertIn('Directory performance:', HTML)
        self.assertIn('Aggregate placement traffic only.', HTML)

    def test_public_directory_event_is_bound_to_an_active_allowlisted_placement(self):
        api = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
        self.assertIn('"is_active": "eq.true"', api)
        self.assertIn('"placement_tier": f"eq.{placement_tier}"', api)
        self.assertIn('That partner placement is unavailable.', api)

    def test_public_directory_records_category_demand_without_market_text(self):
        self.assertIn('trackSearchDemand', PUBLIC_DIRECTORY)
        self.assertIn('Provider Directory Search', PUBLIC_DIRECTORY)
        self.assertIn("category:safeCategory, hasMarket", PUBLIC_DIRECTORY)
        self.assertIn("hof_public_directory_search_${safeCategory}_${hasMarket ? 'market' : 'all'}", PUBLIC_DIRECTORY)
        self.assertNotIn("market:market", PUBLIC_DIRECTORY)


if __name__ == "__main__":
    unittest.main()
