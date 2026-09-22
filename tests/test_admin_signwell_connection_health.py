import importlib.util
from pathlib import Path
from unittest.mock import patch
import unittest

import httpx


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "admin_dashboard_signwell_health",
    ROOT / "api" / "admin-dashboard.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.payload = payload or {}

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, headers=None):
        self.calls.append({"url": url, "headers": headers or {}})
        if self.error:
            raise self.error
        return self.response


class AdminSignwellConnectionHealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_is_read_only_and_redacted(self):
        client = FakeClient(FakeResponse(200))
        with patch.object(MODULE, "SIGNWELL_ENABLED", True), \
             patch.object(MODULE, "SIGNWELL_API_KEY", "private-test-key"), \
             patch.object(MODULE.httpx, "AsyncClient", return_value=client):
            result = await MODULE._check_signwell_connection()

        self.assertTrue(result["connected"])
        self.assertNotIn("private-test-key", str(result))
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0]["url"], "https://www.signwell.com/api/v1/documents/?limit=1")
        self.assertEqual(client.calls[0]["headers"]["X-Api-Key"], "private-test-key")

    async def test_rejected_key_returns_safe_admin_guidance(self):
        client = FakeClient(FakeResponse(401))
        with patch.object(MODULE, "SIGNWELL_ENABLED", True), \
             patch.object(MODULE, "SIGNWELL_API_KEY", "expired-test-key"), \
             patch.object(MODULE.httpx, "AsyncClient", return_value=client):
            result = await MODULE._check_signwell_connection()

        self.assertFalse(result["connected"])
        self.assertIn("Update the production key", result["message"])
        self.assertNotIn("401", result["message"])
        self.assertNotIn("expired-test-key", str(result))

    async def test_network_failure_never_claims_a_document_was_sent(self):
        client = FakeClient(error=httpx.ConnectError("offline"))
        with patch.object(MODULE, "SIGNWELL_ENABLED", True), \
             patch.object(MODULE, "SIGNWELL_API_KEY", "private-test-key"), \
             patch.object(MODULE.httpx, "AsyncClient", return_value=client):
            result = await MODULE._check_signwell_connection()

        self.assertFalse(result["connected"])
        self.assertIn("No document or email was created", result["message"])

    async def test_missing_configuration_stops_before_provider_access(self):
        with patch.object(MODULE, "SIGNWELL_ENABLED", False), \
             patch.object(MODULE, "SIGNWELL_API_KEY", ""), \
             patch.object(MODULE.httpx, "AsyncClient") as client_factory:
            result = await MODULE._check_signwell_connection()

        self.assertFalse(result["connected"])
        client_factory.assert_not_called()

    def test_endpoint_is_below_the_platform_admin_boundary(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        admin_boundary = source.index('if not asyncio.run(_is_platform_admin(user)):')
        action = source.index('if data.get("action") == "check_signwell_connection":')
        combined_action = source.index('if data.get("action") == "check_delivery_connections":')
        self.assertLess(admin_boundary, action)
        self.assertLess(admin_boundary, combined_action)

    def test_admin_ui_explains_the_zero_send_check(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Delivery Connections", source)
        self.assertIn("check_delivery_connections", source)
        self.assertIn("does not create a document, consume a document allowance, or send an email", source)
        self.assertIn('aria-live="polite"', source)


class AdminResendConnectionHealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_lists_one_domain_without_sending(self):
        client = FakeClient(FakeResponse(200))
        with patch.object(MODULE, "RESEND_API_KEY", "private-resend-key"), \
             patch.object(MODULE.httpx, "AsyncClient", return_value=client):
            result = await MODULE._check_resend_connection()

        self.assertTrue(result["connected"])
        self.assertIn("No email was sent", result["message"])
        self.assertNotIn("private-resend-key", str(result))
        self.assertEqual(client.calls[0]["url"], "https://api.resend.com/domains?limit=1")
        self.assertEqual(client.calls[0]["headers"]["Authorization"], "Bearer private-resend-key")

    async def test_rejected_key_returns_safe_admin_guidance(self):
        client = FakeClient(FakeResponse(400, {"name": "validation_error"}))
        with patch.object(MODULE, "RESEND_API_KEY", "expired-resend-key"), \
             patch.object(MODULE.httpx, "AsyncClient", return_value=client):
            result = await MODULE._check_resend_connection()

        self.assertFalse(result["connected"])
        self.assertIn("Update the production key", result["message"])
        self.assertNotIn("400", result["message"])
        self.assertNotIn("expired-resend-key", str(result))

    async def test_sending_only_key_is_recognized_without_broadening_access(self):
        client = FakeClient(FakeResponse(403, {"name": "restricted_api_key"}))
        with patch.object(MODULE, "RESEND_API_KEY", "scoped-resend-key"), \
             patch.object(MODULE.httpx, "AsyncClient", return_value=client):
            result = await MODULE._check_resend_connection()

        self.assertTrue(result["connected"])
        self.assertIn("sending-only access", result["message"])
        self.assertIn("No email was sent", result["message"])

    async def test_network_failure_never_claims_an_email_was_sent(self):
        client = FakeClient(error=httpx.ConnectError("offline"))
        with patch.object(MODULE, "RESEND_API_KEY", "private-resend-key"), \
             patch.object(MODULE.httpx, "AsyncClient", return_value=client):
            result = await MODULE._check_resend_connection()

        self.assertFalse(result["connected"])
        self.assertIn("No email was sent", result["message"])

    async def test_missing_configuration_stops_before_provider_access(self):
        with patch.object(MODULE, "RESEND_API_KEY", ""), \
             patch.object(MODULE.httpx, "AsyncClient") as client_factory:
            result = await MODULE._check_resend_connection()

        self.assertFalse(result["connected"])
        client_factory.assert_not_called()

    async def test_combined_check_runs_both_independent_services(self):
        with patch.object(MODULE, "_check_signwell_connection", return_value={"connected": True}), \
             patch.object(MODULE, "_check_resend_connection", return_value={"connected": True}):
            result = await MODULE._check_delivery_connections()

        self.assertEqual(set(result), {"signwell", "resend"})
        self.assertTrue(result["signwell"]["connected"])
        self.assertTrue(result["resend"]["connected"])


if __name__ == "__main__":
    unittest.main()
