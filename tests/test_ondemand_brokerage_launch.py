import importlib.util
import io
import json
import os
import asyncio
import subprocess
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_PATH = ROOT / "api" / "create-subscription-checkout" / "index.py"
WEBHOOK_PATH = ROOT / "api" / "stripe-webhook" / "index.py"
ADMIN_PATH = ROOT / "api" / "admin-dashboard.py"
LAUNCH_HTML = (ROOT / "ondemand.html").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "index.html").read_text(encoding="utf-8")
VERCEL = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
MIGRATION = (ROOT / "supabase" / "homeofferflow_ondemand_brokerage_launch.sql").read_text(encoding="utf-8")
HARDENING = (ROOT / "supabase" / "homeofferflow_brokerage_security_hardening.sql").read_text(encoding="utf-8")
BROKER_SEED = (ROOT / "supabase" / "homeofferflow_ondemand_broker_seed.sql").read_text(encoding="utf-8")
INVITE_MIGRATION = (ROOT / "supabase" / "homeofferflow_brokerage_invites.sql").read_text(encoding="utf-8")
INVITE_DENY_MIGRATION = (ROOT / "supabase" / "homeofferflow_brokerage_invites_rls_deny.sql").read_text(encoding="utf-8")
BRANDING_MIGRATION = (ROOT / "supabase" / "homeofferflow_brokerage_branding_storage.sql").read_text(encoding="utf-8")

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_example")
os.environ.setdefault("STRIPE_AGENT_MONTHLY_PRICE_ID", "price_existing_agent_monthly")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checkout = load_module("ondemand_subscription_checkout", CHECKOUT_PATH)
webhook = load_module("ondemand_subscription_webhook", WEBHOOK_PATH)
admin = load_module("ondemand_admin_dashboard", ADMIN_PATH)


class Response:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


class StripeClient:
    last_request = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, **kwargs):
        StripeClient.last_request = (url, kwargs)
        return Response(200, {"id": "cs_test_ondemand", "url": "https://checkout.stripe.test/session"})


class MembershipClient:
    requests = []
    existing = [{"id": "member-1", "role": "broker_admin"}]

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, **kwargs):
        self.requests.append(("get", url, kwargs))
        return Response(200, self.existing)

    def patch(self, url, **kwargs):
        self.requests.append(("patch", url, kwargs))
        return Response(204, {}, "")

    def post(self, url, **kwargs):
        self.requests.append(("post", url, kwargs))
        return Response(201, {}, "")


class BrokerageRosterClient:
    last_patch = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def patch(self, url, **kwargs):
        self.__class__.last_patch = (url, kwargs)
        payload = kwargs.get("json") or {}
        return Response(200, [{"status": "suspended", "team_name": payload.get("team_name")}])


class BrokerageInviteClient:
    requests = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, **kwargs):
        self.__class__.requests.append(("post", url, kwargs))
        if "hof_brokerage_invites" in url:
            return Response(201, [{
                "email": "agent@example.com",
                "invite_token": "a" * 32,
                "expires_at": "2030-01-15T12:00:00+00:00",
            }])
        return Response(201, [{"id": "created"}])

    async def patch(self, url, **kwargs):
        self.__class__.requests.append(("patch", url, kwargs))
        return Response(200, [{"id": "updated"}])


class BrokerageInviteEmailClient(BrokerageInviteClient):
    email_request = None

    async def post(self, url, **kwargs):
        if url == "https://api.resend.com/emails":
            self.__class__.email_request = (url, kwargs)
            return Response(200, {"id": "re_invite_123"}, "{\"id\":\"re_invite_123\"}")
        return await super().post(url, **kwargs)


class BrokerageBrandingClient:
    last_patch = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def patch(self, url, **kwargs):
        self.__class__.last_patch = (url, kwargs)
        return Response(200, [{
            "id": "22222222-2222-2222-2222-222222222222",
            "name": "OnDemand Realty",
            "dba_name": "OnDemand Realty",
            "brand_color": "#123456",
            "logo_url": "https://example.supabase.co/storage/v1/object/public/brokerage-branding/22222222-2222-2222-2222-222222222222/brand-logo.png",
        }])


class BrokerageDefaultsClient:
    last_request = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def patch(self, url, **kwargs):
        self.__class__.last_request = ("patch", url, kwargs)
        if "hof_brokerages" in url:
            return Response(200, [{
                "default_title_company": "Sample Title",
                "default_title_contact": "Taylor Escrow",
            }])
        return Response(200, [{
            "preferred_title_company": "Sample Title",
            "preferred_escrow_agent": "Taylor Escrow",
        }])

    async def post(self, url, **kwargs):
        self.__class__.last_request = ("post", url, kwargs)
        return Response(201, [{
            "preferred_title_company": "Sample Title",
            "preferred_escrow_agent": "Taylor Escrow",
        }])


class BrokerageTxrClient:
    last_patch = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def patch(self, url, **kwargs):
        self.__class__.last_patch = (url, kwargs)
        return Response(200, [{
            "txr_all_agents_authorized": True,
            "txr_authorization_attested_by": "11111111-1111-1111-1111-111111111111",
            "txr_authorization_attested_at": "2030-01-15T12:00:00+00:00",
        }])


class OnDemandCheckoutTests(unittest.TestCase):
    def setUp(self):
        checkout.STRIPE_SECRET_KEY = "sk_test_example"
        checkout.AGENT_MONTHLY_PRICE_ID = "price_existing_agent_monthly"
        StripeClient.last_request = None

    def test_public_ondemand_launch_metadata_exposes_only_safe_trial_contract(self):
        request = checkout.handler.__new__(checkout.handler)
        request.path = "/api/create-subscription-checkout?launch=ondemand"
        captured = {}
        request._json = lambda code, data: captured.update(code=code, data=data)
        request._get_brokerage = lambda _slug: {
            "id": "brokerage-1",
            "name": "OnDemand Realty",
            "dba_name": "OnDemand Realty",
            "slug": "ondemand",
            "logo_url": None,
            "brand_color": "#2563eb",
            "website_url": None,
            "plan_name": "OnDemand Agent Launch",
            "internal_notes": "must not be exposed",
        }

        request.do_GET()

        self.assertEqual(captured["code"], 200)
        self.assertEqual(captured["data"]["launch"], "ondemand")
        self.assertEqual(captured["data"]["trialDays"], 60)
        self.assertEqual(captured["data"]["monthlyPrice"], 29)
        self.assertEqual(captured["data"]["brokerage"]["name"], "OnDemand Realty")
        self.assertNotIn("internal_notes", captured["data"]["brokerage"])

    def test_ondemand_checkout_uses_native_card_required_trial_and_existing_price(self):
        body = json.dumps({"launch": "ondemand", "plan": "investor", "billing": "annual"}).encode()
        request = checkout.handler.__new__(checkout.handler)
        request.headers = {
            "Content-Length": str(len(body)),
            "origin": "https://preview-homeofferflow.vercel.app",
            "authorization": "Bearer verified-token",
        }
        request.rfile = io.BytesIO(body)
        captured = {}
        request._json = lambda code, data: captured.update(code=code, data=data)
        request._require_supabase = lambda: None
        request._verified_user = lambda _header: {"id": "user-1", "email": "agent@ondemand.test"}
        request._get_brokerage = lambda _slug: {
            "id": "brokerage-1",
            "name": "OnDemand Realty",
            "dba_name": "OnDemand Realty",
            "slug": "ondemand",
        }
        request._has_active_brokerage_membership = lambda _user_id, _brokerage_id: True
        request._has_current_subscription = lambda _user_id: False
        request._has_current_legal_acceptance = lambda _user_id: True
        with patch.object(checkout.httpx, "Client", StripeClient):
            request.do_POST()

        self.assertEqual(captured["code"], 200)
        form = StripeClient.last_request[1]["data"]
        self.assertEqual(form["line_items[0][price]"], "price_existing_agent_monthly")
        self.assertEqual(form["payment_method_collection"], "always")
        self.assertEqual(form["payment_method_types[0]"], "card")
        self.assertEqual(form["subscription_data[trial_period_days]"], "60")
        self.assertEqual(
            form["subscription_data[trial_settings][end_behavior][missing_payment_method]"],
            "cancel",
        )
        self.assertFalse(
            any("cancel_at" in key for key in form),
            "The OnDemand trial must renew normally; cancellation is only the"
            " documented fallback when no payment method is available at trial end.",
        )
        self.assertNotIn("allow_promotion_codes", form)
        self.assertEqual(form["metadata[brokerage_slug]"], "ondemand")
        self.assertEqual(form["subscription_data[metadata][user_id]"], "user-1")
        self.assertIn("/ondemand?checkout=success", form["success_url"])

    def test_launch_acknowledgement_links_to_the_current_legal_package(self):
        for href in ("/terms.html", "/privacy.html", "/disclaimer.html", "/esign-consent.html"):
            with self.subTest(href=href):
                self.assertIn(href, LAUNCH_HTML)
        self.assertIn("my Agent plan will automatically", LAUNCH_HTML)
        self.assertIn("renew at <strong>$29/month</strong> unless I cancel", LAUNCH_HTML)

    def test_normal_subscription_checkout_still_supports_promotion_codes(self):
        source = CHECKOUT_PATH.read_text(encoding="utf-8")
        self.assertIn('form["allow_promotion_codes"] = "true"', source)
        self.assertIn('"agent_annual": AGENT_ANNUAL_PRICE_ID', source)
        self.assertIn('"investor_monthly": INVESTOR_MONTHLY_PRICE_ID', source)

    def test_ondemand_checkout_blocks_duplicate_current_subscription(self):
        body = json.dumps({"launch": "ondemand"}).encode()
        request = checkout.handler.__new__(checkout.handler)
        request.headers = {
            "Content-Length": str(len(body)),
            "origin": "https://preview-homeofferflow.vercel.app",
            "authorization": "Bearer verified-token",
        }
        request.rfile = io.BytesIO(body)
        captured = {}
        request._json = lambda code, data: captured.update(code=code, data=data)
        request._require_supabase = lambda: None
        request._verified_user = lambda _header: {
            "id": "user-1",
            "email": "agent@ondemand.test",
        }
        request._get_brokerage = lambda _slug: {
            "id": "brokerage-1",
            "name": "OnDemand Realty",
            "dba_name": "OnDemand Realty",
            "slug": "ondemand",
        }
        request._has_active_brokerage_membership = lambda _user_id, _brokerage_id: True
        request._has_current_subscription = lambda _user_id: True
        request._has_current_legal_acceptance = lambda _user_id: True

        with patch.object(checkout.httpx, "Client", StripeClient):
            request.do_POST()

        self.assertEqual(captured["code"], 409)
        self.assertIsNone(StripeClient.last_request)

    def test_ondemand_checkout_requires_active_invited_agent_membership_before_stripe(self):
        body = json.dumps({"launch": "ondemand"}).encode()
        request = checkout.handler.__new__(checkout.handler)
        request.headers = {
            "Content-Length": str(len(body)),
            "origin": "https://www.homeofferflow.com",
            "authorization": "Bearer verified-token",
        }
        request.rfile = io.BytesIO(body)
        captured = {}
        request._json = lambda code, data: captured.update(code=code, data=data)
        request._require_supabase = lambda: None
        request._verified_user = lambda _header: {"id": "user-1", "email": "agent@ondemand.test"}
        request._get_brokerage = lambda _slug: {"id": "brokerage-1", "slug": "ondemand"}
        request._has_active_brokerage_membership = lambda _user_id, _brokerage_id: False

        with patch.object(checkout.httpx, "Client", StripeClient):
            request.do_POST()

        self.assertEqual(captured["code"], 403)
        self.assertIn("active invited agents", captured["data"]["error"])
        self.assertIsNone(StripeClient.last_request)

    def test_ondemand_membership_check_is_scoped_to_active_agent_seat(self):
        request = checkout.handler.__new__(checkout.handler)
        MembershipClient.requests = []
        with patch.object(checkout.httpx, "Client", MembershipClient):
            self.assertTrue(request._has_active_brokerage_membership("user-1", "brokerage-1"))

        _, url, kwargs = MembershipClient.requests[0]
        self.assertTrue(url.endswith("/rest/v1/hof_brokerage_members"))
        self.assertEqual(kwargs["params"]["brokerage_id"], "eq.brokerage-1")
        self.assertEqual(kwargs["params"]["user_id"], "eq.user-1")
        self.assertEqual(kwargs["params"]["role"], "eq.agent")
        self.assertEqual(kwargs["params"]["status"], "eq.active")

    def test_ondemand_checkout_defers_brokerage_membership_until_stripe_confirms(self):
        source = CHECKOUT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("def _enroll_ondemand_user", source)
        self.assertNotIn("self._enroll_ondemand_user", source)

    def test_webhook_profile_association_preserves_existing_broker_role(self):
        class ProfileAndMembershipClient(MembershipClient):
            def get(self, url, **kwargs):
                self.requests.append(("get", url, kwargs))
                if url.endswith("/rest/v1/hof_profiles"):
                    return Response(200, [{"id": "user-1", "role": "brokerage_admin", "is_brokerage_admin": True}])
                return Response(200, [{"id": "member-1", "role": "broker_admin"}])

        member_handler = webhook.handler.__new__(webhook.handler)
        ProfileAndMembershipClient.requests = []
        with patch.object(member_handler, "_require_supabase"), patch.object(
            webhook.httpx, "Client", ProfileAndMembershipClient
        ):
            member_handler._activate_brokerage_membership(
                "user-1", "broker@ondemand.test", "brokerage-1"
            )

        profile_patch = next(
            request for request in ProfileAndMembershipClient.requests
            if request[0] == "patch" and "/rest/v1/hof_profiles" in request[1]
        )
        self.assertEqual(profile_patch[2]["json"]["brokerage_id"], "brokerage-1")
        self.assertNotIn("role", profile_patch[2]["json"])
        self.assertNotIn("is_brokerage_admin", profile_patch[2]["json"])

    def test_launch_origin_rejects_untrusted_domains(self):
        self.assertEqual(
            checkout._safe_origin("https://evil.example/ondemand"),
            "https://www.homeofferflow.com",
        )


class BrokerageAuthorizationTests(unittest.TestCase):
    def test_broker_can_suspend_an_agent_but_not_themself_or_a_broker(self):
        actor = {"id": "11111111-1111-1111-1111-111111111111", "email": "tyler@ondemanddfw.com"}
        context = {"brokerage": {"id": "22222222-2222-2222-2222-222222222222"}}

        async def broker_context(_actor):
            return context

        async def agent_members(_path):
            return [{
                "id": "membership-1",
                "user_id": "33333333-3333-3333-3333-333333333333",
                "role": "agent",
                "status": "active",
            }]

        with patch.object(admin, "_brokerage_admin_context", broker_context), \
             patch.object(admin, "_get", agent_members), \
             patch.object(admin.httpx, "AsyncClient", BrokerageRosterClient):
            result = asyncio.run(admin._set_brokerage_member_status(actor, {
                "user_id": "33333333-3333-3333-3333-333333333333",
                "membership_status": "suspended",
            }))
        self.assertTrue(result["changed"])
        self.assertEqual(result["membershipStatus"], "suspended")
        self.assertEqual(BrokerageRosterClient.last_patch[1]["json"]["status"], "suspended")

        with patch.object(admin, "_brokerage_admin_context", broker_context):
            with self.assertRaisesRegex(PermissionError, "cannot change your own"):
                asyncio.run(admin._set_brokerage_member_status(actor, {
                    "user_id": actor["id"], "membership_status": "suspended"
                }))

    def test_brokerage_membership_endpoint_only_changes_agent_membership(self):
        source = ADMIN_PATH.read_text(encoding="utf-8")
        self.assertIn('data.get("action") == "set_brokerage_member_status"', source)
        self.assertIn('ALLOWED_BROKERAGE_MEMBER_STATUSES = {"active", "suspended"}', source)
        start = source.index("async def _set_brokerage_member_status")
        end = source.index("def _parse_partner_lead_update", start)
        segment = source[start:end]
        self.assertIn("You cannot change your own brokerage-admin membership", segment)
        self.assertIn('member.get("role") or "agent") != "agent"', segment)
        self.assertNotIn("hof_subscriptions?", segment)
        self.assertNotIn("hof_offers?", segment)

    def test_broker_can_set_private_agent_team_without_changing_access_or_billing(self):
        actor = {"id": "11111111-1111-1111-1111-111111111111", "email": "tyler@ondemanddfw.com"}
        context = {"brokerage": {"id": "22222222-2222-2222-2222-222222222222"}}

        async def broker_context(_actor):
            return context

        async def agent_members(_path):
            return [{"id": "membership-1", "user_id": "33333333-3333-3333-3333-333333333333", "role": "agent", "status": "active"}]

        with patch.object(admin, "_brokerage_admin_context", broker_context), \
             patch.object(admin, "_get", agent_members), \
             patch.object(admin.httpx, "AsyncClient", BrokerageRosterClient):
            result = asyncio.run(admin._set_brokerage_member_team(actor, {
                "user_id": "33333333-3333-3333-3333-333333333333",
                "team_name": "  North   Dallas  ",
            }))
        self.assertEqual(result["teamName"], "North Dallas")
        saved = BrokerageRosterClient.last_patch[1]["json"]
        self.assertEqual(saved["team_name"], "North Dallas")
        self.assertEqual(set(saved) - {"updated_at"}, {"team_name"})

        with self.assertRaisesRegex(ValueError, "80 characters"):
            admin._normalized_brokerage_team_name("x" * 81)

    def test_brokerage_team_labels_are_private_organization_only(self):
        source = ADMIN_PATH.read_text(encoding="utf-8")
        self.assertIn('data.get("action") == "set_brokerage_member_team"', source)
        start = source.index("async def _set_brokerage_member_team")
        end = source.index("def _parse_partner_lead_update", start)
        segment = source[start:end]
        self.assertIn('members[0].get("role") or "agent") != "agent"', segment)
        self.assertNotIn("hof_subscriptions?", segment)
        self.assertNotIn("hof_offers?", segment)

        final_script = INDEX_HTML[INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"'):]
        self.assertIn("setBrokerageMemberTeam", final_script)
        self.assertIn("Private team labels organize this roster only", final_script)
        self.assertIn("Team activation cohorts", final_script)
        self.assertIn("teamCohorts", final_script)
        self.assertIn("Aggregate roster health only", final_script)
        self.assertIn("Download roster CSV", final_script)

    def test_brokerage_roster_ui_discloses_membership_scope(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("setBrokerageMemberStatus", final_script)
        self.assertIn("HomeOfferFlow subscription or delete their offers", final_script)
        self.assertIn("HomeOfferFlow billing or delete their offers", final_script)
        self.assertIn("Invitation email sent to", final_script)
        self.assertIn("Email delivery is not configured", final_script)

    def test_pending_invites_can_be_resent_without_exposing_tokens(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("root.resendBrokerageInvite", final_script)
        self.assertIn("onclick=\"resendBrokerageInvite", final_script)
        self.assertIn("invite.expires_at", final_script)
        self.assertNotIn("invite.invite_token", final_script)

    def test_broker_roster_has_privacy_limited_activation_follow_up_action(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("brokerageAgentFollowUpAction", final_script)
        self.assertIn(".replace(/'/g, '&#39;')", final_script)
        self.assertIn("brokerage-follow-up-action", final_script)
        self.assertIn("needs_activation", final_script)
        self.assertIn("Email agent", final_script)
        self.assertIn("mailto:${encodeURIComponent(email)}", final_script)

    def test_broker_roster_supports_privacy_safe_agent_filtering(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        for expected in (
            "filterBrokerageAgents",
            "brokerageAgentFilter",
            "data-brokerage-agent-row",
            "brokerageAgentFilterSummary",
            "Name, email, team, status, or next action",
        ):
            self.assertIn(expected, final_script)

    def test_broker_roster_exports_only_privacy_limited_operational_fields(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        for expected in (
            "exportBrokerageRoster",
            "homeofferflow-brokerage-roster.csv",
            "Download roster CSV",
            "agent.activity?.offerCount",
            "agent.activity?.signedCount",
        ):
            self.assertIn(expected, final_script)
        self.assertNotIn("property_address", final_script[final_script.index("root.exportBrokerageRoster"):final_script.index("root.renderBrokerageFoundationPanel")])

    def test_broker_can_create_an_agent_only_invite_link(self):
        actor = {"id": "11111111-1111-1111-1111-111111111111", "email": "tyler@ondemanddfw.com"}
        context = {"brokerage": {"id": "22222222-2222-2222-2222-222222222222"}}

        async def broker_context(_actor):
            return context

        async def no_existing_access(_path):
            return []

        BrokerageInviteClient.requests = []
        with patch.object(admin, "_brokerage_admin_context", broker_context), \
             patch.object(admin, "_get", no_existing_access), \
             patch.object(admin.httpx, "AsyncClient", BrokerageInviteClient):
            result = asyncio.run(admin._create_brokerage_invite(actor, {"email": "AGENT@example.com"}))

        self.assertFalse(result["reused"])
        self.assertEqual(result["email"], "agent@example.com")
        self.assertEqual(result["inviteUrl"], "https://www.homeofferflow.com/ondemand?invite=" + "a" * 32)
        invite_write = next(request for request in BrokerageInviteClient.requests if request[0] == "post")
        self.assertEqual(invite_write[2]["json"]["role"], "agent")
        self.assertEqual(invite_write[2]["json"]["status"], "pending")
        self.assertEqual(result["emailDelivery"]["status"], "not_configured")

    def test_brokerage_invite_sends_email_when_resend_is_configured(self):
        actor = {"id": "11111111-1111-1111-1111-111111111111", "email": "tyler@ondemanddfw.com"}
        context = {"brokerage": {"id": "22222222-2222-2222-2222-222222222222", "name": "OnDemand Realty"}}

        async def broker_context(_actor):
            return context

        async def no_existing_access(_path):
            return []

        BrokerageInviteEmailClient.requests = []
        BrokerageInviteEmailClient.email_request = None
        with patch.object(admin, "RESEND_API_KEY", "re_test_invite"), \
             patch.object(admin, "_brokerage_admin_context", broker_context), \
             patch.object(admin, "_get", no_existing_access), \
             patch.object(admin.httpx, "AsyncClient", BrokerageInviteEmailClient):
            result = asyncio.run(admin._create_brokerage_invite(actor, {"email": "agent@example.com"}))

        self.assertEqual(result["emailDelivery"], {"status": "sent", "emailId": "re_invite_123"})
        resend_payload = BrokerageInviteEmailClient.email_request[1]["json"]
        self.assertEqual(resend_payload["to"], ["agent@example.com"])
        self.assertIn("OnDemand Realty", resend_payload["subject"])
        self.assertIn(result["inviteUrl"], resend_payload["text"])

    def test_broker_can_revoke_only_a_pending_agent_invite_in_own_brokerage(self):
        actor = {"id": "11111111-1111-1111-1111-111111111111", "email": "tyler@ondemanddfw.com"}
        context = {"brokerage": {"id": "22222222-2222-2222-2222-222222222222"}}
        invite_id = "44444444-4444-4444-4444-444444444444"

        async def broker_context(_actor):
            return context

        async def pending_invite(_path):
            return [{"id": invite_id, "email": "agent@example.com", "status": "pending"}]

        BrokerageInviteClient.requests = []
        with patch.object(admin, "_brokerage_admin_context", broker_context), \
             patch.object(admin, "_get", pending_invite), \
             patch.object(admin.httpx, "AsyncClient", BrokerageInviteClient):
            result = asyncio.run(admin._revoke_brokerage_invite(actor, {"invite_id": invite_id}))

        self.assertEqual(result["inviteId"], invite_id)
        self.assertEqual(result["status"], "revoked")
        writes = [request for request in BrokerageInviteClient.requests if request[0] == "patch"]
        self.assertEqual(len(writes), 1)
        self.assertIn("status=eq.pending", writes[0][1])
        self.assertEqual(writes[0][2]["json"], {"status": "revoked"})

    def test_brokerage_invite_revoke_is_exposed_without_leaking_tokens(self):
        source = ADMIN_PATH.read_text(encoding="utf-8")
        self.assertIn('data.get("action") == "revoke_brokerage_invite"', source)
        dashboard_start = source.index("async def _brokerage_dashboard_payload")
        dashboard_end = source.index("def _normalized_invite_email", dashboard_start)
        dashboard_segment = source[dashboard_start:dashboard_end]
        self.assertNotIn("invite_token", dashboard_segment)
        final_script = INDEX_HTML[INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"'):]
        self.assertIn("revokeBrokerageInvite", final_script)
        self.assertIn("Revoke", final_script)

    def test_invite_acceptance_requires_the_invited_email_before_any_write(self):
        actor = {"id": "33333333-3333-3333-3333-333333333333", "email": "wrong@example.com"}

        async def invite_only(_path):
            return [{
                "id": "invite-1",
                "brokerage_id": "22222222-2222-2222-2222-222222222222",
                "email": "agent@example.com",
                "role": "agent",
                "status": "pending",
                "expires_at": "2030-01-15T12:00:00+00:00",
            }]

        BrokerageInviteClient.requests = []
        with patch.object(admin, "_get", invite_only), \
             patch.object(admin.httpx, "AsyncClient", BrokerageInviteClient):
            with self.assertRaisesRegex(PermissionError, "email address that received"):
                asyncio.run(admin._accept_brokerage_invite(actor, {"invite_token": "a" * 32}))
        self.assertEqual(BrokerageInviteClient.requests, [])

    def test_invite_acceptance_connects_agent_profile_membership_and_consumes_invite(self):
        actor = {"id": "33333333-3333-3333-3333-333333333333", "email": "agent@example.com"}

        async def lookup(path):
            if path.startswith("hof_brokerage_invites?"):
                return [{
                    "id": "invite-1",
                    "brokerage_id": "22222222-2222-2222-2222-222222222222",
                    "email": "agent@example.com",
                    "role": "agent",
                    "status": "pending",
                    "expires_at": "2030-01-15T12:00:00+00:00",
                }]
            if path.startswith("hof_profiles?"):
                return []
            if path.startswith("hof_brokerage_members?"):
                return []
            if path.startswith("hof_brokerages?"):
                return [{"id": "22222222-2222-2222-2222-222222222222", "user_cap": 10}]
            raise AssertionError(path)

        BrokerageInviteClient.requests = []
        with patch.object(admin, "_get", lookup), \
             patch.object(admin, "_require_available_agent_seat", new=AsyncMock()), \
             patch.object(admin.httpx, "AsyncClient", BrokerageInviteClient):
            result = asyncio.run(admin._accept_brokerage_invite(actor, {"invite_token": "a" * 32}))

        self.assertEqual(result, {
            "brokerageId": "22222222-2222-2222-2222-222222222222",
            "accepted": True,
        })
        writes = [request for request in BrokerageInviteClient.requests if request[0] in {"post", "patch"}]
        self.assertEqual(len(writes), 3)
        profile_write = next(request for request in writes if "hof_profiles" in request[1])
        membership_write = next(request for request in writes if "hof_brokerage_members" in request[1])
        invite_write = next(request for request in writes if "hof_brokerage_invites" in request[1])
        self.assertEqual(profile_write[2]["json"]["role"], "agent")
        self.assertEqual(profile_write[2]["json"]["brokerage_id"], "22222222-2222-2222-2222-222222222222")
        self.assertEqual(membership_write[2]["json"]["status"], "active")
        self.assertEqual(membership_write[2]["json"]["role"], "agent")
        self.assertEqual(invite_write[2]["json"]["status"], "accepted")

    def test_expired_invite_is_closed_without_connecting_the_agent(self):
        actor = {"id": "33333333-3333-3333-3333-333333333333", "email": "agent@example.com"}

        async def expired_invite(_path):
            return [{
                "id": "invite-expired",
                "brokerage_id": "22222222-2222-2222-2222-222222222222",
                "email": "agent@example.com",
                "role": "agent",
                "status": "pending",
                "expires_at": "2020-01-15T12:00:00+00:00",
            }]

        BrokerageInviteClient.requests = []
        with patch.object(admin, "_get", expired_invite), \
             patch.object(admin.httpx, "AsyncClient", BrokerageInviteClient):
            with self.assertRaisesRegex(ValueError, "invite has expired"):
                asyncio.run(admin._accept_brokerage_invite(actor, {"invite_token": "a" * 32}))

        self.assertEqual(len(BrokerageInviteClient.requests), 1)
        request = BrokerageInviteClient.requests[0]
        self.assertEqual(request[0], "patch")
        self.assertIn("hof_brokerage_invites", request[1])
        self.assertEqual(request[2]["json"], {"status": "expired"})

    def test_invite_endpoints_and_ui_keep_tokens_private_from_dashboard(self):
        source = ADMIN_PATH.read_text(encoding="utf-8")
        self.assertIn('data.get("action") == "create_brokerage_invite"', source)
        self.assertIn('data.get("action") == "accept_brokerage_invite"', source)
        dashboard_start = source.index("async def _brokerage_dashboard_payload")
        dashboard_end = source.index("def _normalized_invite_email", dashboard_start)
        dashboard_segment = source[dashboard_start:dashboard_end]
        self.assertIn("pendingInvites", dashboard_segment)
        self.assertNotIn("invite_token", dashboard_segment)
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("createBrokerageInvite", final_script)
        self.assertIn("Create invite link", final_script)
        self.assertIn("works only for the invited email", final_script)

    def test_brokerage_invite_ui_ignores_rapid_duplicate_starts(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("root.__hofBrokerageInviteInFlight", final_script)
        self.assertIn("if (root.__hofBrokerageInviteInFlight) return;", final_script)
        self.assertIn("root.__hofBrokerageInviteInFlight = true;", final_script)
        self.assertIn("root.__hofBrokerageInviteInFlight = false;", final_script)

    def test_broker_dashboard_exposes_source_readiness_without_private_source_details(self):
        source = ADMIN_PATH.read_text(encoding="utf-8")
        start = source.index("async def _brokerage_dashboard_payload")
        end = source.index("def _normalized_invite_email", start)
        segment = source[start:end]
        self.assertIn("sourceReadiness", segment)
        self.assertIn("storage paths, filenames, fingerprints, or source URLs", segment)
        self.assertIn('"readyForRestrictedDraft": brokerage_gate_ready', segment)
        self.assertIn("BROKERAGE_TXR_FORM_CODES", segment)

        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("Restricted form readiness", final_script)
        self.assertIn("Awaiting approved source", final_script)
        self.assertIn("must never omit the TXR/NAR gate", INDEX_HTML)

    def test_invite_migration_is_private_and_allows_one_pending_agent_invite(self):
        self.assertIn("alter column brokerage_id set not null", INVITE_MIGRATION)
        self.assertIn("check (role = 'agent')", INVITE_MIGRATION)
        self.assertIn("status in ('pending', 'accepted', 'expired', 'revoked')", INVITE_MIGRATION)
        self.assertIn("one_pending_email", INVITE_MIGRATION)
        self.assertIn("revoke all on table public.hof_brokerage_invites from anon, authenticated", INVITE_MIGRATION)
        self.assertIn("grant all on table public.hof_brokerage_invites to service_role", INVITE_MIGRATION)
        self.assertIn("create policy hof_brokerage_invites_deny_browser", INVITE_DENY_MIGRATION)
        self.assertIn("on public.hof_brokerage_invites", INVITE_DENY_MIGRATION)
        self.assertIn("to anon, authenticated", INVITE_DENY_MIGRATION)

    def test_broker_can_update_only_own_storage_backed_branding(self):
        actor = {"id": "11111111-1111-1111-1111-111111111111", "email": "tyler@ondemanddfw.com"}
        brokerage_id = "22222222-2222-2222-2222-222222222222"

        async def broker_context(_actor):
            return {"brokerage": {"id": brokerage_id}}

        BrokerageBrandingClient.last_patch = None
        payload = {
            "brand_color": "#123456",
            "logo_url": "https://example.supabase.co/storage/v1/object/public/brokerage-branding/"
                        + brokerage_id + "/brand-logo.png",
        }
        with patch.object(admin, "_brokerage_admin_context", broker_context), \
             patch.object(admin.httpx, "AsyncClient", BrokerageBrandingClient):
            result = asyncio.run(admin._update_brokerage_branding(actor, payload))

        self.assertEqual(result["brandColor"], "#123456")
        self.assertIn("id=eq." + brokerage_id, BrokerageBrandingClient.last_patch[0])
        self.assertEqual(BrokerageBrandingClient.last_patch[1]["json"]["brand_color"], "#123456")

    def test_brokerage_txr_authorization_requires_admin_attestation_and_writes_only_gate_fields(self):
        actor = {"id": "11111111-1111-1111-1111-111111111111", "email": "tyler@ondemanddfw.com"}
        brokerage_id = "22222222-2222-2222-2222-222222222222"

        async def broker_context(_actor):
            return {"brokerage": {"id": brokerage_id}}

        with patch.object(admin, "_brokerage_admin_context", broker_context):
            with self.assertRaisesRegex(ValueError, "administrator must attest"):
                asyncio.run(admin._update_brokerage_txr_authorization(actor, {
                    "status": "all_agents_authorized",
                    "attestation": False,
                }))

        BrokerageTxrClient.last_patch = None
        with patch.object(admin, "_brokerage_admin_context", broker_context), \
             patch.object(admin.httpx, "AsyncClient", BrokerageTxrClient):
            result = asyncio.run(admin._update_brokerage_txr_authorization(actor, {
                "status": "all_agents_authorized",
                "attestation": True,
            }))

        self.assertTrue(result["allAgentsAuthorized"])
        self.assertIn("id=eq." + brokerage_id, BrokerageTxrClient.last_patch[0])
        saved = BrokerageTxrClient.last_patch[1]["json"]
        self.assertEqual(saved["txr_all_agents_authorized"], True)
        self.assertEqual(saved["txr_authorization_attested_by"], actor["id"])
        self.assertEqual(set(saved), {
            "txr_all_agents_authorized",
            "txr_authorization_attested_by",
            "txr_authorization_attested_at",
            "updated_at",
        })

    def test_branding_rejects_arbitrary_logo_urls_and_invalid_colors(self):
        brokerage_id = "22222222-2222-2222-2222-222222222222"
        with self.assertRaisesRegex(ValueError, "#RRGGBB"):
            admin._parse_brokerage_branding_update({"brand_color": "blue"}, brokerage_id)
        with self.assertRaisesRegex(ValueError, "uploaded through"):
            admin._parse_brokerage_branding_update({
                "logo_url": "https://attacker.example/logo.png"
            }, brokerage_id)

    def test_branding_storage_migration_limits_writes_to_active_broker_admins(self):
        self.assertIn("'brokerage-branding'", BRANDING_MIGRATION)
        self.assertIn("public = true", BRANDING_MIGRATION)
        self.assertIn("file_size_limit = 2097152", BRANDING_MIGRATION)
        self.assertIn("array['image/png', 'image/jpeg', 'image/webp']", BRANDING_MIGRATION)
        self.assertIn("on storage.objects for all to authenticated", BRANDING_MIGRATION)
        self.assertIn("m.status = 'active'", BRANDING_MIGRATION)
        self.assertIn("m.role in ('broker_admin', 'owner')", BRANDING_MIGRATION)
        self.assertIn("p.brokerage_id::text = (storage.foldername(name))[1]", BRANDING_MIGRATION)
        self.assertIn("brand-logo.png", BRANDING_MIGRATION)

    def test_brokerage_branding_ui_uses_limited_direct_storage_upload(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("saveBrokerageBranding", final_script)
        self.assertIn("update_brokerage_branding", final_script)
        self.assertIn("brokerage-branding", final_script)
        self.assertIn("image/png', 'image/jpeg', 'image/webp'", final_script)
        self.assertIn("2 * 1024 * 1024", final_script)
        self.assertIn("Only active brokerage admins can update", final_script)

    def test_brokerage_ui_exposes_the_live_txr_authorization_gate(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("saveBrokerageTxrAuthorization", final_script)
        self.assertIn("update_brokerage_txr_authorization", final_script)
        self.assertIn("Texas REALTORS® / NAR form authorization", final_script)
        self.assertIn("This organization-level gate is not inferred from a license number", final_script)

    def test_broker_can_save_title_suggestions_but_not_transaction_terms(self):
        actor = {"id": "11111111-1111-1111-1111-111111111111", "email": "tyler@ondemanddfw.com"}
        brokerage_id = "22222222-2222-2222-2222-222222222222"

        async def broker_context(_actor):
            return {"brokerage": {"id": brokerage_id}}

        BrokerageDefaultsClient.last_request = None
        with patch.object(admin, "_brokerage_admin_context", broker_context), \
             patch.object(admin.httpx, "AsyncClient", BrokerageDefaultsClient):
            result = asyncio.run(admin._update_brokerage_shared_defaults(actor, {
                "default_title_company": "Sample Title",
                "default_title_contact": "Taylor Escrow",
                "default_option_fee": "9999",
            }))

        self.assertEqual(result["defaultTitleCompany"], "Sample Title")
        self.assertEqual(result["defaultTitleContact"], "Taylor Escrow")
        saved = BrokerageDefaultsClient.last_request[2]["json"]
        self.assertEqual(set(saved) - {"updated_at"}, {"default_title_company", "default_title_contact"})

    def test_agent_can_opt_in_to_connected_brokerage_title_defaults_only(self):
        actor = {"id": "33333333-3333-3333-3333-333333333333", "email": "agent@example.com"}
        brokerage_id = "22222222-2222-2222-2222-222222222222"

        async def lookup(path):
            if path.startswith("hof_profiles?"):
                return [{"id": actor["id"], "brokerage_id": brokerage_id}]
            if path.startswith("hof_brokerage_members?"):
                return [{"id": "membership-1"}]
            if path.startswith("hof_brokerages?"):
                return [{"default_title_company": "Sample Title", "default_title_contact": "Taylor Escrow"}]
            if path.startswith("hof_agent_profiles?"):
                return [{"user_id": actor["id"]}]
            raise AssertionError(path)

        BrokerageDefaultsClient.last_request = None
        with patch.object(admin, "_get", lookup), \
             patch.object(admin.httpx, "AsyncClient", BrokerageDefaultsClient):
            result = asyncio.run(admin._apply_brokerage_shared_defaults(actor))

        self.assertEqual(result["preferredTitleCompany"], "Sample Title")
        self.assertEqual(result["preferredEscrowAgent"], "Taylor Escrow")
        self.assertEqual(BrokerageDefaultsClient.last_request[0], "patch")
        self.assertNotIn("default_option_fee", BrokerageDefaultsClient.last_request[2]["json"])

    def test_brokerage_shared_defaults_and_seat_visibility_ui_are_explicit(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        for item in (
            "saveBrokerageSharedDefaults",
            "applyBrokerageSharedDefaults",
            "update_brokerage_shared_defaults",
            "apply_brokerage_shared_defaults",
            "Agents must choose to copy",
            "Agent seats",
            "agentSeatCap",
            "brokerage-seat-momentum",
            "Seat utilization",
            "Invite an agent",
        ):
            self.assertIn(item, final_script)

    def test_brokerage_title_defaults_reload_for_brokers_and_connected_agents(self):
        source = ADMIN_PATH.read_text(encoding="utf-8")
        context_start = source.index("async def _brokerage_admin_context")
        context_end = source.index("async def _brokerage_dashboard_payload", context_start)
        context = source[context_start:context_end]
        self.assertIn("default_title_company,default_title_contact", context)

        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn(
            "billing_status,default_title_company,default_title_contact",
            final_script,
        )

    def test_webhook_activation_preserves_existing_broker_role(self):
        member_handler = webhook.handler.__new__(webhook.handler)
        MembershipClient.requests = []
        MembershipClient.existing = [{"id": "member-1", "role": "broker_admin"}]
        with patch.object(member_handler, "_require_supabase"), patch.object(
            webhook.httpx, "Client", MembershipClient
        ):
            member_handler._activate_brokerage_membership(
                "user-1", "broker@ondemand.test", "brokerage-1"
            )
        writes = [
            request
            for request in MembershipClient.requests
            if request[0] in {"patch", "post"} and "/rest/v1/hof_brokerage_members" in request[1]
        ]
        self.assertEqual(writes[0][0], "patch")
        self.assertNotIn("role", writes[0][2]["json"])
        self.assertEqual(writes[0][2]["json"]["status"], "active")

    def test_broker_dashboard_query_excludes_sensitive_offer_fields(self):
        source = ADMIN_PATH.read_text(encoding="utf-8")
        start = source.index("async def _brokerage_dashboard_payload")
        end = source.index("def _parse_partner_lead_update", start)
        segment = source[start:end]
        for sensitive in ("buyer_name", "buyer_email", "property_address", "offer_price"):
            self.assertNotIn(sensitive, segment)
        self.assertIn(
            "&deleted_at=is.null&select=user_id,status,signwell_status,created_at,updated_at",
            segment,
        )
        for explicit_flag in (
            '"buyerDetailsIncluded": False',
            '"propertyDetailsIncluded": False',
            '"offerTermsIncluded": False',
            '"documentContentsIncluded": False',
        ):
            self.assertIn(explicit_flag, segment)

    def test_security_migration_removes_browser_role_and_subscription_writes(self):
        self.assertIn("grant update (email, team_name, updated_at)", HARDENING)
        self.assertNotIn("grant update (role", HARDENING)
        self.assertIn("grant select on table public.hof_subscriptions", HARDENING)
        subscription_grants = HARDENING[
            HARDENING.index("revoke all on table public.hof_subscriptions"):
            HARDENING.index("grant all on table public.hof_profiles to service_role")
        ]
        self.assertNotIn("grant insert", subscription_grants)
        self.assertNotIn("grant update", subscription_grants)
        self.assertIn("hof_brokerage_members_select_own", HARDENING)


class OnDemandLaunchPageTests(unittest.TestCase):
    def test_clean_route_rewrites_to_launch_page(self):
        self.assertIn(
            {"source": "/ondemand", "destination": "/ondemand.html"},
            VERCEL.get("rewrites", []),
        )

    def test_launch_discloses_price_trial_card_and_cancellation(self):
        for text in ("$0", "60 days", "$29/month", "card is required", "Cancel anytime"):
            self.assertIn(text.lower(), LAUNCH_HTML.lower())
        self.assertNotIn("coupon", LAUNCH_HTML.lower())
        self.assertNotIn("promo code", LAUNCH_HTML.lower())

    def test_launch_clearly_discloses_current_agent_form_scope(self):
        for text in (
            "purchase-offer packet",
            "seller temporary residential lease when seller post-closing possession applies",
            "not yet a complete transaction-form library",
            "buyer representation agreements",
            "listing agreements",
            "seller disclosure notices",
            "brokerage-approved workflow",
            "restricted Texas REALTORS",
            "individual agent attestation",
            "approved private source revision",
        ):
            self.assertIn(text.lower(), LAUNCH_HTML.lower())

    def test_launch_answers_trial_and_scope_questions_before_enrollment(self):
        for text in (
            'Enrollment questions',
            'Why is a card required if the first 60 days are free?',
            'Can I cancel before the trial renews?',
            'What can I use HomeOfferFlow for during this launch?',
            'prevents the first monthly charge',
        ):
            self.assertIn(text.lower(), LAUNCH_HTML.lower())

    def test_launch_requires_authenticated_checkout_and_terms_confirmation(self):
        self.assertIn('"Authorization": `Bearer ${state.session.access_token}`', LAUNCH_HTML)
        self.assertIn('id="terms" type="checkbox"', LAUNCH_HTML)
        self.assertIn('emailRedirectTo: `${window.location.origin}/ondemand${state.inviteToken', LAUNCH_HTML)
        self.assertIn('action: "accept_brokerage_invite"', LAUNCH_HTML)
        self.assertIn("Sign in with the email address that received this brokerage invite", ADMIN_PATH.read_text(encoding="utf-8"))

    def test_ondemand_inline_enrollment_script_parses_before_release(self):
        # The standalone enrollment page owns sign-in, invite acceptance, and
        # Stripe trial launch. Parse its actual inline script in the same Node
        # runtime used by the Vercel application so a syntax error cannot turn
        # the entire agent enrollment card inert at runtime.
        parser = """
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const match = html.match(/<script>\\s*\\(\\(\\) => \\{([\\s\\S]*?)\\n\\s*\\}\\)\\(\\);\\s*<\\/script>/);
if (!match) throw new Error('OnDemand inline enrollment script not found');
new Function(match[1]);
"""
        result = subprocess.run(
            ["node", "-e", parser, str(ROOT / "ondemand.html")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_browser_no_longer_creates_beta_subscription_or_sets_authorization_fields(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("status:'inactive'", final_script)
        self.assertNotIn("from('hof_subscriptions').insert", final_script)
        self.assertNotIn("role: role", final_script)
        self.assertNotIn("is_brokerage_admin:true", final_script.replace(" ", ""))

    def test_brokerage_seed_uses_confirmed_broker_identity(self):
        self.assertIn("'OnDemand Realty'", MIGRATION)
        self.assertIn("'ondemand'", MIGRATION)
        self.assertIn("'Tyler Demando'", MIGRATION)
        self.assertIn("'tyler@ondemanddfw.com'", MIGRATION)
        self.assertIn("'Tyler Demando'", BROKER_SEED)
        self.assertIn("'tyler@ondemanddfw.com'", BROKER_SEED)
        self.assertIn("'brokerage_admin'", BROKER_SEED)
        self.assertIn("'broker_admin'", BROKER_SEED)
        self.assertIn("'active'", BROKER_SEED)


if __name__ == "__main__":
    unittest.main()
