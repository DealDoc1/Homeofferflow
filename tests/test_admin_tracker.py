import importlib.util
import os
import unittest
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py"
SEAT_CAP_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "supabase"
    / "homeofferflow_enforce_brokerage_agent_seat_caps.sql"
)
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

    def test_brokerage_agent_seat_cap_accepts_positive_integer_or_uncapped(self):
        self.assertEqual(admin_dashboard._brokerage_agent_seat_cap({"user_cap": 300}), 300)
        self.assertEqual(admin_dashboard._brokerage_agent_seat_cap({"user_cap": "12"}), 12)
        self.assertIsNone(admin_dashboard._brokerage_agent_seat_cap({"user_cap": None}))
        self.assertIsNone(admin_dashboard._brokerage_agent_seat_cap({}))

    def test_brokerage_agent_seat_cap_rejects_invalid_limits(self):
        with self.assertRaisesRegex(RuntimeError, "invalid agent-seat limit"):
            admin_dashboard._brokerage_agent_seat_cap({"user_cap": "many"})
        with self.assertRaisesRegex(RuntimeError, "invalid agent-seat limit"):
            admin_dashboard._brokerage_agent_seat_cap({"user_cap": -1})

    async def test_brokerage_agent_seat_check_counts_pending_invites_when_creating_new_invites(self):
        brokerage = {"id": "brokerage-123", "user_cap": 2}
        with patch.object(
            admin_dashboard,
            "_get",
            new=AsyncMock(side_effect=[[{"id": "member-1"}], [{"id": "invite-1"}]]),
        ):
            with self.assertRaisesRegex(ValueError, "2-agent seat limit"):
                await admin_dashboard._require_available_agent_seat(brokerage, include_pending=True)

    async def test_brokerage_agent_seat_check_allows_pending_invitee_to_accept_last_open_seat(self):
        brokerage = {"id": "brokerage-123", "user_cap": 2}
        with patch.object(
            admin_dashboard,
            "_get",
            new=AsyncMock(side_effect=[[{"id": "member-1"}], [{"id": "invite-1"}]]),
        ):
            await admin_dashboard._require_available_agent_seat(brokerage, include_pending=False)

    def test_database_trigger_is_the_concurrency_safe_agent_seat_guard(self):
        migration = SEAT_CAP_MIGRATION.read_text(encoding="utf-8")
        self.assertIn("for update", migration)
        self.assertIn("hof_brokerage_invites_enforce_agent_seat_cap", migration)
        self.assertIn("hof_brokerage_members_enforce_agent_seat_cap", migration)
        self.assertIn("active_agents + pending_invites >= cap", migration)

    async def test_brokerage_dashboard_returns_operational_counts_not_offer_or_listing_details(self):
        context = {
            "brokerage": {"id": "brokerage-123", "user_cap": 300, "name": "Example Realty"}
        }
        members = [{"user_id": "agent-123", "email": "agent@example.com", "role": "agent", "status": "active"}]
        agent_profiles = [{"user_id": "agent-123", "agent_name": "Agent Example", "agent_email": "agent@example.com", "license_number": "123"}]
        subscriptions = [{"user_id": "agent-123", "status": "trialing", "plan": "agent_starter_monthly", "trial_ends_at": "2026-09-01", "current_period_end": None}]
        # These sensitive keys simulate an upstream mistake. The dashboard
        # payload must ignore them rather than forwarding them to a broker.
        offers = [{
            "user_id": "agent-123", "status": "sent", "signwell_status": "awaiting_signature",
            "created_at": "2026-07-29T00:00:00Z", "updated_at": "2026-07-29T00:00:00Z",
            "buyer_name": "Private Buyer", "property_address": "123 Private Lane",
            "offer_terms": {"price": 500000}, "document_contents": "private",
        }]
        listing_workspaces = [{"listing_kind": "sale", "status": "intake", "seller_names": ["Private Seller"], "property_address": "456 Private Road"}]

        with patch.object(admin_dashboard, "_get", new=AsyncMock(return_value=members)), patch.object(
            admin_dashboard,
            "_get_optional",
            new=AsyncMock(side_effect=[[], [], listing_workspaces, agent_profiles, subscriptions, offers]),
        ):
            payload = await admin_dashboard._brokerage_dashboard_payload(context)

        agent = payload["agents"][0]
        self.assertEqual(agent["activity"]["offerCount"], 1)
        self.assertEqual(agent["engagement"], "active")
        self.assertEqual(agent["nextAction"], "Keep building client offers")
        self.assertEqual(payload["metrics"]["agentsNeedingActivation"], 0)
        self.assertEqual(payload["metrics"]["trialsEndingSoon"], 0)
        self.assertEqual(payload["listingWorkspaceSummary"], [{"listingKind": "sale", "status": "intake", "workspaceCount": 1}])
        self.assertEqual(len(payload["sourceReadiness"]), 8)
        self.assertEqual(payload["privacy"], {
            "buyerDetailsIncluded": False,
            "propertyDetailsIncluded": False,
            "offerTermsIncluded": False,
            "documentContentsIncluded": False,
        })
        serialized = str(payload)
        for sensitive_value in ("Private Buyer", "123 Private Lane", "500000", "private", "Private Seller", "456 Private Road"):
            self.assertNotIn(sensitive_value, serialized)

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

    def test_seller_lead_update_requires_uuid_and_allowlisted_status(self):
        lead_id = "e35eace9-2760-4b11-a01a-07ee65f2744e"
        self.assertEqual(
            admin_dashboard._parse_seller_lead_update({"seller_lead_id": lead_id, "status": "QUALIFIED"}),
            (lead_id, "qualified"),
        )
        with self.assertRaisesRegex(ValueError, "seller lead ID"):
            admin_dashboard._parse_seller_lead_update({"seller_lead_id": "not-a-uuid", "status": "qualified"})
        with self.assertRaisesRegex(ValueError, "valid seller lead status"):
            admin_dashboard._parse_seller_lead_update({"seller_lead_id": lead_id, "status": "deleted"})

    async def test_seller_lead_update_returns_saved_row(self):
        lead_id = "e35eace9-2760-4b11-a01a-07ee65f2744e"
        response = FakeResponse(200, [{"id": lead_id, "status": "contacted"}])
        with patch.object(admin_dashboard.httpx, "AsyncClient", return_value=FakeClient(response)):
            row = await admin_dashboard._update_seller_lead(lead_id, "contacted")
        self.assertEqual(row, {"id": lead_id, "status": "contacted"})

    async def test_partner_lead_update_does_not_succeed_when_lead_is_missing(self):
        response = FakeResponse(200, [])
        with patch.object(admin_dashboard.httpx, "AsyncClient", return_value=FakeClient(response)):
            with self.assertRaisesRegex(ValueError, "not found"):
                await admin_dashboard._update_partner_lead("e35eace9-2760-4b11-a01a-07ee65f2744e", "contacted")

    async def test_platform_partner_placement_is_validated_and_not_brokerage_owned(self):
        payload = admin_dashboard._parse_partner_placement({
            "partner_lead_id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "agreement_confirmed": True,
            "placement_tier": "premier",
            "monthly_fee": "399",
        })
        self.assertEqual(payload["source_lead_id"], "e35eace9-2760-4b11-a01a-07ee65f2744e")
        self.assertEqual(payload["placement_tier"], "premier")
        self.assertEqual(payload["monthly_fee"], 399.0)
        with self.assertRaisesRegex(ValueError, "agreement"):
            admin_dashboard._parse_partner_placement({
                "partner_lead_id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
                "placement_tier": "founding",
            })

    async def test_platform_partner_placement_returns_saved_row(self):
        response = FakeResponse(201, [{"id": "placement-1", "brokerage_id": None, "partner_name": "North Texas Movers"}])
        payload = {
            "source_lead_id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "placement_tier": "founding",
            "monthly_fee": 149.0,
        }
        lead = {
            "id": payload["source_lead_id"],
            "company_name": "North Texas Movers",
            "contact_name": "Partner Contact",
            "contact_email": "partner@example.com",
            "contact_phone": "2145550100",
            "website_url": "https://example.com",
            "partner_type": "moving_storage",
            "market_area": "DFW",
            "status": "qualified",
            "payment_status": "paid",
            "onboarding_status": "ready",
        }
        with patch.object(admin_dashboard, "_get", new=AsyncMock(side_effect=[[lead], []])), \
             patch.object(admin_dashboard.httpx, "AsyncClient", return_value=FakeClient(response)):
            row = await admin_dashboard._create_platform_partner_placement(payload)
        self.assertEqual(row["id"], "placement-1")

    async def test_unpaid_partner_application_cannot_activate_public_placement(self):
        lead = {
            "id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "company_name": "North Texas Movers",
            "partner_type": "moving_storage",
            "market_area": "DFW",
            "payment_status": "checkout_started",
            "status": "qualified",
        }
        with patch.object(admin_dashboard, "_get", new=AsyncMock(return_value=[lead])):
            with self.assertRaisesRegex(PermissionError, "paid partner application"):
                await admin_dashboard._create_platform_partner_placement({
                    "source_lead_id": lead["id"],
                    "placement_tier": "founding",
                    "monthly_fee": 149.0,
                })


if __name__ == "__main__":
    unittest.main()
