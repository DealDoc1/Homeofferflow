from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class LazyPlacesLoadingTests(unittest.TestCase):
    def test_places_is_loaded_only_after_an_address_workflow_opens(self):
        self.assertIn("window.loadHofPlaces = function()", HTML)
        self.assertIn("window._hofPlacesLoadPromise", HTML)
        self.assertIn("document.head.appendChild(script)", HTML)
        self.assertNotIn('<script src="https://maps.googleapis.com/maps/api/js?', HTML)
        self.assertIn("const placesLoad = window.loadHofPlaces?.();", HTML)
        self.assertIn("Promise.resolve(window.loadHofPlaces?.()).then(() =>", HTML)

    def test_places_failure_keeps_manual_address_entry_available(self):
        self.assertIn("manual address entry remains available", HTML)
        self.assertIn("script.onerror = () =>", HTML)
        self.assertIn("window.loadHofPlaces?.();", HTML)

    def test_every_address_input_is_wired_including_late_rendered_forms(self):
        self.assertIn("function addressAutocompleteInputs()", HTML)
        self.assertIn("document.querySelectorAll('input[id], input[name]')", HTML)
        self.assertIn("/(?:address|addr)/i.test(`${input.id} ${input.name}`)", HTML)
        self.assertIn("'profInvestorMailing'", HTML)
        self.assertIn(".map(input => [input, callbacks[input.id] || null])", HTML)
        self.assertIn('name="clientAddress"', HTML)
        self.assertIn('name="propertyAddress"', HTML)
        self.assertIn("document.addEventListener('focusin'", HTML)
        self.assertIn("fillBrandOfficeAddressFields", HTML)
        for input_id in (
            "escrowAddress", "sellerMailAddr", "profInvestorEscrowAddress",
            "profEscrowAddress", "brandOfficeAddress", "sellerLeadAddress",
            "listingWorkspaceAddress", "hofSellerAddress",
        ):
            self.assertIn(f'id="{input_id}"', HTML)


if __name__ == "__main__":
    unittest.main()
