from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class OfferWorkspaceExportTests(unittest.TestCase):
    def test_export_is_available_from_the_filtered_workspace_view(self):
        self.assertIn("onclick=\"hofExportVisibleOffers()\"", HTML)
        self.assertIn("Download the visible offers as CSV", HTML)
        self.assertIn("const offers = sortedOffers(state.offers || []);", HTML)
        self.assertIn('onclick="startAccountOffer()">Start a new buyer offer</button>', HTML)

    def test_export_contains_operational_fields_without_client_email_or_ids(self):
        self.assertIn("['Property', 'Buyer', 'Offer amount', 'Status', 'Buyer signing', 'Updated']", HTML)
        self.assertIn("link.download = 'homeofferflow-offers.csv';", HTML)
        self.assertIn("Agent Offers Exported", HTML)
        self.assertNotIn("buyer_email", HTML[HTML.index("root.hofExportVisibleOffers"):HTML.index("root.hofSetOfferWorkspaceFilter")])


if __name__ == "__main__":
    unittest.main()
