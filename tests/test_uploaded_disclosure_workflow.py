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

    def test_upload_rejects_files_without_a_pdf_signature_before_packet_generation(self):
        self.assertIn("file.slice(0, 4).arrayBuffer()", INDEX_HTML)
        self.assertIn("signature !== '%PDF'", INDEX_HTML)
        self.assertIn("This file is not a readable PDF", INDEX_HTML)

    def test_upload_list_can_remove_one_document_without_clearing_the_packet(self):
        self.assertIn("function removeUploadedDisclosure(index)", INDEX_HTML)
        self.assertIn("docs.splice(index, 1)", INDEX_HTML)
        self.assertIn("uploaded-doc-remove", INDEX_HTML)
        self.assertIn("Remove ${escapeHtml(d.name)}", INDEX_HTML)

    def test_attachment_acknowledgement_is_invalidated_after_packet_changes(self):
        self.assertIn("function resetUploadedDisclosureAcknowledgement()", INDEX_HTML)
        self.assertIn("[docs[index], docs[target]] = [docs[target], docs[index]];\n    resetUploadedDisclosureAcknowledgement();", INDEX_HTML)
        self.assertIn("docs[index].type = event.target.value;\n        resetUploadedDisclosureAcknowledgement();", INDEX_HTML)
        self.assertIn("docs.splice(index, 1);\n    resetUploadedDisclosureAcknowledgement();", INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
