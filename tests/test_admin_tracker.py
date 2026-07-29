import importlib.util
import os
import unittest
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py"
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
SPEC = importlib.util.spec_from_file_location("admin_dashboard", MODULE_PATH)
admin_dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(admin_dashboard)


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *_args, **_kwargs):
        return self.response

    async def patch(self, *_args, **_kwargs):
        return self.response

    async def post(self, *_args, **_kwargs):
        return self.response


class AdminTrackerSecurityTests(IsolatedAsyncioTestCase):
    async def test_missing_bearer_token_is_rejected_without_network_call(self):
        self.assertIsNone(await admin_dashboard._verified_user(""))
        self.assertIsNone(await admin_dashboard._verified_user("Basic no"))

    async def test_auth_user_endpoint_validates_session_and_returns_verified_identity(self):
        response = FakeResponse(200, {"id": "user-123", "email": "ADMIN@EXAMPLE.COM"})
        with patch.object(admin_dashboard.httpx, "AsyncClient", return_value=FakeClient(response)):
            user = await admin_dashboard._verified_user("Bearer signed-session-token")
        self.assertEqual(user, {"id": "user-123", "email": "admin@example.com"})

    async def test_invalid_session_is_rejected(self):
        response = FakeResponse(401, {"message": "invalid token"})
        with patch.object(admin_dashboard.httpx, "AsyncClient", return_value=FakeClient(response)):
            self.assertIsNone(await admin_dashboard._verified_user("Bearer invalid"))

    async def test_platform_admin_membership_is_checked_for_non_allowlisted_user(self):
        with patch.object(admin_dashboard, "_get", new=AsyncMock(return_value=[])) as get_rows:
            allowed = await admin_dashboard._is_platform_admin({"id": "user-456", "email": "agent@example.com"})
        self.assertFalse(allowed)
        get_rows.assert_awaited_once()

    async def test_verified_default_admin_email_is_allowed(self):
        with patch.object(admin_dashboard, "_get", new=AsyncMock()) as get_rows:
            allowed = await admin_dashboard._is_platform_admin({"id": "user-789", "email": "andrewchri@gmail.com"})
        self.assertTrue(allowed)
        get_rows.assert_not_awaited()

    async def test_default_platform_admins_remain_allowed_when_env_adds_operations_admins(self):
        with patch.object(admin_dashboard, "ADMIN_EMAILS", {"operations@example.com"}), \
             patch.object(admin_dashboard, "_get", new=AsyncMock()) as get_rows:
            allowed = await admin_dashboard._is_platform_admin({"id": "support-1", "email": "support@homeofferflow.com"})
        self.assertTrue(allowed)
        get_rows.assert_not_awaited()

    async def test_brokerage_dashboard_requires_active_broker_membership_even_if_profile_flag_is_stale(self):
        user = {"id": "user-123", "email": "former-broker@example.com"}
        profile = [{
            "id": "user-123",
            "brokerage_id": "brokerage-123",
            "is_brokerage_admin": True,
            "role": "brokerage_admin",
        }]

        with patch.object(admin_dashboard, "_get", new=AsyncMock(side_effect=[profile, []])) as get_rows:
            context = await admin_dashboard._brokerage_admin_context(user)

        self.assertIsNone(context)
        self.assertEqual(get_rows.await_count, 2)

    async def test_brokerage_dashboard_accepts_active_broker_membership(self):
        user = {"id": "user-123", "email": "broker@example.com"}
        profile = [{
            "id": "user-123",
            "brokerage_id": "brokerage-123",
            "is_brokerage_admin": False,
            "role": "agent",
        }]
        membership = [{"id": "membership-123"}]
        brokerage = [{"id": "brokerage-123", "name": "OnDemand Realty"}]

        with patch.object(admin_dashboard, "_get", new=AsyncMock(side_effect=[profile, membership, brokerage])):
            context = await admin_dashboard._brokerage_admin_context(user)

        self.assertEqual(context["brokerage"]["id"], "brokerage-123")

    async def test_optional_admin_dataset_fails_open_to_empty_list(self):
        with patch.object(admin_dashboard, "_get", new=AsyncMock(side_effect=RuntimeError("table missing"))):
            rows = await admin_dashboard._get_optional("hof_partner_leads?select=*")
        self.assertEqual(rows, [])

    async def test_partner_lead_update_requires_uuid_and_allowlisted_status(self):
        lead_id = "e35eace9-2760-4b11-a01a-07ee65f2744e"
        self.assertEqual(
            admin_dashboard._parse_partner_lead_update({"lead_id": lead_id, "status": "QUALIFIED"}),
            (lead_id, "qualified", None),
        )
        with self.assertRaisesRegex(ValueError, "lead ID"):
            admin_dashboard._parse_partner_lead_update({"lead_id": "not-a-uuid", "status": "qualified"})
        with self.assertRaisesRegex(ValueError, "valid partner lead status"):
            admin_dashboard._parse_partner_lead_update({"lead_id": lead_id, "status": "deleted"})
        with self.assertRaisesRegex(ValueError, "valid partner onboarding status"):
            admin_dashboard._parse_partner_lead_update({"lead_id": lead_id, "status": "qualified", "onboarding_status": "sent"})

    async def test_partner_lead_update_returns_saved_row(self):
        lead_id = "e35eace9-2760-4b11-a01a-07ee65f2744e"
        response = FakeResponse(200, [{"id": lead_id, "status": "contacted"}])
        with patch.object(admin_dashboard.httpx, "AsyncClient", return_value=FakeClient(response)):
            row = await admin_dashboard._update_partner_lead(lead_id, "contacted", "in_progress")
        self.assertEqual(row, {"id": lead_id, "status": "contacted"})

    async def test_partner_lead_update_does_not_succeed_when_lead_is_missing(self):
        response = FakeResponse(200, [])
        with patch.object(admin_dashboard.httpx, "AsyncClient", return_value=FakeClient(response)):
            with self.assertRaisesRegex(ValueError, "not found"):
                await admin_dashboard._update_partner_lead("e35eace9-2760-4b11-a01a-07ee65f2744e", "contacted")

    async def test_platform_partner_placement_is_validated_and_not_brokerage_owned(self):
        payload = admin_dashboard._parse_partner_placement({
            "partner_name": "North Texas Movers",
            "partner_type": "moving_storage",
            "market_area": "DFW",
            "placement_tier": "premier",
            "website_url": "https://example.com",
            "monthly_fee": "399",
        })
        self.assertIsNone(payload["brokerage_id"])
        self.assertEqual(payload["placement_tier"], "premier")
        self.assertEqual(payload["monthly_fee"], 399.0)
        with self.assertRaisesRegex(ValueError, "Website URL"):
            admin_dashboard._parse_partner_placement({
                "partner_name": "Bad URL Co",
                "partner_type": "moving_storage",
                "market_area": "DFW",
                "placement_tier": "founding",
                "website_url": "example.com",
            })

    async def test_platform_partner_placement_returns_saved_row(self):
        response = FakeResponse(201, [{"id": "placement-1", "brokerage_id": None, "partner_name": "North Texas Movers"}])
        payload = {
            "brokerage_id": None,
            "partner_name": "North Texas Movers",
            "partner_type": "moving_storage",
            "market_area": "DFW",
            "placement_tier": "founding",
            "website_url": "https://example.com",
            "logo_url": None,
            "monthly_fee": 149.0,
            "is_active": True,
        }
        with patch.object(admin_dashboard.httpx, "AsyncClient", return_value=FakeClient(response)):
            row = await admin_dashboard._create_platform_partner_placement(payload)
        self.assertEqual(row["id"], "placement-1")


if __name__ == "__main__":
    unittest.main()
