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
        ):
            self.assertIn(event, script)

        self.assertIn("trackEvent(name, data)", script)
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

    def test_seller_address_autocomplete_fails_softly_and_has_a_google_compatibility_path(self):
        self.assertIn("libraries=places", HTML)
        self.assertIn("typeof google.maps.importLibrary !== 'function'", HTML)
        self.assertIn("wireLegacyGoogleAddressInputs", HTML)
        self.assertIn("google.maps.places.Autocomplete", HTML)
        self.assertIn("Google Places autocomplete is unavailable; manual address entry remains available.", HTML)
        self.assertIn("['fsboPropertyAddress', fillFsboAddressFields]", HTML)

    def test_seller_intake_has_a_hidden_bot_guard_without_adding_required_fields(self):
        self.assertIn('id="fsboWebsiteConfirm"', HTML)
        self.assertIn('fsbo_website_confirm: fsboVal(\'fsboWebsiteConfirm\')', HTML)
        self.assertIn('aria-hidden="true"', HTML)

    def test_title_company_interest_uses_the_api_canonical_category(self):
        self.assertIn('name="fsboPartner" value="title"> Title company', HTML)
        self.assertNotIn('name="fsboPartner" value="title_company"', HTML)


if __name__ == "__main__":
    unittest.main()
