import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ROBOTS = (ROOT / "robots.txt").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
PARTNERS = (ROOT / "partners.html").read_text(encoding="utf-8")
SELLERS = (ROOT / "sellers.html").read_text(encoding="utf-8")
DIRECTORY = (ROOT / "directory.html").read_text(encoding="utf-8")
NOT_FOUND = (ROOT / "404.html").read_text(encoding="utf-8")
BUYERS = (ROOT / "buyers.html").read_text(encoding="utf-8")
BUYERS_COMPACT = " ".join(BUYERS.split())
AGENTS = (ROOT / "agents.html").read_text(encoding="utf-8")
INVESTORS = (ROOT / "investors.html").read_text(encoding="utf-8")
ONDEMAND = (ROOT / "ondemand.html").read_text(encoding="utf-8")
FSBO_GUIDE = (ROOT / "texas-fsbo-guide.html").read_text(encoding="utf-8")
SELLER_OFFER_REVIEW_GUIDE = (ROOT / "texas-seller-offer-review.html").read_text(encoding="utf-8")
AGENT_GUIDE = (ROOT / "texas-agent-offer-workflow.html").read_text(encoding="utf-8")
BUYER_GUIDE = (ROOT / "texas-homebuyer-offer-guide.html").read_text(encoding="utf-8")
INVESTOR_GUIDE = (ROOT / "texas-investor-offer-guide.html").read_text(encoding="utf-8")
TERMS = (ROOT / "terms.html").read_text(encoding="utf-8")
PRIVACY = (ROOT / "privacy.html").read_text(encoding="utf-8")
DISCLAIMER = (ROOT / "disclaimer.html").read_text(encoding="utf-8")
ESIGN_CONSENT = (ROOT / "esign-consent.html").read_text(encoding="utf-8")
SELLER_REVIEW = (ROOT / "seller-review.html").read_text(encoding="utf-8")
FIELD_MAPPER = (ROOT / "field-mapper.html").read_text(encoding="utf-8")
VERCEL = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))


class PublicDiscoveryMetadataTests(unittest.TestCase):
    def test_landing_page_has_canonical_share_and_structured_metadata(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/"', INDEX)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/"', INDEX)
        preview_path = ROOT / "assets" / "homeofferflow-social-preview-v1.png"
        preview_url = "https://www.homeofferflow.com/assets/homeofferflow-social-preview-v1.png"
        self.assertTrue(preview_path.is_file())
        self.assertIn(f'property="og:image" content="{preview_url}"', INDEX)
        self.assertIn('property="og:image:width" content="1200"', INDEX)
        self.assertIn('property="og:image:height" content="630"', INDEX)
        self.assertIn('name="twitter:card" content="summary_large_image"', INDEX)
        self.assertIn(f'name="twitter:image" content="{preview_url}"', INDEX)
        self.assertIn('"@type": "SoftwareApplication"', INDEX)
        self.assertIn('"@type": "HowTo"', INDEX)
        self.assertIn('Prepare a Texas real estate offer with HomeOfferFlow', INDEX)
        self.assertIn('Answer plain questions', INDEX)
        self.assertIn('"priceCurrency": "USD"', INDEX)
        self.assertIn('"@type": "FAQPage"', INDEX)
        self.assertIn('Can I start a HomeOfferFlow buyer offer without paying?', INDEX)
        self.assertIn('Does HomeOfferFlow provide legal advice or represent me as an agent?', INDEX)
        self.assertIn('Clear answers before you begin a Texas offer.', INDEX)
        self.assertIn('Does HomeOfferFlow replace my agent or attorney?', INDEX)
        self.assertIn('How does HomeOfferFlow help Texas FSBO sellers?', INDEX)
        self.assertIn('Can Texas agents use HomeOfferFlow for different transaction types?', INDEX)

    def test_crawlers_can_discover_the_public_marketing_routes(self):
        self.assertIn('Sitemap: https://www.homeofferflow.com/sitemap.xml', ROBOTS)
        self.assertIn('https://www.homeofferflow.com/', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/ondemand', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/partners', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/sellers', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/buyers', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/agents', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/investors', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/directory', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/texas-fsbo-guide', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/texas-seller-offer-review', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/texas-agent-offer-workflow', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/texas-homebuyer-offer-guide', SITEMAP)
        self.assertIn('https://www.homeofferflow.com/texas-investor-offer-guide', SITEMAP)

    def test_public_workflow_guides_provide_descriptive_social_image_alt_text(self):
        expected = {
            "texas-lease-offer-workflow.html": "HomeOfferFlow Texas lease workflow guide",
            "texas-listing-workflow.html": "HomeOfferFlow Texas listing workflow guide",
            "texas-agent-form-library.html": "HomeOfferFlow Texas agent form library guide",
            "texas-home-service-partner-guide.html": "HomeOfferFlow Texas home-service partner placement guide",
        }
        for filename, alt in expected.items():
            page = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn(f'property="og:image:alt" content="{alt}"', page)

    def test_high_intent_acquisition_pages_provide_twitter_image_alt_text(self):
        expected = {
            "agents.html": "HomeOfferFlow Texas real estate offer tools for agents and brokers",
            "sellers.html": "HomeOfferFlow Texas FSBO seller support",
            "buyers.html": "HomeOfferFlow Texas homebuyer offer workflow",
            "investors.html": "HomeOfferFlow Texas investor workspace",
            "partners.html": "HomeOfferFlow founding partner placements for Texas home-service businesses",
            "ondemand.html": "HomeOfferFlow guided Texas offer workflow",
        }
        for filename, alt in expected.items():
            page = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn(f'name="twitter:image:alt" content="{alt}"', page)

    def test_policy_urls_are_canonical_and_private_tool_screens_are_not_indexable(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/terms.html"', TERMS)
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/privacy.html"', PRIVACY)
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/disclaimer.html"', DISCLAIMER)
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/esign-consent.html"', ESIGN_CONSENT)
        self.assertIn('<meta name="robots" content="noindex, nofollow, noarchive, nosnippet"', SELLER_REVIEW)
        self.assertIn('<meta name="robots" content="noindex, nofollow, noarchive"', FIELD_MAPPER)

    def test_ondemand_trial_page_has_canonical_share_and_structured_metadata(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/ondemand"', ONDEMAND)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/ondemand"', ONDEMAND)
        self.assertIn('property="og:image" content="https://www.homeofferflow.com/assets/homeofferflow-social-preview-v1.png"', ONDEMAND)
        self.assertIn('name="twitter:card" content="summary_large_image"', ONDEMAND)
        self.assertIn('"@type":"SoftwareApplication"', ONDEMAND)
        self.assertIn('"price":"29"', ONDEMAND)
        self.assertIn('60 days of HomeOfferFlow free, then $29 per month unless canceled.', ONDEMAND)

    def test_partner_acquisition_page_has_share_metadata_and_a_direct_application_path(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/partners"', PARTNERS)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/partners"', PARTNERS)
        self.assertIn('property="og:site_name" content="HomeOfferFlow"', PARTNERS)
        self.assertIn('property="og:image" content="https://www.homeofferflow.com/assets/homeofferflow-social-preview-v1.png"', PARTNERS)
        self.assertIn('property="og:image:alt"', PARTNERS)
        self.assertIn('name="twitter:card" content="summary_large_image"', PARTNERS)
        self.assertIn('meta name="twitter:title"', PARTNERS)
        self.assertIn('meta name="twitter:description"', PARTNERS)
        self.assertIn('meta name="twitter:image" content="https://www.homeofferflow.com/assets/homeofferflow-social-preview-v1.png"', PARTNERS)
        self.assertIn('"@type":"Service"', PARTNERS)
        self.assertIn('"@type":"OfferCatalog"', PARTNERS)
        self.assertIn('"name":"HomeOfferFlow Founding Partner Launch Pricing"', PARTNERS)
        self.assertIn('"name":"Core Partner founding placement"', PARTNERS)
        self.assertIn('"name":"Featured Partner founding placement"', PARTNERS)
        self.assertIn('"name":"Premier Partner founding placement"', PARTNERS)
        for tier, price in (
            ('founding_pilot', '149'),
            ('monthly_placement', '399'),
            ('market_exclusive', '799'),
        ):
            self.assertIn(f'partner_tier={tier}', PARTNERS)
            self.assertIn(f'"price":"{price}"', PARTNERS)
        self.assertIn('One active Premier placement per category and market while active.', PARTNERS)
        self.assertNotIn('guaranteed traffic', PARTNERS.lower())
        self.assertIn('href="/?partner=1&amp;partner_quick_start=1"', PARTNERS)
        self.assertIn('Start no-charge application', PARTNERS)
        self.assertIn('Start with a no-charge application:', PARTNERS)
        self.assertIn('partner_tier=founding_pilot', PARTNERS)
        self.assertIn('partner_tier=monthly_placement', PARTNERS)
        self.assertIn('partner_tier=market_exclusive', PARTNERS)
        self.assertIn('data-partner-apply', PARTNERS)
        self.assertIn("const allowed = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content'];", PARTNERS)
        self.assertIn("destination.searchParams.set(key, value)", PARTNERS)
        self.assertIn("Founding Partner Landing Viewed", PARTNERS)
        self.assertIn("const tierLabels = { founding_pilot: 'Core Partner'", PARTNERS)
        self.assertIn('id="partnerCampaignContext"', PARTNERS)
        self.assertIn("track('Founding Partner Landing Viewed', {tier: selectedTier || 'unspecified', category: selectedCategory || 'unspecified', channel: campaignChannel});", PARTNERS)
        self.assertIn("Founding Partner Landing CTA Selected", PARTNERS)
        self.assertIn("const allowedCategories = new Set", PARTNERS)
        self.assertIn("campaign.set('partner_category', selectedCategory)", PARTNERS)
        self.assertIn("campaign.set('partner_tier', selectedTier)", PARTNERS)
        self.assertIn("key === 'partner_tier' && destination.searchParams.has(key)", PARTNERS)
        self.assertIn("destination.searchParams.set('utm_source', 'organic')", PARTNERS)
        self.assertIn("destination.searchParams.set('utm_campaign', 'partner_acquisition')", PARTNERS)
        self.assertIn('/_vercel/insights/script.js', PARTNERS)
        self.assertIn('not a referral or a required provider choice', PARTNERS)
        self.assertIn('What happens after you choose a founding tier.', PARTNERS)
        self.assertIn('Apply with the essentials', PARTNERS)
        self.assertIn('Review secure checkout', PARTNERS)
        self.assertIn('Complete private setup', PARTNERS)
        self.assertIn('before a placement goes live', PARTNERS)
        self.assertIn('"@type":"FAQPage"', PARTNERS)
        self.assertIn('Founding partner questions', PARTNERS)
        self.assertIn('Clear commercial terms before you apply.', PARTNERS)
        self.assertIn('When does monthly founding partner billing begin?', PARTNERS)
        self.assertIn('What does Premier category-and-market exclusivity mean?', PARTNERS)
        self.assertIn('One active Premier sponsor per category and market', PARTNERS)
        self.assertIn('Premier Partners reserve one active Premier placement', PARTNERS)
        self.assertIn('href="/partners">Become a Founding Partner</a>', INDEX)

    def test_provider_directory_describes_its_searchable_collection(self):
        self.assertIn('"@type":"CollectionPage"', DIRECTORY)
        self.assertIn('"name":"Texas Home Service Provider Directory by Category and Market"', DIRECTORY)
        self.assertIn('"url":"https://www.homeofferflow.com/directory"', DIRECTORY)
        self.assertIn('"isPartOf":{"@id":"https://www.homeofferflow.com/#website"}', DIRECTORY)
        self.assertIn('Texas home service providers by category and market.', DIRECTORY)
        self.assertIn('Texas Home Service Provider Directory by Category and Market | HomeOfferFlow', DIRECTORY)
        self.assertIn('"@type":"HowTo"', DIRECTORY)
        self.assertIn('Find a Texas home-service provider', DIRECTORY)
        self.assertIn('Review and contact independently', DIRECTORY)
        self.assertIn('loading="lazy" decoding="async"', DIRECTORY)

    def test_provider_directory_exposes_popular_categories_before_javascript_runs(self):
        self.assertIn('id="directory-categories"', DIRECTORY)
        self.assertIn('aria-label="Popular Texas home-service categories"', DIRECTORY)
        for category in ('title', 'lender', 'inspection', 'insurance', 'roofing', 'general_contractor'):
            self.assertIn(f'href="/directory?category={category}"', DIRECTORY)

    def test_not_found_page_routes_visitors_into_the_simple_workflows(self):
        self.assertIn('<meta name="robots" content="noindex, nofollow, noarchive">', NOT_FOUND)
        self.assertIn('<meta name="theme-color" content="#173f35">', NOT_FOUND)
        self.assertIn('viewport-fit=cover', NOT_FOUND)
        self.assertIn('safe-area-inset-top', NOT_FOUND)
        self.assertIn('safe-area-inset-bottom', NOT_FOUND)
        self.assertIn('rel="manifest" href="/manifest.webmanifest"', NOT_FOUND)
        for path in (
            '/?agent=1&amp;workflow=sale_listing',
            '/?agent=1&amp;workflow=purchase',
            '/?agent=1&amp;workflow=lease_listing',
            '/?agent=1&amp;workflow=lease_representation',
            'href="/directory"',
            'href="/partners"',
        ):
            self.assertIn(path, NOT_FOUND)

    def test_fsbo_guide_is_a_crawlable_people_first_path_to_the_free_seller_plan(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/texas-fsbo-guide">', FSBO_GUIDE)
        self.assertIn('"@type":"Article"', FSBO_GUIDE)
        self.assertIn('"@type":"FAQPage"', FSBO_GUIDE)
        self.assertIn('Get my free seller plan', FSBO_GUIDE)
        self.assertIn('not legal, tax, lending, inspection, title, or brokerage advice', FSBO_GUIDE)
        self.assertIn('/texas-fsbo-guide', (ROOT / 'vercel.json').read_text(encoding='utf-8'))
        self.assertIn('href="/texas-fsbo-guide"', SELLERS)

    def test_agent_offer_workflow_guide_is_a_crawlable_people_first_path_to_the_workspace(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/texas-agent-offer-workflow">', AGENT_GUIDE)
        self.assertIn('"@type":"Article"', AGENT_GUIDE)
        self.assertIn('"@type":"FAQPage"', AGENT_GUIDE)
        self.assertIn('Start a private client draft', AGENT_GUIDE)
        self.assertIn('id="agentGuideQuestionOne"', AGENT_GUIDE)
        self.assertIn('href="/agents#transaction-start"', AGENT_GUIDE)
        self.assertIn('choose listing, buying, lease listing, or lease representation', AGENT_GUIDE)
        self.assertIn('not legal, tax, lending, title, or brokerage advice', AGENT_GUIDE)
        self.assertIn('/texas-agent-offer-workflow', (ROOT / 'vercel.json').read_text(encoding='utf-8'))
        self.assertIn('href="/texas-agent-offer-workflow"', AGENTS)
        self.assertIn('agent-workflow-guide-metrics.js', AGENT_GUIDE)

    def test_homepage_exposes_the_shared_agent_form_library_path(self):
        self.assertIn('href="/texas-agent-form-library"', INDEX)
        self.assertIn('Texas agent form library', INDEX)
        self.assertIn('workspace=relationship', AGENT_GUIDE)
        self.assertIn('private relationship drafts', AGENT_GUIDE)
        self.assertIn('preview-only until their separate signing QA is complete', AGENT_GUIDE)

    def test_homebuyer_offer_guide_is_a_crawlable_people_first_path_to_the_paid_workflow(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/texas-homebuyer-offer-guide">', BUYER_GUIDE)
        self.assertIn('"@type":"Article"', BUYER_GUIDE)
        self.assertIn('"@type":"FAQPage"', BUYER_GUIDE)
        self.assertIn('"@type":"BreadcrumbList"', BUYER_GUIDE)
        self.assertIn('aria-label="Breadcrumb"', BUYER_GUIDE)
        self.assertIn('Texas Homebuyer Offer Planning Guide', BUYER_GUIDE)
        self.assertIn('Build my offer — no payment to start', BUYER_GUIDE)
        self.assertIn('not legal, lending, title, inspection, tax, or brokerage advice', BUYER_GUIDE)
        self.assertIn('/texas-homebuyer-offer-guide', (ROOT / 'vercel.json').read_text(encoding='utf-8'))
        self.assertIn('href="/texas-homebuyer-offer-guide"', BUYERS)

    def test_seller_offer_review_guide_is_a_crawlable_people_first_path_to_offer_review(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/texas-seller-offer-review">', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('"@type":"Article"', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('"@type":"FAQPage"', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('"@type":"Service"', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('"price":"599"', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('<meta name="twitter:title" content="Texas Seller Offer Review | HomeOfferFlow">', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('property="og:image:alt" content="HomeOfferFlow Texas seller offer review guide"', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('Texas Seller Offer Review', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('Start seller offer review', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('does not recommend, accept, reject, or negotiate', SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn('/texas-seller-offer-review', (ROOT / 'vercel.json').read_text(encoding='utf-8'))
        self.assertIn('href="/texas-seller-offer-review"', FSBO_GUIDE)

    def test_seller_offer_review_guide_records_privacy_safe_funnel_events(self):
        self.assertIn("record('fsbo_landing_viewed')", SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn("record('fsbo_landing_cta_selected')", SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn("service_level: 'offer_review'", SELLER_OFFER_REVIEW_GUIDE)
        self.assertIn("sessionStorage.getItem(key)", SELLER_OFFER_REVIEW_GUIDE)
        self.assertNotIn('location.href', SELLER_OFFER_REVIEW_GUIDE)

    def test_investor_offer_guide_is_a_crawlable_people_first_path_to_the_workspace(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/texas-investor-offer-guide">', INVESTOR_GUIDE)
        self.assertIn('"@type":"Article"', INVESTOR_GUIDE)
        self.assertIn('"@type":"FAQPage"', INVESTOR_GUIDE)
        self.assertIn('Open investor workspace — no payment', INVESTOR_GUIDE)
        self.assertIn('not legal, tax, lending, investment, title, inspection, or brokerage advice', INVESTOR_GUIDE)
        self.assertIn('/texas-investor-offer-guide', (ROOT / 'vercel.json').read_text(encoding='utf-8'))
        self.assertIn('href="/texas-investor-offer-guide"', INVESTORS)

    def test_seller_acquisition_page_is_indexable_and_routes_to_the_existing_safe_intake(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/sellers"', SELLERS)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/sellers"', SELLERS)
        self.assertIn('"@type":"Service"', SELLERS)
        self.assertIn('href="/?seller=1&amp;seller_package=free_intake"', SELLERS)
        self.assertIn('seller_package=free_intake', SELLERS)
        self.assertIn('seller_package=seller_prep', SELLERS)
        self.assertIn('seller_package=launch_kit', SELLERS)
        self.assertIn('seller_package=flat_fee_mls', SELLERS)
        self.assertIn('seller_package=offer_review', SELLERS)
        self.assertIn('seller_package=contract_help', SELLERS)
        self.assertIn('seller_package=premium_bundle', SELLERS)
        self.assertIn('data-seller-apply', SELLERS)
        self.assertIn("const allowed = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content'];", SELLERS)
        self.assertIn("const sellerPackages = new Set(['free_intake', 'seller_prep', 'launch_kit', 'flat_fee_mls', 'offer_review', 'contract_help', 'premium_bundle']);", SELLERS)
        self.assertIn("const sellerPackageLabels = { free_intake: 'Free Seller Intake'", SELLERS)
        self.assertIn('id="sellerCampaignContext"', SELLERS)
        self.assertIn("track('FSBO Seller Landing Viewed', selectedCampaignPackage ? { sellerPackage: selectedCampaignPackage } : {});", SELLERS)
        self.assertIn("destination.searchParams.get('seller_package') === 'free_intake'", SELLERS)
        self.assertIn("destination.searchParams.set(key, value)", SELLERS)
        self.assertIn("FSBO Seller Landing Viewed", SELLERS)
        self.assertIn("FSBO Seller Landing CTA Selected", SELLERS)
        self.assertIn('/_vercel/insights/script.js', SELLERS)
        self.assertIn('This is an intake—not checkout or a service order.', SELLERS)
        self.assertIn('What happens after a free seller request.', SELLERS)
        self.assertIn('Your request is saved', SELLERS)
        self.assertIn('replyable email receipt', SELLERS)
        self.assertIn('seller email supplied', SELLERS)
        self.assertIn('Scope is reviewed', SELLERS)
        self.assertIn('You confirm before payment', SELLERS)
        self.assertIn('No payment is collected through this intake.', SELLERS)
        self.assertIn('"@type":"FAQPage"', SELLERS)
        self.assertIn('Texas FSBO questions', SELLERS)
        self.assertIn('Immediate timeline-specific seller plan', SELLERS)
        self.assertIn('Get my free seller plan', SELLERS)
        self.assertIn('Explore the FSBO launch kit', SELLERS)
        self.assertIn("grid.classList.add('seller-tier-grid')", SELLERS)
        self.assertIn('seller-tier-toggle', SELLERS)
        self.assertIn('See all support paths', SELLERS)
        self.assertIn("Show fewer support paths", SELLERS)
        self.assertIn("'launch_kit'", SELLERS)
        self.assertIn("'premium_bundle'", SELLERS)
        self.assertIn('href="/sellers">FSBO Seller Support</a>', INDEX)
        self.assertIn('href="/texas-fsbo-guide"', INDEX)

    def test_homebuyer_offer_page_is_indexable_and_routes_to_the_existing_safe_workflow(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/buyers"', BUYERS_COMPACT)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/buyers"', BUYERS_COMPACT)
        self.assertIn('"@type": "Service"', BUYERS)
        self.assertIn('"price": "99"', BUYERS)
        self.assertIn('"@type":"HowTo"', BUYERS)
        self.assertIn('Prepare a Texas homebuyer offer packet', BUYERS)
        self.assertIn('Review the complete summary', BUYERS)
        self.assertIn('data-buyer-start href="/?buyer=1"', BUYERS)
        self.assertIn("Homebuyer Offer Landing Viewed", BUYERS)
        self.assertIn("Homebuyer Offer Landing CTA Selected", BUYERS)
        self.assertIn('const allowedChannels = new Set([', BUYERS)
        self.assertIn('"homeofferflow_admin" && allowedChannels.has(medium)', BUYERS)
        self.assertIn('track("Homebuyer Offer Landing Viewed", attribution);', BUYERS)
        self.assertIn('"utm_campaign",', BUYERS)
        self.assertIn('There is no payment required to begin.', BUYERS)
        self.assertIn("params().get('buyer') === '1'", INDEX)
        self.assertIn("window.startHomebuyerOffer?.();", INDEX)

    def test_clean_homebuyer_route_rewrites_to_the_shareable_offer_page(self):
        self.assertIn(
            {"source": "/buyers", "destination": "/buyers.html"},
            VERCEL.get("rewrites", []),
        )

    def test_agent_workspace_page_is_indexable_and_routes_to_passwordless_sign_in(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/agents"', AGENTS)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/agents"', AGENTS)
        self.assertIn('"@type":"SoftwareApplication"', AGENTS)
        self.assertIn('"@type":"FAQPage"', AGENTS)
        self.assertIn('"name":"Do I need a password?"', AGENTS)
        self.assertIn('"name":"What happens after I choose a transaction?"', AGENTS)
        self.assertIn('"name":"Can I use saved defaults for the next offer?"', AGENTS)
        self.assertIn('"name":"Can I organize a seller-side listing?"', AGENTS)
        self.assertIn('"name":"Can I prepare private form reviews?"', AGENTS)
        self.assertIn('"name":"Does this replace broker supervision?"', AGENTS)
        self.assertIn('private relationship, consumer-notice, seller-disclosure, finance, environmental, and mineral review drafts', AGENTS)
        self.assertIn('private TXR-1501, TXR-1506, TXR-1507, TXR-1508, TXR-1905, TXR-1914, TXR-1917, and TXR-1919 review-draft creation for every signed-in agent', AGENTS)
        self.assertIn('Private seller planning', AGENTS)
        self.assertIn('universal TREC-55-1 seller-disclosure and optional TREC-61-0 water-disclosure review drafts', AGENTS)
        self.assertIn('seller listing launch checklist or consultation brief', AGENTS)
        self.assertIn('the queue identifies the selected signer and requires an explicit recipient confirmation before a document is sent.', AGENTS)
        self.assertIn('href="/?agent=1&amp;workflow=purchase"', AGENTS)
        self.assertIn('HomeOfferFlow does not automatically select a legal form.', AGENTS)
        self.assertIn('No password and no charge to start a private workspace.', AGENTS)
        self.assertIn('href="/ondemand?utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=ondemand_trial"', AGENTS)
        self.assertIn('"name":"OnDemand Agent Workspace"', AGENTS)
        self.assertIn('"price":"29"', AGENTS)
        self.assertIn('60-day free trial followed by $29 monthly unless canceled', AGENTS)
        self.assertIn('See your 60-day HomeOfferFlow trial', AGENTS)
        self.assertIn({'source': '/agents', 'destination': '/agents.html'}, VERCEL.get('rewrites', []))

    def test_investor_workspace_page_is_indexable_and_routes_to_passwordless_sign_in(self):
        self.assertIn('<link rel="canonical" href="https://www.homeofferflow.com/investors"', INVESTORS)
        self.assertIn('property="og:url" content="https://www.homeofferflow.com/investors"', INVESTORS)
        self.assertIn('aria-label="Breadcrumb"', INVESTORS)
        self.assertIn('"@type":"BreadcrumbList"', INVESTORS)
        self.assertIn('"@type":"HowTo"', INVESTORS)
        self.assertIn('Start a Texas investor offer workspace', INVESTORS)
        self.assertIn('Save stable defaults', INVESTORS)
        self.assertIn('"@type":"FAQPage"', INVESTORS)
        self.assertIn('"name":"Do I need a password for the investor workspace?"', INVESTORS)
        self.assertIn('href="/?investor=1"', INVESTORS)
        self.assertIn('No password and no charge to open the workspace.', INVESTORS)
        self.assertIn({'source': '/investors', 'destination': '/investors.html'}, VERCEL.get('rewrites', []))

    def test_seller_support_page_exposes_breadcrumb_context(self):
        self.assertIn('aria-label="Breadcrumb"', SELLERS)
        self.assertIn('"@type":"BreadcrumbList"', SELLERS)
        self.assertIn('"name":"Texas FSBO Seller Support"', SELLERS)

    def test_provider_directory_exposes_breadcrumb_context(self):
        self.assertIn('aria-label="Breadcrumb"', DIRECTORY)
        self.assertIn('"@type":"BreadcrumbList"', DIRECTORY)
        self.assertIn('"name":"Texas Service Provider Directory"', DIRECTORY)

    def test_homebuyer_offer_page_exposes_breadcrumb_context(self):
        self.assertIn('aria-label="Breadcrumb"', BUYERS)
        self.assertIn('"@type":"BreadcrumbList"', BUYERS)
        self.assertIn('"name":"Texas Homebuyer Offer Packet"', BUYERS)

    def test_clean_public_marketing_routes_resolve_and_are_canonical(self):
        for route, destination in (
            ("/partners", "/partners.html"),
            ("/texas-home-service-partner-guide", "/texas-home-service-partner-guide.html"),
            ("/sellers", "/sellers.html"),
            ("/directory", "/directory.html"),
        ):
            self.assertIn({"source": route, "destination": destination}, VERCEL.get("rewrites", []))

    def test_core_public_landing_pages_have_complete_share_cards(self):
        for page in (BUYERS, SELLERS, AGENTS, INVESTORS, DIRECTORY):
            compact = " ".join(page.split())
            self.assertIn('property="og:site_name" content="HomeOfferFlow"', compact)
            self.assertIn('property="og:image" content="https://www.homeofferflow.com/assets/homeofferflow-social-preview-v1.png"', compact)
            self.assertIn('meta name="twitter:card" content="summary_large_image"', compact)
            self.assertIn('meta name="twitter:title"', compact)
            self.assertIn('meta name="twitter:description"', compact)
            self.assertIn('meta name="twitter:image" content="https://www.homeofferflow.com/assets/homeofferflow-social-preview-v1.png"', compact)

    def test_homepage_exposes_each_public_path_from_the_primary_navigation(self):
        self.assertIn('<details class="nav-discovery">', INDEX)
        self.assertIn('<summary>Explore</summary>', INDEX)
        self.assertIn('class="nav-directory" href="/directory"', INDEX)
        self.assertIn("Provider Directory Navigation Selected", INDEX)
        for href, label in (
            ('/buyers', 'Homebuyer offer'),
            ('/agents', 'Agent &amp; broker workspace'),
            ('/investors', 'Investor workspace'),
            ('/sellers', 'FSBO seller support'),
            ('/directory', 'Find a provider'),
            ('/partners', 'Partner placements'),
        ):
            self.assertIn(f'<a href="{href}">{label}</a>', INDEX)

    def test_public_directory_uses_only_the_existing_safe_directory_endpoint(self):
        self.assertIn('href="https://www.homeofferflow.com/directory"', DIRECTORY)
        self.assertIn("fetch('/api/fsbo-lead?'+query)", DIRECTORY)
        self.assertIn("partner_directory:'1'", DIRECTORY)
        self.assertIn('restoreFiltersFromUrl', DIRECTORY)
        self.assertIn('syncFiltersToUrl', DIRECTORY)
        self.assertIn("url.searchParams.set('category', category)", DIRECTORY)
        self.assertIn("url.searchParams.set('market', market)", DIRECTORY)
        self.assertIn('allowedCategories.has(category)', DIRECTORY)
        self.assertIn('No active HomeOfferFlow provider profiles', DIRECTORY)
        self.assertIn('const unavailable = category =>', DIRECTORY)
        self.assertIn('data-directory-retry', DIRECTORY)
        self.assertIn('Retry provider profiles', DIRECTORY)
        self.assertIn("$('results').querySelector('[data-directory-retry]')?.addEventListener('click', () => load());", DIRECTORY)
        self.assertIn('Own a service business? Explore a founding placement', DIRECTORY)
        self.assertIn("query.set('partner_category', category)", DIRECTORY)
        self.assertIn('List your ${esc(categoryLabel)} business with HomeOfferFlow', DIRECTORY)
        self.assertIn('href="/partners"', DIRECTORY)
        self.assertIn('"@type":"FAQPage"', DIRECTORY)
        self.assertIn('Directory questions', DIRECTORY)
        self.assertIn('provider_directory', DIRECTORY)
        self.assertIn('partner_acquisition', DIRECTORY)
        self.assertIn("Provider Directory Partner CTA Selected", DIRECTORY)
        self.assertIn("Provider Directory Consumer CTA Selected", DIRECTORY)
        self.assertIn("data-directory-consumer-cta", DIRECTORY)
        self.assertIn("utm_campaign:'consumer_recovery'", DIRECTORY)
        self.assertIn("Build a Texas buyer offer", DIRECTORY)
        self.assertIn("Explore FSBO seller support", DIRECTORY)
        self.assertIn('bindPartnerCtas', DIRECTORY)
        for category in (
            'title', 'lender', 'inspection', 'surveyor', 'home_warranty',
            'insurance', 'roofing', 'hvac', 'plumbing', 'electrical',
            'foundation_structural', 'general_contractor', 'pest_termite',
            'septic_well', 'restoration', 'photography_video', 'staging',
            'repairs_handyman', 'cleaning', 'moving_storage', 'lawn_pool',
            'security_smart_home', 'other',
        ):
            self.assertIn(f'<option value="{category}">', DIRECTORY)
        self.assertIn('href="/directory">Find a Provider</a>', INDEX)
        self.assertIn('href="/directory" style="color:var(--gold-light);font-weight:800;">Browse approved provider listings →</a>', INDEX)


if __name__ == "__main__":
    unittest.main()
