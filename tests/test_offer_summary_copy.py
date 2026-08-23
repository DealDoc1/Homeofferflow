from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class OfferSummaryCopyTests(unittest.TestCase):
    def test_detail_view_exposes_copy_summary_action(self):
        self.assertIn('onclick="copyOfferSummary(\'${esc(offer.id)}\')"', HTML)
        self.assertIn("root.copyOfferSummary = async function(offerId)", HTML)

    def test_summary_uses_operational_fields_and_excludes_private_identifiers(self):
        start = HTML.index("root.copyOfferSummary = async function(offerId)")
        end = HTML.index("root.hofRenderOfferWorkspaceV10", start)
        block = HTML[start:end]
        for field in ("Property:", "Buyer:", "Offer amount:", "Financing:", "Status:", "Buyer signing:", "Updated:"):
            self.assertIn(field, block)
        self.assertNotIn("buyer_email", block)
        self.assertNotIn("signwell_document_id", block)
        self.assertIn("root.__hofCurrentOffer", block)
        self.assertIn("offer_summary_copied", block)


if __name__ == "__main__":
    unittest.main()
