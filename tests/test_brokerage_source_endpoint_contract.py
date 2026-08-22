import asyncio
import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("brokerage_source_endpoint", ROOT / "api" / "admin-dashboard.py")
admin = importlib.util.module_from_spec(SPEC)
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-role-test")
SPEC.loader.exec_module(admin)


class BrokerageSourceEndpointContractTests(unittest.TestCase):
    def test_agent_payload_is_platform_wide_and_sanitized(self):
        captured = {}

        async def optional(path):
            captured["path"] = path
            return [{
                "id": "source-1",
                "form_code": "TXR-1507",
                "source_revision": "06-15-26",
                "status": "approved",
                "authorization_attested": True,
                "updated_at": "2026-07-31T00:00:00Z",
            }]

        with patch.object(admin, "_get_optional", optional):
            payload = asyncio.run(admin._brokerage_form_sources_payload({"id": "agent-1"}, approved_only=True))

        self.assertIn("status=eq.approved", captured["path"])
        self.assertIn("authorization_attested=is.true", captured["path"])
        self.assertNotIn("brokerage_id=eq.", captured["path"])
        self.assertEqual(payload["sources"][0]["form_code"], "TXR-1507")
        self.assertNotIn("storage_path", payload["sources"][0])
        self.assertNotIn("source_sha256", payload["sources"][0])

    def test_broker_admin_payload_is_scoped_and_does_not_expose_storage_path(self):
        captured = {}

        async def context(_user):
            return {"brokerage": {"id": "brokerage-1"}}

        async def optional(path):
            captured["path"] = path
            return [{
                "id": "source-1",
                "form_code": "TXR-1501",
                "source_revision": "06-15-26",
                "status": "approved",
                "original_filename": "TXR1501.pdf",
                "source_sha256": "a" * 64,
                "updated_at": "2026-07-31T00:00:00Z",
            }]

        with patch.object(admin, "_brokerage_admin_context", context), patch.object(admin, "_get_optional", optional):
            payload = asyncio.run(admin._brokerage_form_sources_payload({"id": "broker-1"}))

        self.assertIn("brokerage_id=eq.brokerage-1", captured["path"])
        self.assertIn("status=neq.retired", captured["path"])
        self.assertEqual(payload["sources"][0]["original_filename"], "TXR1501.pdf")
        self.assertNotIn("storage_path", payload["sources"][0])


if __name__ == "__main__":
    unittest.main()
