import unittest
from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AddressAutocompleteTests(unittest.TestCase):
    def test_google_places_is_requested_only_after_address_focus(self):
        self.assertIn("document.addEventListener('focusin'", HTML)
        self.assertIn("requestGooglePlaces();", HTML)
        self.assertNotIn('<script src="https://maps.googleapis.com/maps/api/js?', HTML)

    def test_all_current_address_inputs_share_the_autocomplete_registry(self):
        expected_ids = (
            "propAddress",
            "showingAddress",
            "buyerMailAddr",
            "escrowAddress",
            "salePropertyAddr",
            "fsboPropertyAddress",
            "sellerLeadAddress",
            "brandOfficeAddress",
            "profInvestorMailing",
            "profInvestorEscrowAddress",
            "profEscrowAddress",
        )
        for input_id in expected_ids:
            with self.subTest(input_id=input_id):
                self.assertIn(f"['{input_id}'", HTML)

    def test_suggestion_text_is_escaped_before_dropdown_rendering(self):
        self.assertIn("const escapeSuggestionText", HTML)
        self.assertIn("${escapeSuggestionText(main)}", HTML)
        self.assertIn("${escapeSuggestionText(secondary)}", HTML)

    def test_dynamic_account_panels_rewire_google_places_after_rendering(self):
        tab_function = HTML[HTML.index("function showAccountTab"):HTML.index("async function openAccountDashboard")]
        self.assertIn("renderAccountProfileForm()", tab_function)
        self.assertIn("renderBrokerageFoundationPanel()", tab_function)
        self.assertIn("renderSellerFoundationPanel()", tab_function)
        self.assertIn("if (typeof wireAddressInput === 'function') wireAddressInput();", tab_function)

    def test_google_library_completion_wires_the_field_that_triggered_loading(self):
        setup_function = HTML[HTML.index("async function setupPlacesServices()"):HTML.index("function initPlacesService()")]
        self.assertIn("_autocompleteService = true;", setup_function)
        self.assertIn("wireAddressInput();", setup_function)
        self.assertNotIn("getCurrentSteps()[state.step]", setup_function)


if __name__ == "__main__":
    unittest.main()
