from pathlib import Path
import re
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
SELLERS = (Path(__file__).resolve().parents[1] / "sellers.html").read_text(encoding="utf-8")
SELLER_BRIDGE = (Path(__file__).resolve().parents[1] / "assets" / "seller-campaign-package-bridge.js").read_text(encoding="utf-8")


class FsboIntakeConversionTests(unittest.TestCase):
    def test_minimum_viable_seller_request_is_clear_and_accessible(self):
        self.assertIn("Two details. One free plan.", HTML)
        self.assertIn("Get Your Free FSBO Seller Plan", HTML)
        self.assertIn("Property address and email are all we need", HTML)
        self.assertIn("Manual entry still works.", HTML)
        self.assertIn('placeholder="123 Main St, City, TX ZIP"', HTML)

    def test_seller_entry_uses_consumer_plan_language_not_internal_lead_capture_terms(self):
        self.assertIn("Build a simple Texas <em>FSBO seller plan</em>.", HTML)
        self.assertIn("Start Your Free Plan", HTML)
        self.assertIn("Free Seller Plan →", HTML)
        self.assertIn("No checkout, commitment, or pressure to choose a service.", HTML)
        self.assertNotIn("FSBO path is lead capture only", HTML)
        self.assertIn('id="fsboAddressHelp"', HTML)
        self.assertIn('id="fsboPropertyAddress"', HTML)
        self.assertIn('id="fsboSellerEmail"', HTML)
        self.assertIn('label for="fsboPropertyAddress">Property Address</label>', HTML)
        self.assertIn('label for="fsboSellerEmail">Email</label>', HTML)
        self.assertIn('label for="fsboTimeline">Timeline', HTML)
        self.assertIn('inputmode="email" autocomplete="email"', HTML)
        self.assertGreaterEqual(HTML.count('aria-required="true"'), 2)
        self.assertIn("Seller Name <span", HTML)
        self.assertIn("Phone <span", HTML)
        self.assertIn("Target Asking Price <span", HTML)
        self.assertIn("Save My Seller Request", HTML)
        self.assertIn('id="fsboSellerQuickSubmit"', HTML)
        self.assertIn("Get My Free Seller Plan", HTML)
        self.assertIn("No checkout or service commitment.", HTML)
        self.assertIn("No checkout. Optional details can wait.", HTML)
        self.assertIn('id="fsboRequiredReadyCue"', HTML)
        self.assertIn("function renderFsboRequiredReadyCue", HTML)
        self.assertIn("Your address and email are complete", HTML)
        self.assertIn("Your free seller plan is already selected", HTML)
        self.assertIn("One quick question: what would help most right now?", HTML)
        self.assertIn("selectFsboGuidedGoal", HTML)
        self.assertIn("fsboGuidedGoalPackages", HTML)

    def test_primary_seller_action_does_not_repeat_the_intake_explanation(self):
        action_start = HTML.index('id="fsboSellerQuickSubmit"')
        action_section = HTML[HTML.rfind('<div class="notice sage"', 0, action_start):action_start]
        self.assertIn("No checkout. Optional details can wait.", action_section)
        self.assertNotIn("Ready when you are.", action_section)

    def test_seller_funnel_events_are_analytics_only_and_never_include_identity(self):
        start = HTML.index("const fsboFunnel =")
        end = HTML.index("const __oldOpenAccountDashboardFsbo", start)
        script = HTML[start:end]

        for event in (
            "FSBO Seller Intake Opened",
            "FSBO Seller Intake Required Fields Ready",
            "FSBO Seller Package Selected",
            "FSBO Seller Goal Selected",
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

    def test_required_details_ready_is_persisted_as_aggregate_funnel_evidence(self):
        api = (Path(__file__).resolve().parents[1] / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
        admin = (Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("'FSBO Seller Intake Required Fields Ready': 'fsbo_required_fields_ready'", HTML)
        self.assertIn('"fsbo_required_fields_ready": "ready"', api)
        self.assertIn('"fsbo_required_fields_ready"', admin)
        self.assertIn('"sellerRequiredReadyCount"', admin)
        self.assertIn('"sellerReadyToSaveRate"', admin)
        self.assertIn("'FSBO Seller Address Started': 'fsbo_address_started'", HTML)
        self.assertIn("'FSBO Seller Email Started': 'fsbo_email_started'", HTML)
        self.assertIn('"fsbo_address_started": "started"', api)
        self.assertIn('"fsbo_email_started": "started"', api)
        self.assertIn('"fsbo_request_save_failed": "failed"', api)
        self.assertIn('"sellerAddressStartedCount"', admin)
        self.assertIn('"sellerEmailStartedCount"', admin)
        self.assertIn('"sellerRequiredReadyRate"', admin)
        self.assertIn('"sellerRequestSaveFailureCount"', admin)
        self.assertIn("ready-to-save", HTML)
        self.assertIn('"fsbo_goal_selected": "selected"', api)
        self.assertIn('"fsbo_goal_selected"', admin)

    def test_seller_plan_receipt_delivery_is_visible_as_aggregate_operations_evidence(self):
        api = (Path(__file__).resolve().parents[1] / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
        admin = (Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("def _record_seller_plan_receipt_event", api)
        self.assertIn("FSBO_RECEIPT_DELIVERY_STATUSES", api)
        self.assertIn("fsbo_seller_plan_receipt_", api)
        self.assertIn('"sellerPlanReceiptSentCount"', admin)
        self.assertIn('"sellerPlanReceiptFailureCount"', admin)
        self.assertIn("Seller-plan receipts:", HTML)

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
        self.assertIn("Start a no-charge seller plan in under a minute", HTML)
        self.assertIn("Start free — address + email · no checkout", HTML)
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

    def test_selected_paid_package_is_explained_before_the_short_required_intake(self):
        self.assertIn('id="fsboSelectedPackageCallout"', HTML)
        self.assertIn("window.renderFsboSelectedPackageCallout", HTML)
        self.assertIn("Selected path: ${item.title} (${item.price})", HTML)
        self.assertIn("this is not checkout or a service order", HTML)

    def test_admin_seller_campaigns_land_on_the_explanatory_seller_page_before_intake(self):
        self.assertIn("return `https://www.homeofferflow.com/sellers?${params.toString()}`;", HTML)
        self.assertIn("campaignPackage: campaignPackage || null", HTML)

    def test_public_seller_page_preserves_every_allowlisted_admin_campaign_package(self):
        self.assertIn('/assets/seller-campaign-package-bridge.js', SELLERS)
        for package in ('free_intake', 'seller_prep', 'launch_kit', 'flat_fee_mls', 'offer_review', 'contract_help', 'premium_bundle'):
            self.assertIn(f'{package}:', SELLER_BRIDGE)
        self.assertIn("destination.searchParams.set('seller_package', selected)", SELLER_BRIDGE)
        self.assertIn('link.textContent = selectedPackage.cta', SELLER_BRIDGE)
        self.assertIn("cta: 'Request flat-fee MLS details'", SELLER_BRIDGE)
        self.assertIn("const primaryCtaLabels = new Set", SELLER_BRIDGE)
        self.assertIn("'Start free seller intake'", SELLER_BRIDGE)
        self.assertIn("const isCampaignPrimaryCta = primaryCtaLabels.has(link.textContent.trim());", SELLER_BRIDGE)
        self.assertIn("FSBO Seller Expanded Campaign Landing Viewed", SELLER_BRIDGE)

    def test_admin_seller_workspace_can_create_allowlisted_fsbo_campaign_links_and_copy(self):
        self.assertIn("FSBO Campaign Toolkit", HTML)
        self.assertIn("copySellerCampaignLink()", HTML)
        self.assertIn("copySellerCampaignInvitation()", HTML)
        self.assertIn("printSellerCampaignFlyer()", HTML)
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

    def test_admin_can_print_a_self_contained_seller_campaign_flyer(self):
        self.assertIn("Print Seller Flyer", HTML)
        self.assertIn("window.printSellerCampaignFlyer", HTML)
        self.assertIn("Printable seller flyer opened.", HTML)
        self.assertIn("Seller Campaign Flyer Printed", HTML)
        self.assertIn("This is an intake, not checkout, representation", HTML)

    def test_admin_can_create_privacy_safe_homebuyer_acquisition_links_and_copy(self):
        self.assertIn("Homebuyer Campaign Toolkit", HTML)
        self.assertIn("copyBuyerCampaignLink()", HTML)
        self.assertIn("copyBuyerCampaignInvitation()", HTML)
        self.assertIn("printBuyerCampaignFlyer()", HTML)
        self.assertIn("previewBuyerCampaignLink()", HTML)
        self.assertIn('id="buyerCampaignChannel"', HTML)
        self.assertIn('id="buyerCampaignName"', HTML)
        self.assertIn("https://www.homeofferflow.com/buyers?", HTML)
        self.assertIn("Homebuyer Campaign Link Copied", HTML)
        self.assertIn("Homebuyer Campaign Invitation Copied", HTML)
        self.assertIn("never a buyer’s identity, property, financing, or offer details", HTML)

    def test_admin_can_print_a_self_contained_buyer_campaign_flyer(self):
        self.assertIn("Print Buyer Flyer", HTML)
        self.assertIn("window.printBuyerCampaignFlyer", HTML)
        self.assertIn("Homebuyer Campaign Flyer Printed", HTML)
        self.assertIn("Printable buyer flyer opened.", HTML)
        self.assertIn("$99 only when your completed packet is ready", HTML)

    def test_seller_address_autocomplete_fails_softly_and_has_a_google_compatibility_path(self):
        self.assertIn("libraries=places", HTML)
        self.assertIn("v=weekly", HTML)
        self.assertIn("const waitForPlaces", HTML)
        self.assertIn("typeof google.maps.importLibrary !== 'function'", HTML)
        self.assertIn("wireLegacyGoogleAddressInputs", HTML)
        self.assertIn("google.maps.places.Autocomplete", HTML)
        self.assertIn("Google Places autocomplete is unavailable; manual address entry remains available.", HTML)
        self.assertIn("fsboPropertyAddress: fillFsboAddressFields", HTML)
        self.assertIn("function addressAutocompleteInputs()", HTML)

    def test_google_selected_seller_address_updates_progress_and_advances_to_email(self):
        start = HTML.index("function fillFsboAddressFields(components)")
        end = HTML.index("function tryInitAutocomplete()", start)
        fill = HTML[start:end]
        self.assertIn("addressEl.dispatchEvent(new Event('input', { bubbles: true }))", fill)
        self.assertIn("const emailEl = document.getElementById('fsboSellerEmail');", fill)
        self.assertIn("window.setTimeout(() => emailEl.focus(), 0);", fill)

    def test_seller_intake_has_a_hidden_bot_guard_without_adding_required_fields(self):
        self.assertIn('id="fsboWebsiteConfirm"', HTML)
        self.assertIn('fsbo_website_confirm: fsboVal(\'fsboWebsiteConfirm\')', HTML)
        self.assertIn('aria-hidden="true"', HTML)

    def test_title_company_interest_uses_the_api_canonical_category(self):
        self.assertIn('name="fsboPartner" value="title"> Title company', HTML)
        self.assertNotIn('name="fsboPartner" value="title_company"', HTML)

    def test_selected_partner_interests_use_checked_allowlisted_values(self):
        self.assertIn("const fsboPartnerCategories = new Set", HTML)
        self.assertIn("function getFsboPartners()", HTML)
        self.assertIn('input[name="fsboPartner"]:checked', HTML)
        self.assertIn("fsboPartnerCategories.has(category)", HTML)

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
        optional_details = HTML.index('Add timing or contact details')
        customization = HTML.index('Customize your plan or explore services')
        packages = HTML.index('class="fsbo-package-grid"')
        partners = HTML.index('Partner suggestions wanted')
        full = HTML.index('id="fsboSellerSubmit"')
        self.assertLess(quick, packages)
        self.assertLess(quick, optional_details)
        self.assertLess(quick, customization)
        self.assertLess(quick, partners)
        self.assertLess(quick, full)
        self.assertIn('<details class="partner-optional-details" style="margin-top:.9rem;">', HTML)
        customization_start = HTML.index('<details class="partner-optional-details" style="margin-top:1rem;">')
        customization_end = HTML.index('</details>', customization_start)
        customization_section = HTML[customization_start:customization_end]
        self.assertIn('id="fsboGuidedGoalCard"', customization_section)
        self.assertIn('class="fsbo-package-grid"', customization_section)
        self.assertIn('Partner suggestions wanted', customization_section)
        self.assertIn("document.querySelectorAll('[data-fsbo-submit]')", HTML)
        self.assertIn("Request ${item.title} Details", HTML)

    def test_launch_kit_package_copy_clarifies_ready_to_launch_fit(self):
        self.assertIn('Best for sellers ready to launch.', HTML)
        self.assertIn('data-fsbo-need="launch_kit"', HTML)

    def test_fsbo_submit_buttons_expose_busy_state_while_saving(self):
        start = HTML.index("window.submitFsboSellerLead = async function")
        end = HTML.index("fsboDraftFields.forEach", start)
        submit = HTML[start:end]
        self.assertIn("button.setAttribute('aria-busy', 'true')", submit)
        self.assertIn("button.setAttribute('aria-busy', 'false')", submit)
        self.assertIn("button.textContent = 'Saving…'", submit)

    def test_fsbo_submission_status_is_announced_as_one_atomic_message(self):
        self.assertIn('id="fsboSellerStatus" class="platform-status" role="status" aria-live="polite" aria-atomic="true"', HTML)

    def test_quick_submit_validates_and_focuses_the_actual_required_field(self):
        start = HTML.index("window.submitFsboSellerLead")
        end = HTML.index("const submissionKey = fsboSubmissionKey(payload);", start)
        submit = HTML[start:end]
        self.assertIn("emailInput?.checkValidity()", submit)
        self.assertIn("Enter a valid email address to save your seller plan.", submit)
        self.assertIn("setAttribute('aria-invalid'", submit)
        self.assertIn("(!hasAddress ? addressInput : emailInput)?.focus();", submit)

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
