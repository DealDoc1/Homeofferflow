import base64
import hashlib
import importlib.util
import json
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "platform_form_source_upload", ROOT / "lib" / "platform_form_source_upload.py"
)
module = importlib.util.module_from_spec(SPEC)
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-role-test")
SPEC.loader.exec_module(module)


class PlatformFormSourceUploadTests(unittest.TestCase):
    def _payload(self, content=b"%PDF-1.7\nsource"):
        return {
            "brokerageId": "brokerage-1",
            "formCode": "TXR-1507",
            "sourceRevision": "06-15-26",
            "originalFilename": "TXR1507.pdf",
            "sourceSha256": hashlib.sha256(content).hexdigest(),
            "contentBase64": base64.b64encode(content).decode("ascii"),
            "authorizationAttested": True,
        }

    def test_parser_accepts_pdf_and_recomputes_exact_fingerprint(self):
        parsed = module._parse_payload(json.dumps(self._payload()).encode())
        self.assertEqual(parsed["form_code"], "TXR-1507")
        self.assertEqual(parsed["source_revision"], "06-15-26")
        self.assertEqual(parsed["source_sha256"], hashlib.sha256(parsed["content"]).hexdigest())

    def test_parser_accepts_supplied_trec_seller_sources(self):
        for form_code, filename in (("TREC-55-1", "seller_disclosure_notice_55-1.pdf"), ("TREC-61-0", "seller_water_disclosure_61-0.pdf")):
            payload = self._payload()
            payload["formCode"] = form_code
            payload["originalFilename"] = filename
            parsed = module._parse_payload(json.dumps(payload).encode())
            self.assertEqual(parsed["form_code"], form_code)

    def test_parser_accepts_every_new_shared_txr_source_code(self):
        for form_code in ("TXR-1905", "TXR-1914", "TXR-1917", "TXR-1919", "TXR-1948", "TXR-1953", "TXR-1954"):
            payload = self._payload()
            payload["formCode"] = form_code
            payload["originalFilename"] = f"{form_code.replace('-', '')}.pdf"
            parsed = module._parse_payload(json.dumps(payload).encode())
            self.assertEqual(parsed["form_code"], form_code)

    def test_shared_txr_source_migration_matches_the_intake_allowlist(self):
        migration = (ROOT / "supabase" / "migrations" / "20260822151500_expand_shared_txr_source_codes.sql").read_text()
        for form_code in ("TXR-1905", "TXR-1914", "TXR-1917", "TXR-1919", "TXR-1948", "TXR-1953", "TXR-1954"):
            self.assertIn(f"'{form_code}'", migration)

    def test_parser_rejects_non_pdf_even_with_valid_base64(self):
        content = b"not a pdf"
        with self.assertRaisesRegex(ValueError, "not a PDF"):
            module._parse_payload(json.dumps(self._payload(content)).encode())

    def test_parser_rejects_fingerprint_mismatch(self):
        payload = self._payload()
        payload["sourceSha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "fingerprint does not match"):
            module._parse_payload(json.dumps(payload).encode())

    def test_parser_requires_authorization_attestation(self):
        payload = self._payload()
        payload["authorizationAttested"] = False
        with self.assertRaisesRegex(ValueError, "authorized to approve"):
            module._parse_payload(json.dumps(payload).encode())

    def test_parser_rejects_unknown_form_code(self):
        payload = self._payload()
        payload["formCode"] = "TXR-9999"
        with self.assertRaisesRegex(ValueError, "supported form source"):
            module._parse_payload(json.dumps(payload).encode())

    def test_response_contract_reports_the_actual_released_workflow_status(self):
        source = (ROOT / "lib" / "platform_form_source_upload.py").read_text()
        self.assertIn('"workflowActivated": _workflow_activation_status(parsed["form_code"])', source)
        self.assertFalse(module._workflow_activation_status("TXR-1507"))
        previous = module.TXR_SIGNING_ENABLED
        try:
            module.TXR_SIGNING_ENABLED = True
            self.assertTrue(module._workflow_activation_status("TXR-1507"))
            self.assertFalse(module._workflow_activation_status("TXR-1101"))
        finally:
            module.TXR_SIGNING_ENABLED = previous
        self.assertIn("Platform-admin access is required", source)
        self.assertIn("authorization_attested", source)

    def test_private_source_endpoint_does_not_advertise_wildcard_cors(self):
        source = (ROOT / "lib" / "platform_form_source_upload.py").read_text()
        self.assertIn('handler.send_header("Access-Control-Allow-Origin", PUBLIC_APP_ORIGIN)', source)
        self.assertIn('handler.send_header("Vary", "Origin")', source)
        self.assertNotIn('handler.send_header("Access-Control-Allow-Origin", "*")', source)

    def test_post_route_passes_raw_json_bytes_to_the_fingerprint_parser(self):
        source = (ROOT / "lib" / "platform_form_source_upload.py").read_text()
        self.assertIn("raw_payload = self.rfile.read(length)", source)
        self.assertIn("_upload_source(user, raw_payload)", source)

    def test_hobby_safe_route_is_integrated_into_existing_admin_function(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text()
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("platform_source_brokerages", source)
        self.assertIn('"upload_platform_form_source"', source)
        self.assertIn("MAX_SOURCE_UPLOAD_BODY_BYTES = 15 * 1024 * 1024", source)
        self.assertIn("if length > MAX_BODY_BYTES:", source)
        self.assertIn("/api/admin-dashboard?scope=platform_source_brokerages", html)
        self.assertIn("action:'upload_platform_form_source'", html)
        self.assertIn("document.getElementById('accountPanelAdmin') || document.getElementById('accountPanelDashboard')", html)
        self.assertIn("Universal form library maintenance", html)
        self.assertIn("Agents use the universal released form library", html)
        self.assertIn("does not gate agent access", html)


if __name__ == "__main__":
    unittest.main()
