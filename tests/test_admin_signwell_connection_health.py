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
    def __init__(self, status_code):
        self.status_code = status_code


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
        self.assertLess(admin_boundary, action)

    def test_admin_ui_explains_the_zero_send_check(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Signature Delivery Connection", source)
        self.assertIn("check_signwell_connection", source)
        self.assertIn("does not create a document, consume a document allowance, or send an email", source)
        self.assertIn('aria-live="polite"', source)


if __name__ == "__main__":
    unittest.main()
