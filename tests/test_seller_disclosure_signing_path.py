import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("seller_disclosure_signing_admin", ROOT / "api" / "admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SellerDisclosureSigningPathTests(unittest.TestCase):
    def test_recipient_order_matches_the_disclosure_execution_rows(self):
        recipients = MODULE._seller_disclosure_signing_recipients(
            {"seller_names": ["Seller One", "Seller Two"], "buyer_names": ["Buyer One"]},
            ["seller1@example.com", "seller2@example.com", "buyer1@example.com"],
        )
        self.assertEqual(
            [(recipient["id"], recipient["name"], recipient["email"]) for recipient in recipients],
            [
                ("1", "Seller One", "seller1@example.com"),
                ("2", "Seller Two", "seller2@example.com"),
                ("3", "Buyer One", "buyer1@example.com"),
            ],
        )

    def test_recipient_builder_requires_each_named_party_once(self):
        draft = {"seller_names": ["Seller One"], "buyer_names": ["Buyer One"]}
        with self.assertRaisesRegex(ValueError, "each named Seller and Buyer"):
            MODULE._seller_disclosure_signing_recipients(draft, ["seller@example.com"])
        with self.assertRaisesRegex(ValueError, "different"):
            MODULE._seller_disclosure_signing_recipients(draft, ["same@example.com", "same@example.com"])

    def test_backend_requires_reviewed_draft_and_uses_packet_offset(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        start = source.index("async def _send_seller_disclosure_for_signature")
        end = source.index("async def _render_representation_draft_preview", start)
        signing = source[start:end]
        self.assertIn("seller_review_attested=is.true", signing)
        self.assertIn("page_offset=4", signing)
        self.assertIn("signwell_document_id", signing)
        self.assertIn('"draft": True', signing)
        self.assertIn("_signwell_document_matches_signing_request", signing)
        self.assertIn("}/send", signing)
        self.assertIn("Nothing was sent.", signing)
        self.assertIn("send_seller_disclosure_for_signature", source)

    def test_lifecycle_migration_allows_server_managed_sent_and_signed_states(self):
        sql = (ROOT / "supabase" / "migrations" / "20260910005240_seller_disclosure_signing_lifecycle.sql").read_text()
        self.assertIn("'sent'", sql)
        self.assertIn("'signed'", sql)
        self.assertIn("signwell_document_id", sql)
        self.assertIn("hof_seller_disclosure_drafts_update_own", sql)

    def test_agent_workspace_can_refresh_and_download_only_its_signed_disclosure(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("sellerDisclosureId:draft.id", source)
        self.assertIn("hof-seller-refresh-signing", source)
        self.assertIn("hof-seller-download-signed", source)
        self.assertIn("HomeOfferFlow-signed-seller-disclosure.pdf", source)


if __name__ == "__main__":
    unittest.main()
