import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, patch
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("admin_dashboard", ROOT / "api" / "admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PlatformAdminBrokerageAttestationTests(unittest.TestCase):
    def test_platform_admin_can_target_an_active_brokerage(self):
        async def run():
            actor = {"id": "platform-user", "email": "andrewchri@gmail.com"}
            data = {
                "brokerage_id": "57f5c952-80af-4ba9-9f7f-ad99dcbc31c5",
                "status": "all_agents_authorized",
                "attestation": True,
            }
            with patch.object(MODULE, "_brokerage_admin_context", new=AsyncMock(return_value=None)),                  patch.object(MODULE, "_is_platform_admin", new=AsyncMock(return_value=True)),                  patch.object(MODULE, "_get", new=AsyncMock(return_value=[{"id": data["brokerage_id"]}])),                  patch.object(MODULE.httpx, "AsyncClient") as client_cls:
                response = AsyncMock()
                response.status_code = 200
                response.json = lambda: [{
                    "id": data["brokerage_id"],
                    "txr_all_agents_authorized": True,
                    "txr_authorization_attested_at": "2026-08-07T00:00:00+00:00",
                    "txr_authorization_attested_by": actor["id"],
                }]
                client = AsyncMock()
                client.__aenter__.return_value = client
                client.patch.return_value = response
                client_cls.return_value = client
                result = await MODULE._update_brokerage_txr_authorization(actor, data)
                self.assertTrue(result["allAgentsAuthorized"])
                self.assertEqual(client.patch.await_args.kwargs["json"]["txr_authorization_attested_by"], actor["id"])

        asyncio.run(run())

    def test_non_admin_cannot_target_another_brokerage(self):
        async def run():
            actor = {"id": "agent-user", "email": "agent@example.com"}
            data = {
                "brokerage_id": "57f5c952-80af-4ba9-9f7f-ad99dcbc31c5",
                "status": "all_agents_authorized",
                "attestation": True,
            }
            with patch.object(MODULE, "_brokerage_admin_context", new=AsyncMock(return_value=None)),                  patch.object(MODULE, "_is_platform_admin", new=AsyncMock(return_value=False)):
                with self.assertRaisesRegex(PermissionError, "Brokerage admin access"):
                    await MODULE._update_brokerage_txr_authorization(actor, data)

        asyncio.run(run())

    def test_broker_admin_stays_scoped_to_own_brokerage(self):
        async def run():
            actor = {"id": "broker-user", "email": "broker@example.com"}
            context = {"brokerage": {"id": "own-brokerage"}}
            data = {
                "brokerage_id": "different-brokerage",
                "status": "all_agents_authorized",
                "attestation": True,
            }
            with patch.object(MODULE, "_brokerage_admin_context", new=AsyncMock(return_value=context)),                  patch.object(MODULE, "_is_platform_admin", new=AsyncMock(return_value=False)),                  patch.object(MODULE.httpx, "AsyncClient") as client_cls:
                response = AsyncMock()
                response.status_code = 200
                response.json = lambda: [{
                    "id": "own-brokerage",
                    "txr_all_agents_authorized": True,
                    "txr_authorization_attested_at": "2026-08-07T00:00:00+00:00",
                    "txr_authorization_attested_by": actor["id"],
                }]
                client = AsyncMock()
                client.__aenter__.return_value = client
                client.patch.return_value = response
                client_cls.return_value = client
                await MODULE._update_brokerage_txr_authorization(actor, data)
                url = client.patch.await_args.args[0]
                self.assertIn("id=eq.own-brokerage", url)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
