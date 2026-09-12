import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class GoogleAddressAutocompleteCoverageTests(unittest.TestCase):
    def test_every_current_address_entry_control_is_discoverable(self):
        # addressAutocompleteInputs intentionally matches both id and name so
        # static wizard controls and fields created inside signed-in dialogs
        # receive the same Google Places experience.
        required_controls = {
            "buyerMailAddr", "propAddress", "escrowAddress", "salePropertyAddr",
            "sellerMailAddr", "profInvestorEscrowAddress", "profEscrowAddress",
            "brandOfficeAddress", "sellerLeadAddress", "listingWorkspaceAddress",
            "fsboPropertyAddress", "clientAddress", "propertyAddress", "address", "hofSellerAddress", "profInvestorMailing",
        }
        for control in required_controls:
            self.assertRegex(
                INDEX,
                rf'<input[^>]+(?:id|name)="{re.escape(control)}"',
                msg=f"{control} must remain an address input covered by Google Places.",
            )

        self.assertIn("document.querySelectorAll('input[id], input[name]')", INDEX)
        self.assertIn("/(?:address|addr)/i.test(`${input.id} ${input.name}`)", INDEX)
        self.assertIn("const addressFieldMetadata = input =>", INDEX)
        self.assertIn("associatedLabels", INDEX)
        self.assertIn("input.closest('label')?.textContent", INDEX)
        self.assertIn("/(?:street|mailing|office|property|escrow)\\s+address/i.test(addressFieldMetadata(input))", INDEX)
        self.assertIn("!['email', 'hidden', 'checkbox', 'radio', 'submit', 'button'].includes(input.type)", INDEX)
        self.assertIn("['propertyToSell', 'profInvestorMailing']", INDEX)
        self.assertIn("legacyAddressKeys.has(input.name)", INDEX)

    def test_late_rendered_address_inputs_are_wired_on_focus(self):
        self.assertIn("document.addEventListener('focusin'", INDEX)
        self.assertIn("if (!isHofAddressInput(input)) return;", INDEX)
        self.assertIn("window._hofPlacesSetup = wireAddressInput", INDEX)
        self.assertIn("Promise.resolve(window.loadHofPlaces?.()).then(() => wireAddressInput())", INDEX)

    def test_late_inserted_address_inputs_are_registered_before_focus(self):
        self.assertIn("function observeAddedAddressInputs()", INDEX)
        self.assertIn("new MutationObserver(records =>", INDEX)
        self.assertIn("observer.observe(document.body, { childList: true, subtree: true });", INDEX)
        self.assertIn("if (_autocompleteService) wireAddressInput();", INDEX)

    def test_address_inputs_keep_a_native_fallback_without_replacing_google_places(self):
        self.assertIn("input.setAttribute('autocomplete', 'street-address');", INDEX)
        self.assertIn("input.setAttribute('inputmode', 'text');", INDEX)
        self.assertIn("input.dataset.hofGoogleAddress = 'true';", INDEX)
        self.assertIn("Google remains the primary picker", INDEX)
        self.assertIn("addressAutocompleteInputs();\n\n  // Agreement, profile, and workspace panels", INDEX)

    def test_static_private_address_inputs_declare_street_address_semantics(self):
        # The dynamic detector still wires every late-rendered dialog to Google
        # Places. These static entry points also expose their intent directly
        # to the browser before that code runs.
        for control in ("fsboPropertyAddress", "clientAddress", "hofSellerAddress", "profInvestorMailing", "profInvestorEscrowAddress", "profEscrowAddress"):
            self.assertRegex(
                INDEX,
                rf'<input[^>]+(?:id|name)="{control}"[^>]+autocomplete="street-address"',
            )
        self.assertGreaterEqual(INDEX.count('name="propertyAddress" required maxlength="400" autocomplete="street-address"'), 4)
        self.assertIn('name="address" required maxlength="400" autocomplete="street-address" inputmode="text"', INDEX)

    def test_late_rendered_legacy_address_controls_are_observed(self):
        self.assertIn("const HOF_LEGACY_ADDRESS_KEYS = new Set(['propertyToSell', 'profInvestorMailing']);", INDEX)
        self.assertIn("const isHofAddressInput = input => input instanceof HTMLInputElement", INDEX)
        self.assertIn("node.querySelectorAll?.('input[id], input[name]').forEach(input => controls.push(input));", INDEX)
        self.assertIn("return controls.some(isHofAddressInput);", INDEX)
        self.assertIn("function wireLegacyGoogleAddressInputs", INDEX)

    def test_client_mailing_selection_prefills_city_state_zip_without_treating_it_as_an_address(self):
        self.assertIn("clientAddress: fillClientMailingAddressFields", INDEX)
        self.assertIn("function fillClientMailingAddressFields(components)", INDEX)
        self.assertIn("#txr1501AgreementForm [name=\"clientCityStateZip\"]", INDEX)
        self.assertNotIn("'clientCityStateZip'", INDEX.split("const HOF_LEGACY_ADDRESS_KEYS", 1)[1].split(";", 1)[0])

    def test_brokerage_office_selection_fills_city_state_and_zip(self):
        start = INDEX.index("function fillBrandOfficeAddressFields(components)")
        end = INDEX.index("function fillFsboAddressFields(components)", start)
        handler = INDEX[start:end]
        self.assertIn("if (t.includes('postal_code')) zip = c.long_name;", handler)
        self.assertIn("const zipEl = document.getElementById('brandOfficeZip');", handler)
        self.assertIn("if (zipEl && zip) zipEl.value = zip;", handler)

    def test_selection_telemetry_excludes_transaction_addresses(self):
        self.assertIn("trackEvent('Google Address Selected'", INDEX)
        self.assertIn("{ field, service: _autocompleteService || 'unknown' }", INDEX)
        self.assertNotIn("trackEvent('Google Address Selected', { address", INDEX)
        self.assertNotIn("trackEvent('Google Address Selected', { place", INDEX)

    def test_keyboard_navigation_starts_at_the_expected_end_of_the_suggestion_list(self):
        self.assertIn("const nextIndex = _activeSuggestionIndex < 0", INDEX)
        self.assertIn("? (direction === 1 ? 0 : options.length - 1)", INDEX)
        self.assertIn("_setActiveAddressSuggestion(nextIndex);", INDEX)

    def test_places_replays_a_focused_address_typed_while_the_library_loaded(self):
        self.assertIn("If it\n    // becomes ready after the user has already started typing", INDEX)
        self.assertIn("document.activeElement === input && input.value.trim().length >= 3", INDEX)
        self.assertIn("window.setTimeout(() => input.dispatchEvent(new Event('input', { bubbles: true })), 0);", INDEX)

    def test_address_suggestions_close_when_the_viewport_moves(self):
        self.assertIn("window.addEventListener('resize', _hideDropdown, { once: true });", INDEX)
        self.assertIn("document.addEventListener('scroll', _hideDropdown, { capture: true, once: true });", INDEX)
