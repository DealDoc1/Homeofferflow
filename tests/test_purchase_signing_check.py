from contextlib import redirect_stdout
from io import BytesIO, StringIO
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pypdf import PdfReader

from scripts.qa.purchase_signing_check import (
    EXISTING_QA_DOCUMENT, build_packet, build_payload, diagnose_credential,
    existing_key, layout_fingerprint, send_once,
)


SHA = "da511a0d242d3026e7b716ad6cfbfeea3c4c49a5"


class PurchaseSigningCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet, cls.fields, cls.cases = build_packet()

    def test_specimen_is_reproducible_and_contains_only_changed_source_pages(self):
        again, fields, cases = build_packet()
        self.assertEqual(layout_fingerprint(self.packet, self.fields, self.cases),
                         layout_fingerprint(again, fields, cases))
        self.assertEqual(self.fields, fields)
        self.assertEqual(self.cases, cases)
        self.assertEqual(len(PdfReader(BytesIO(again)).pages), 13)
        self.assertEqual([c["source_pages"] for c in cases], [[1, 8, 10, 11], [1, 8, 10, 11], [1, 8, 10, 11, 13]])
        self.assertEqual([c["field_count"] for c in cases], [4, 12, 10])
        self.assertEqual(len(fields[0]), 26)

    def test_reviewed_layout_hash_detects_a_moved_provider_field(self):
        shifted = [[dict(f) for f in self.fields[0]]]
        shifted[0][0]["x"] += 1
        self.assertNotEqual(layout_fingerprint(self.packet, self.fields, self.cases),
                            layout_fingerprint(self.packet, shifted, self.cases))

    def test_payload_is_nonbinding_parallel_and_restricted_to_the_approved_qa_inboxes(self):
        payload = build_payload(self.packet, self.fields, SHA)
        self.assertIs(payload["test_mode"], True)
        self.assertIs(payload["apply_signing_order"], False)
        self.assertIs(payload["draft"], False)
        self.assertIs(payload["reminders"], False)
        self.assertIs(payload["with_signature_page"], False)
        self.assertEqual({r["email"] for r in payload["recipients"]},
                         {"andrewchri@gmail.com", "brewbqinfo@gmail.com"})
        self.assertEqual({f["recipient_id"] for f in self.fields[0]}, {"qa_a", "qa_b"})
        self.assertEqual(len({f["api_id"] for f in self.fields[0]}), 26)
        with self.assertRaises(ValueError):
            build_payload(self.packet, self.fields, "main")

    def test_static_source_contains_no_original_editable_widgets_or_field_tree(self):
        reader = PdfReader(BytesIO(self.packet))
        self.assertFalse(reader.get_fields())
        for page in reader.pages:
            self.assertFalse(any(ref.get_object().get("/Subtype") == "/Widget"
                                 for ref in page.get("/Annots", [])))
            self.assertIn("QA", page.extract_text())
        self.assertTrue(reader.metadata.title.startswith("QA ONLY"))

    def test_selected_pages_keep_the_production_content_streams_exactly(self):
        reader = PdfReader(BytesIO(self.packet))
        for case in self.cases:
            for page_number, digest in zip(case["output_pages"], case["content_sha256"]):
                page = reader.pages[page_number - 1]
                self.assertEqual(hashlib.sha256(page.get_contents().get_data()).hexdigest(), digest)

    def test_every_translated_field_is_within_its_real_assembled_page(self):
        reader = PdfReader(BytesIO(self.packet))
        for field in self.fields[0]:
            page = reader.pages[field["page"] - 1]
            self.assertGreaterEqual(field["x"], 0)
            self.assertGreaterEqual(field["y"], 0)
            self.assertLessEqual((field["x"] + field["width"]) * .75, float(page.mediabox.width))
            self.assertLessEqual((field["y"] + field["height"]) * .75, float(page.mediabox.height))

    def test_successful_response_records_only_safe_metadata_and_cannot_resend(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            calls = []
            def post(url, **kwargs):
                calls.append((url, kwargs))
                self.assertEqual(json.loads(receipt.read_text())["status"], "started")
                return SimpleNamespace(status_code=201, json=lambda: {
                    "id": "qa-document", "status": "sent", "test_mode": True,
                    "embedded_signing_url": "https://example.test/SECRET_LINK",
                })
            result = send_once(self.packet, self.fields, SHA, "SECRET_KEY", receipt, post=post)
            self.assertEqual(result["status"], "created")
            self.assertNotIn("SECRET", receipt.read_text())
            with self.assertRaises(ValueError):
                send_once(self.packet, self.fields, SHA, "SECRET_KEY", receipt, post=post)
            self.assertEqual(len(calls), 1)

    def test_ambiguous_failure_is_recorded_without_retries_or_sensitive_error_text(self):
        for mode in ("timeout", "http_error", "invalid_json", "missing_test_mode"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                receipt = Path(directory) / "receipt.json"
                calls = []
                def post(url, **kwargs):
                    calls.append(url)
                    if mode == "timeout":
                        raise TimeoutError("SECRET_KEY and SECRET_SIGNING_LINK")
                    if mode == "http_error":
                        return SimpleNamespace(status_code=429)
                    if mode == "invalid_json":
                        return SimpleNamespace(status_code=201, json=lambda: (_ for _ in ()).throw(ValueError("SECRET_KEY")))
                    return SimpleNamespace(status_code=201, json=lambda: {"id": "qa-document"})
                output = StringIO()
                with redirect_stdout(output):
                    result = send_once(self.packet, self.fields, SHA, "SECRET_KEY", receipt, post=post)
                self.assertEqual(result["status"], "unconfirmed")
                self.assertNotIn("SECRET", receipt.read_text() + output.getvalue())
                self.assertEqual(len(calls), 1)
                with self.assertRaises(ValueError):
                    send_once(self.packet, self.fields, SHA, "SECRET_KEY", receipt, post=post)

    def test_serialized_controls_are_decoded_and_direct_environment_values_are_not_reinterpreted(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"SIGNWELL_API_KEY": ""}):
            path = Path(directory) / "environment.local"
            path.write_text('SIGNWELL_API_KEY="TEST_SECRET\\r\\n"\n')
            self.assertEqual(existing_key(path), "TEST_SECRET")
            self.assertEqual(existing_key(path, trim=False), "TEST_SECRET\r\n")
            path.write_text("SIGNWELL_API_KEY='TEST_SECRET'\n")
            self.assertEqual(existing_key(path), "TEST_SECRET")
            with patch.dict("os.environ", {"SIGNWELL_API_KEY": "DIRECT_SECRET\\n"}):
                self.assertEqual(existing_key(path), "DIRECT_SECRET\\n")

    def test_read_only_diagnostic_compares_candidates_without_exporting_values_or_links(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"SIGNWELL_API_KEY": ""}):
            path = Path(directory) / "environment.local"
            path.write_text('SIGNWELL_API_KEY="TEST_SECRET\\n"\n')
            calls = []
            def get(url, **kwargs):
                calls.append(url)
                self.assertTrue(url.endswith(EXISTING_QA_DOCUMENT))
                valid = kwargs["headers"]["X-Api-Key"] == "TEST_SECRET"
                return SimpleNamespace(status_code=200 if valid else 401, json=lambda: {
                    "id": EXISTING_QA_DOCUMENT, "name": "QA ONLY - example",
                    "embedded_signing_url": "SECRET_SIGNING_LINK",
                })
            result = diagnose_credential(path, get=get)
            self.assertIs(result["decoding_changed"], True)
            self.assertIs(result["runtime_trailing_whitespace"], True)
            self.assertIs(result["runtime_transport_controls"], True)
            self.assertEqual(result["legacy"]["http_status"], 401)
            self.assertEqual(result["normalized"]["http_status"], 200)
            self.assertIs(result["normalized"]["confirmed_qa_document"], True)
            self.assertNotIn("SECRET", json.dumps(result))
            self.assertEqual(len(calls), 2)

    def test_identical_candidate_and_diagnostic_errors_make_no_extra_requests_or_expose_secrets(self):
        with patch.dict("os.environ", {"SIGNWELL_API_KEY": "TEST_SECRET"}):
            calls = []
            def get(url, **kwargs):
                calls.append(url)
                raise TimeoutError("TEST_SECRET")
            result = diagnose_credential(None, get=get)
            self.assertIs(result["decoding_changed"], False)
            self.assertEqual(len(calls), 1)
            self.assertNotIn("TEST_SECRET", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
