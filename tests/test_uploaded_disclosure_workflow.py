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
        self.assertIn("type: suggestedUploadedDisclosureType(file.name)", INDEX_HTML)
        self.assertIn("I reviewed the uploaded PDFs, labels, and packet order", INDEX_HTML)

    def test_uploads_suggest_a_label_from_a_common_filename_without_removing_agent_control(self):
        self.assertIn("function suggestedUploadedDisclosureType(filename)", INDEX_HTML)
        for label in ("seller_disclosure", "survey", "hoa_documents", "pid_mud_notice", "lead_based_paint"):
            with self.subTest(label=label):
                self.assertIn("return '" + label + "'", INDEX_HTML)
        self.assertIn("return 'other';", INDEX_HTML)
        self.assertIn("The agent can change every suggested label", INDEX_HTML)
        self.assertIn("We suggest a label from each filename", INDEX_HTML)

    def test_upload_guidance_describes_the_current_packet_experience(self):
        self.assertIn("Upload PDF disclosures or listing-side documents to include them with the final offer packet.", INDEX_HTML)
        self.assertNotIn("Phase 1: upload PDF disclosures", INDEX_HTML)
        self.assertNotIn("Signature placement on uploaded docs is coming next.", INDEX_HTML)

    def test_supported_packet_boundary_uses_a_clear_next_step_not_internal_testing_language(self):
        start = INDEX_HTML.index("function confirmControlledLaunchSupport")
        end = INDEX_HTML.index("async function handlePayment", start)
        boundary = INDEX_HTML[start:end]
        self.assertIn("needs a short support review before purchase or generation", boundary)
        self.assertIn("Please contact support before purchasing or generating this packet.", boundary)
        self.assertNotIn("still testing", boundary)

    def test_supported_buyer_temporary_lease_is_not_stopped_before_generation(self):
        start = INDEX_HTML.index("function controlledLaunchUnsupportedPaths")
        end = INDEX_HTML.index("function validateParagraph4LeaseInputs", start)
        boundary = INDEX_HTML[start:end]
        self.assertNotIn("Buyer's Temporary Residential Lease", boundary)
        self.assertNotIn("data.buyerTemporaryLease", boundary)

    def test_upload_rejects_files_without_a_pdf_signature_before_packet_generation(self):
        self.assertIn("file.slice(0, 4).arrayBuffer()", INDEX_HTML)
        self.assertIn("signature !== '%PDF'", INDEX_HTML)
        self.assertIn("This file is not a readable PDF", INDEX_HTML)

    def test_uploads_append_safely_and_fit_the_function_payload_budget(self):
        start = INDEX_HTML.index("async function handleUploadedDisclosureDocs(fileList)")
        end = INDEX_HTML.index("function controlledLaunchUnsupportedPaths", start)
        handler = INDEX_HTML[start:end]
        self.assertIn("const maxFileBytes = 2 * 1024 * 1024;", handler)
        self.assertIn("const maxTotalBytes = Math.floor(2.5 * 1024 * 1024);", handler)
        self.assertIn("const docs = [...existingDocs];", handler)
        self.assertIn("existingDocs.length + files.length > maxFiles", handler)
        self.assertIn("existingBytes + selectedBytes > maxTotalBytes", handler)
        self.assertIn("duplicateName", handler)
        self.assertIn("window.hofUploadedDisclosureDocs = docs;", handler)
        self.assertIn("if (input) input.value = '';", handler)
        self.assertIn("Add up to 5 files, 2MB each and 2.5MB combined.", INDEX_HTML)

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

    def test_resuming_an_offer_never_reuses_prior_attachment_contents(self):
        self.assertIn("function resetUploadedDisclosureDraftForOffer(data = {})", INDEX_HTML)
        self.assertIn("window.hofUploadedDisclosureDocs = [];", INDEX_HTML)
        self.assertIn("resetUploadedDisclosureDraftForOffer(offer.offer_data || {});", INDEX_HTML)
        self.assertIn("resetUploadedDisclosureDraftForOffer({});", INDEX_HTML)
        self.assertIn("Re-upload required before sending:", INDEX_HTML)

    def test_duplicate_offer_drops_transaction_sensitive_attachments(self):
        self.assertIn("delete copyData.uploadedDisclosureDocs;", INDEX_HTML)
        self.assertIn("delete copyData.uploadedDocNames;", INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
