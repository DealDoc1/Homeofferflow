from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class OfferDuplicateWorkspaceTests(unittest.TestCase):
    def test_duplicate_scrubs_source_packet_and_signing_metadata(self):
        start = HTML.index("async function duplicateOffer(id)")
        end = HTML.index("\n  async function deleteOffer", start)
        body = HTML[start:end]

        self.assertIn("const copyData = { ...(offer.offer_data || {}) };", body)
        for key in (
            "'_hofOfferId'",
            "'signwell'",
            "'signwellDocumentId'",
            "'signwellStatus'",
            "'generatedAt'",
            "'packetGeneratedAt'",
            "'signingUrl'",
            "'recipients'",
        ):
            self.assertIn(key, body)
        self.assertIn("status: 'Draft'", body)
        self.assertIn("signwell_document_id", body)


if __name__ == "__main__":
    unittest.main()
