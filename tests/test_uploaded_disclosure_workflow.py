import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class UploadedDisclosureWorkflowTests(unittest.TestCase):
    def test_upload_ui_labels_orders_and_confirms_documents(self):
        required = (
            "Packet order (first listed is appended first)",
            "uploadedDisclosureAck",
            "Seller's Disclosure",
            "Survey / T-47",
            "HOA / POA documents",
            "PID / MUD notice",
            "Lead-based paint disclosure",
            "moveUploadedDisclosure",
            "validateUploadedDisclosureDocs",
        )
        for copy in required:
            with self.subTest(copy=copy):
                self.assertIn(copy, INDEX_HTML)

    def test_generation_paths_validate_uploaded_documents_before_continuing(self):
        validation_call = "if (!validateUploadedDisclosureDocs()) return;"
        self.assertGreaterEqual(INDEX_HTML.count(validation_call), 2)
        self.assertIn("type: 'other'", INDEX_HTML)
        self.assertIn("I reviewed the uploaded PDFs, labels, and packet order", INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
