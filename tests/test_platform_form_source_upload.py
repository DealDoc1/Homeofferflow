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

    def test_response_contract_explicitly_keeps_workflow_inactive(self):
        source = (ROOT / "lib" / "platform_form_source_upload.py").read_text()
        self.assertIn('"workflowActivated": False', source)
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
        self.assertIn("Platform source-owner intake", html)


if __name__ == "__main__":
    unittest.main()
