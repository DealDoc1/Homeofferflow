from pathlib import Path
import re
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class FsboIntakeConversionTests(unittest.TestCase):
    def test_minimum_viable_seller_request_is_clear_and_accessible(self):
        self.assertIn("Start in under a minute.", HTML)
        self.assertIn("Property address and email are all we need", HTML)
        self.assertIn('id="fsboPropertyAddress"', HTML)
        self.assertIn('id="fsboSellerEmail"', HTML)
        self.assertGreaterEqual(HTML.count('aria-required="true"'), 2)
        self.assertIn("Seller Name <span", HTML)
        self.assertIn("Phone <span", HTML)
        self.assertIn("Target Asking Price <span", HTML)
        self.assertIn("Save My Seller Request", HTML)
        self.assertIn('id="fsboSellerQuickSubmit"', HTML)
        self.assertIn("Get My Free Seller Plan", HTML)
        self.assertIn("No checkout or service commitment.", HTML)

    def test_seller_funnel_events_are_analytics_only_and_never_include_identity(self):
        start = HTML.index("const fsboFunnel =")
        end = HTML.index("const __oldOpenAccountDashboardFsbo", start)
        script = HTML[start:end]

        for event in (
            "FSBO Seller Intake Opened",
            "FSBO Seller Intake Required Fields Ready",
            "FSBO Seller Package Selected",
            "FSBO Seller Request Submission Started",
            "FSBO Seller Request Saved",
            "FSBO Seller Request Save Failed",
            "FSBO Seller Request Receipt Viewed",
            "FSBO Seller Request Receipt Cleared",
        ):
            self.assertIn(event, script)

        self.assertIn("trackEvent(name, data)", script)
        self.assertIn("source: source === 'quick' ? 'quick' : 'full'", script)
        tracked_arguments = "\n".join(re.findall(r"trackFsboFunnel\\(([^;]+)\\);", script))
        self.assertNotIn("sellerEmail", tracked_arguments)
        self.assertNotIn("seller_email", tracked_arguments)
        self.assertNotIn("propertyAddress", tracked_arguments)
        self.assertNotIn("property_address", tracked_arguments)

    def test_restoring_a_draft_does_not_inflate_package_selection_analytics(self):
        self.assertIn("window.selectFsboNeed?.(draft.fsboNeed, false)", HTML)
        self.assertIn("function(key, shouldTrack = true)", HTML)
        self.assertIn("if (shouldTrack) trackFsboFunnel", HTML)

    def test_audience_card_routes_sellers_directly_to_the_minimum_field_intake(self):
        self.assertIn('href="?seller=1"', HTML)
        self.assertIn("FSBO Seller Card CTA Selected", HTML)
        self.assertIn("surface: 'audience_grid'", HTML)
        self.assertIn("setAudience('fsbo'); trackEvent('FSBO Seller Card CTA Selected'", HTML)
        self.assertIn("openFsboSellerModal();", HTML)
        self.assertIn("Start free — address + email", HTML)
        card_start = HTML.index("FSBO Seller Card CTA Selected")
        card_end = HTML.index("</a>", card_start)
        card = HTML[card_start:card_end]
        self.assertNotIn("seller_email", card)
        self.assertNotIn("property_address", card)

    def test_shared_seller_url_opens_the_same_intake_without_identity_in_the_url(self):
        self.assertIn("params().get('seller') === '1'", HTML)
        self.assertIn("window.setAudience?.('fsbo');", HTML)
        self.assertIn("window.openFsboSellerModal?.();", HTML)
        routing_start = HTML.index("params().get('seller') === '1'")
        routing_end = HTML.index("if (params().get('partner_onboarding'))", routing_start)
        routing = HTML[routing_start:routing_end]
        self.assertNotIn("seller_email", routing)
        self.assertNotIn("property_address", routing)

    def test_campaign_links_can_preselect_only_existing_seller_packages_without_overwriting_a_draft(self):
        self.assertIn("const fsboCampaignPackages = new Set", HTML)
        self.assertIn("get('seller_package')", HTML)
        self.assertIn("return fsboCampaignPackages.has(packageKey) ? packageKey : '';", HTML)
        self.assertIn("const campaignPackage = fsboDraftExists() ? '' : campaignFsboPackage();", HTML)
        self.assertIn("if (campaignPackage) window.selectFsboNeed?.(campaignPackage, false);", HTML)
        self.assertIn("campaignPackage: campaignPackage || null", HTML)

    def test_admin_seller_workspace_can_create_allowlisted_fsbo_campaign_links_and_copy(self):
        self.assertIn("FSBO Campaign Toolkit", HTML)
        self.assertIn("copySellerCampaignLink()", HTML)
        self.assertIn("copySellerCampaignInvitation()", HTML)
        self.assertIn("previewSellerCampaignLink()", HTML)
        self.assertIn("const sellerCampaignPackages = new Set", HTML)
        self.assertIn("const sellerCampaignChannels = new Set", HTML)
        self.assertIn("sellerCampaignPackages.has(packageKey)", HTML)
        self.assertIn("sellerCampaignChannels.has(channel)", HTML)
        self.assertIn("function sellerCampaignLabel(value)", HTML)
        self.assertIn("utm_source: 'homeofferflow_admin'", HTML)
        self.assertIn("params.set('utm_medium', channel)", HTML)
        self.assertIn("params.set('utm_campaign', campaign)", HTML)
        self.assertIn('id="sellerCampaignChannel"', HTML)
        self.assertIn('id="sellerCampaignName"', HTML)
        self.assertIn("Seller Campaign Link Copied", HTML)
        self.assertIn("Seller Campaign Invitation Copied", HTML)
        self.assertIn("This is an intake—not checkout or a confirmed service order.", HTML)

    def test_admin_can_create_privacy_safe_homebuyer_acquisition_links_and_copy(self):
        self.assertIn("Homebuyer Campaign Toolkit", HTML)
        self.assertIn("copyBuyerCampaignLink()", HTML)
        self.assertIn("copyBuyerCampaignInvitation()", HTML)
        self.assertIn("previewBuyerCampaignLink()", HTML)
        self.assertIn('id="buyerCampaignChannel"', HTML)
        self.assertIn('id="buyerCampaignName"', HTML)
        self.assertIn("https://www.homeofferflow.com/buyers?", HTML)
        self.assertIn("Homebuyer Campaign Link Copied", HTML)
        self.assertIn("Homebuyer Campaign Invitation Copied", HTML)
        self.assertIn("never a buyer’s identity, property, financing, or offer details", HTML)

    def test_seller_address_autocomplete_fails_softly_and_has_a_google_compatibility_path(self):
        self.assertIn("libraries=places", HTML)
        self.assertIn("typeof google.maps.importLibrary !== 'function'", HTML)
        self.assertIn("wireLegacyGoogleAddressInputs", HTML)
        self.assertIn("google.maps.places.Autocomplete", HTML)
        self.assertIn("Google Places autocomplete is unavailable; manual address entry remains available.", HTML)
        self.assertIn("fsboPropertyAddress: fillFsboAddressFields", HTML)
        self.assertIn("function addressAutocompleteInputs()", HTML)

    def test_seller_intake_has_a_hidden_bot_guard_without_adding_required_fields(self):
        self.assertIn('id="fsboWebsiteConfirm"', HTML)
        self.assertIn('fsbo_website_confirm: fsboVal(\'fsboWebsiteConfirm\')', HTML)
        self.assertIn('aria-hidden="true"', HTML)

    def test_title_company_interest_uses_the_api_canonical_category(self):
        self.assertIn('name="fsboPartner" value="title"> Title company', HTML)
        self.assertNotIn('name="fsboPartner" value="title_company"', HTML)

    def test_seller_intake_modal_has_dialog_keyboard_and_focus_support(self):
        self.assertIn('role="dialog" aria-modal="true" aria-labelledby="fsboSellerTitle"', HTML)
        self.assertIn('id="fsboSellerClose"', HTML)
        self.assertIn('aria-label="Close seller package request"', HTML)
        self.assertIn("fsboFunnel.returnFocus = document.activeElement", HTML)
        self.assertIn("document.getElementById('fsboPropertyAddress')?.focus();", HTML)
        self.assertIn("if (event.key === 'Escape')", HTML)
        self.assertIn("if (event.key !== 'Tab') return;", HTML)
        self.assertIn("if (returnFocus?.isConnected) returnFocus.focus();", HTML)

    def test_free_intake_has_a_submit_path_before_optional_package_and_partner_choices(self):
        quick = HTML.index('id="fsboSellerQuickSubmit"')
        packages = HTML.index('class="fsbo-package-grid"')
        partners = HTML.index('Partner suggestions wanted')
        full = HTML.index('id="fsboSellerSubmit"')
        self.assertLess(quick, packages)
        self.assertLess(quick, partners)
        self.assertLess(quick, full)
        self.assertIn("document.querySelectorAll('[data-fsbo-submit]')", HTML)
        self.assertIn("Request ${item.title} Details", HTML)

    def test_selected_seller_path_adapts_only_the_optional_qualification_prompt(self):
        self.assertIn('const fsboSituationPrompts = {', HTML)
        self.assertIn("label: 'What would you like to compare about the offer?'", HTML)
        self.assertIn("label: 'What should we know about your MLS-interest request?'", HTML)
        self.assertIn('id="fsboNotesLabel" for="fsboNotes"', HTML)
        self.assertIn('const prompt = fsboSituationPrompts[key] || fsboSituationPrompts.free_intake;', HTML)
        self.assertIn("notes.placeholder = prompt.placeholder", HTML)
        self.assertIn('Property address and email are all we need', HTML)


if __name__ == "__main__":
    unittest.main()
