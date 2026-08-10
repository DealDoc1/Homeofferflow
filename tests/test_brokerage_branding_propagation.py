import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
PRODUCTION = (ROOT / "api" / "fill-pdf.py").read_text(encoding="utf-8")
STAGING = (ROOT / "api" / "fill_pdf_20_19_staging.py").read_text(encoding="utf-8")
VERIFIED = (ROOT / "lib" / "verified_20_19.py").read_text(encoding="utf-8")


class BrokerageBrandingPropagationTests(unittest.TestCase):
    def test_saved_offer_payload_carries_active_brokerage_branding(self):
        for value in ("brokerageName", "brokerageLogoUrl", "brokerageBrandColor", "brokerageContactEmail"):
            self.assertIn(value, INDEX)
        self.assertIn("window.hofPlatform?.brokerage", INDEX)

    def test_success_page_surfaces_connected_brokerage_branding(self):
        for value in ("successBrokerageBrand", "Offer packet prepared with your brokerage workspace.", "brandColor", "brandLogo"):
            self.assertIn(value, INDEX)
        self.assertIn("/^#[0-9a-f]{6}$/i", INDEX)

    def test_brokerage_disclaimer_is_labeled_and_propagated_without_replacing_legal_copy(self):
        self.assertIn("brokerageDisclaimer", INDEX)
        self.assertIn("Brokerage note:", INDEX)
        self.assertIn(".slice(0, 500)", INDEX)
        self.assertIn("approvedEducationalDisclaimer", INDEX)

    def test_production_and_staging_signing_messages_identify_brokerage(self):
        for source in (PRODUCTION, STAGING):
            self.assertIn("brokerage_name", source)
            self.assertIn("brokerageName", source)
            self.assertIn("prepared_by_line", source)
            self.assertIn("HomeOfferFlow", source)

    def test_signer_requester_identity_preserves_brokerage_and_platform(self):
        for source in (PRODUCTION, VERIFIED):
            self.assertIn('f"{str(brokerage_name)[:180]} via HomeOfferFlow"', source)
            self.assertIn('"custom_requester_name": (', source)


if __name__ == "__main__":
    unittest.main()
