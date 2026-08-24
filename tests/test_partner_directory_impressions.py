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
        self.assertIn("recordPartnerApplicationStart", PUBLIC_DIRECTORY)
        self.assertIn("partner_quick_start:'1'", PUBLIC_DIRECTORY)
        self.assertIn("partner_category", PUBLIC_DIRECTORY)
        self.assertIn("partner_directory_application_selected", PUBLIC_DIRECTORY)
        self.assertIn("partner_directory_pricing_selected", PUBLIC_DIRECTORY)
        self.assertIn("partnerDetailsUrl", PUBLIC_DIRECTORY)
        self.assertIn("data-directory-partner-details", PUBLIC_DIRECTORY)
        self.assertIn("Provider Directory Placement Pricing Selected", PUBLIC_DIRECTORY)
        self.assertIn("request_type:'partner_landing_event'", PUBLIC_DIRECTORY)
        self.assertIn("const directorySource = new URLSearchParams(window.location.search).get('utm_source');", PUBLIC_DIRECTORY)
        self.assertIn("directorySource === 'pwa_shortcut' ? 'pwa_provider_directory' : 'public_directory'", PUBLIC_DIRECTORY)
        self.assertIn("directory_surface:directorySurface", PUBLIC_DIRECTORY)
        self.assertIn('/_vercel/insights/script.js', PUBLIC_DIRECTORY)
        self.assertIn("const cta = String(provider.cta_label || '').trim().slice(0, 80) || 'Visit site';", PUBLIC_DIRECTORY)
        self.assertIn('${esc(cta)} ↗', PUBLIC_DIRECTORY)
        self.assertIn("/texas-home-service-partner-guide?utm_source=provider_directory", PUBLIC_DIRECTORY)

    def test_public_directory_gives_non_regulated_paid_placements_visible_order_without_ranking_regulated_services(self):
        self.assertIn("neutralProviderTypes = new Set(['lender','title','inspection','surveyor'])", PUBLIC_DIRECTORY)
        self.assertIn("placementRank = {exclusive_market:0,premier:1,founding:2}", PUBLIC_DIRECTORY)
        self.assertIn('const sortDirectoryRows = rows =>', PUBLIC_DIRECTORY)
        self.assertIn('const rows = sortDirectoryRows(Array.isArray(data.partners) ? data.partners : []);', PUBLIC_DIRECTORY)
        self.assertIn('if (!leftNeutral && !rightNeutral)', PUBLIC_DIRECTORY)
        self.assertIn("placementLabels = {exclusive_market:'Premier Partner',premier:'Featured Partner',founding:'Core Partner'}", PUBLIC_DIRECTORY)
        self.assertIn("const placement = neutral ? 'Sponsored profile' : `Sponsored · ${placementLabels[provider.placement_tier] || 'Partner'}`;", PUBLIC_DIRECTORY)

    def test_admin_metrics_can_report_aggregate_paid_directory_value(self):
        api = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"partnerDirectoryImpressionCount"', api)
        self.assertIn('"partnerDirectoryOutboundClickCount"', api)
        self.assertIn('"partnerDirectoryOutboundClickRate"', api)
        self.assertIn('partner_directory_traffic_by_placement', api)
        self.assertIn('"directoryTraffic"', api)
        self.assertIn('"partnerDirectoryFsboSellerPlanImpressionCount"', api)
        self.assertIn('"partnerDirectoryFsboSellerPlanOutboundClickCount"', api)
        self.assertIn('"partnerDirectoryPwaImpressionCount"', api)
        self.assertIn('"partnerDirectoryPwaOutboundClickCount"', api)
        self.assertIn('Directory value:', HTML)
        self.assertIn('Installed-app directory value:', HTML)
        self.assertIn('Directory acquisition:', HTML)
        self.assertIn('partnerDirectoryPricingSelectionCount', api)
        self.assertIn('partnerDirectoryPricingSelectionCount', HTML)
        self.assertIn('"partnerDirectoryApplicationStartCount"', api)
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

    def test_empty_selected_category_searches_create_a_privacy_safe_partner_recruitment_signal(self):
        api = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        lead_api = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
        self.assertIn("recordUnfilledDirectoryDemand", PUBLIC_DIRECTORY)
        self.assertIn("partner_directory_empty_search", PUBLIC_DIRECTORY)
        self.assertIn("hof_public_directory_empty_search_${category}", PUBLIC_DIRECTORY)
        self.assertIn("if (!rows.length) recordUnfilledDirectoryDemand(category);", PUBLIC_DIRECTORY)
        self.assertIn('"partner_directory_empty_search": "unfilled_search"', lead_api)
        self.assertIn('"partnerDirectoryEmptySearchCount"', api)
        self.assertIn('"partnerDirectoryEmptySearchCategoryCounts"', api)
        self.assertIn("partnerDirectoryEmptySearchCount", HTML)
        self.assertIn("topUnfilledPartnerDemand", HTML)
        self.assertIn("copyPartnerDemandInvitation", HTML)
        self.assertIn("directory_demand", HTML)
        self.assertIn("destination.searchParams.set('partner_category', category)", PUBLIC_DIRECTORY)
        self.assertIn("never sends email or carries visitor/search/market data", HTML)
        self.assertNotIn("market:market", PUBLIC_DIRECTORY)

    def test_empty_all_category_directory_result_guides_visitors_to_a_private_category_signal(self):
        self.assertIn("categoryChoices = !category", PUBLIC_DIRECTORY)
        self.assertIn("data-directory-category", PUBLIC_DIRECTORY)
        self.assertIn("We record only the category—not your search text or market.", PUBLIC_DIRECTORY)
        self.assertIn("bindCategoryChoices", PUBLIC_DIRECTORY)
        self.assertIn("$('category').value = category;", PUBLIC_DIRECTORY)

    def test_empty_directory_keeps_consumer_recovery_primary_and_provider_recruitment_available(self):
        self.assertIn('Need help with your own next step?', PUBLIC_DIRECTORY)
        self.assertIn('class="provider-join"', PUBLIC_DIRECTORY)
        self.assertIn('Do you provide ${categoryLabel ? esc(categoryLabel) : \'a Texas home service\'}?', PUBLIC_DIRECTORY)
        self.assertIn('data-directory-partner-details', PUBLIC_DIRECTORY)
        self.assertIn('data-directory-partner-cta', PUBLIC_DIRECTORY)


if __name__ == "__main__":
    unittest.main()
