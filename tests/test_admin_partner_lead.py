import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "api" / "admin-partner-lead.py"
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
SPEC = importlib.util.spec_from_file_location("admin_partner_lead", MODULE_PATH)
admin_partner_lead = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(admin_partner_lead)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else []
        self.text = text if text is not None else "[]"

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.request = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None):
        self.request = {"method": "GET", "url": url, "headers": headers}
        return self.response

    def patch(self, url, headers=None, json=None):
        self.request = {"method": "PATCH", "url": url, "headers": headers, "json": json}
        return self.response


class AdminPartnerLeadTests(unittest.TestCase):
    lead_id = "e35eace9-2760-4b11-a01a-07ee65f2744e"

    def test_payload_requires_uuid_and_allowlisted_status(self):
        self.assertEqual(
            admin_partner_lead._parse_update_payload({"lead_id": self.lead_id, "status": "QUALIFIED"}),
            (self.lead_id, "qualified"),
        )
        with self.assertRaisesRegex(ValueError, "lead ID"):
            admin_partner_lead._parse_update_payload({"lead_id": "not-a-uuid", "status": "qualified"})
        with self.assertRaisesRegex(ValueError, "valid partner lead status"):
            admin_partner_lead._parse_update_payload({"lead_id": self.lead_id, "status": "deleted"})

    def test_default_admin_email_is_allowed(self):
        self.assertTrue(admin_partner_lead._is_platform_admin({"id": "user-1", "email": "andrewchri@gmail.com"}))

    def test_update_uses_service_role_and_returns_updated_lead(self):
        row = {"id": self.lead_id, "status": "contacted"}
        client = FakeClient(FakeResponse(200, [row], text="[{}]"))
        with patch.object(admin_partner_lead.httpx, "Client", return_value=client):
            result = admin_partner_lead._update_lead(self.lead_id, "contacted")
        self.assertEqual(result, row)
        self.assertEqual(client.request["method"], "PATCH")
        self.assertIn("hof_partner_leads?id=eq", client.request["url"])
        self.assertEqual(client.request["json"]["status"], "contacted")
        self.assertEqual(client.request["headers"]["Authorization"], "Bearer test-service-key")

    def test_missing_lead_is_not_reported_as_success(self):
        client = FakeClient(FakeResponse(200, [], text="[]"))
        with patch.object(admin_partner_lead.httpx, "Client", return_value=client):
            with self.assertRaisesRegex(ValueError, "not found"):
                admin_partner_lead._update_lead(self.lead_id, "contacted")


if __name__ == "__main__":
    unittest.main()
