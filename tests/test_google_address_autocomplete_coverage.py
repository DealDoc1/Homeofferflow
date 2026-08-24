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
            "fsboPropertyAddress", "clientAddress", "propertyAddress", "hofSellerAddress", "clientCityStateZip",
        }
        for control in required_controls:
            self.assertRegex(
                INDEX,
                rf'<input[^>]+(?:id|name)="{re.escape(control)}"',
                msg=f"{control} must remain an address input covered by Google Places.",
            )

        self.assertIn("document.querySelectorAll('input[id], input[name]')", INDEX)
        self.assertIn("/(?:address|addr)/i.test(`${input.id} ${input.name}`)", INDEX)
        self.assertIn("['propertyToSell', 'profInvestorMailing', 'clientCityStateZip']", INDEX)
        self.assertIn("legacyAddressKeys.has(input.name)", INDEX)

    def test_late_rendered_address_inputs_are_wired_on_focus(self):
        self.assertIn("document.addEventListener('focusin'", INDEX)
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

    def test_late_rendered_legacy_address_controls_are_observed(self):
        self.assertIn("const HOF_LEGACY_ADDRESS_KEYS = new Set(['propertyToSell', 'profInvestorMailing', 'clientCityStateZip']);", INDEX)
        self.assertIn("const isHofAddressInput = input => input instanceof HTMLInputElement", INDEX)
        self.assertIn("node.querySelectorAll?.('input[id], input[name]').forEach(input => controls.push(input));", INDEX)
        self.assertIn("return controls.some(isHofAddressInput);", INDEX)
        self.assertIn("function wireLegacyGoogleAddressInputs", INDEX)

    def test_selection_telemetry_excludes_transaction_addresses(self):
        self.assertIn("trackEvent('Google Address Selected'", INDEX)
        self.assertIn("{ field, service: _autocompleteService || 'unknown' }", INDEX)
        self.assertNotIn("trackEvent('Google Address Selected', { address", INDEX)
        self.assertNotIn("trackEvent('Google Address Selected', { place", INDEX)
