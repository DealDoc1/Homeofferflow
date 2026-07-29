import importlib.util
import io
import json
import os
import asyncio
import unittest
from pathlib import Path
from unittest.mock import patch


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
        return Response(200, [{"status": "suspended"}])


class OnDemandCheckoutTests(unittest.TestCase):
    def setUp(self):
        checkout.STRIPE_SECRET_KEY = "sk_test_example"
        checkout.AGENT_MONTHLY_PRICE_ID = "price_existing_agent_monthly"
        StripeClient.last_request = None

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
        request._has_current_subscription = lambda _user_id: False
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
        self.assertNotIn("allow_promotion_codes", form)
        self.assertEqual(form["metadata[brokerage_slug]"], "ondemand")
        self.assertEqual(form["subscription_data[metadata][user_id]"], "user-1")
        self.assertIn("/ondemand?checkout=success", form["success_url"])

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
        request._has_current_subscription = lambda _user_id: True

        with patch.object(checkout.httpx, "Client", StripeClient):
            request.do_POST()

        self.assertEqual(captured["code"], 409)
        self.assertIsNone(StripeClient.last_request)

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

    def test_brokerage_roster_ui_discloses_membership_scope(self):
        marker = INDEX_HTML.index('id="hof-ondemand-brokerage-launch-v1"')
        final_script = INDEX_HTML[marker:]
        self.assertIn("setBrokerageMemberStatus", final_script)
        self.assertIn("HomeOfferFlow subscription or delete their offers", final_script)
        self.assertIn("HomeOfferFlow billing or delete their offers", final_script)

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
            "buyer-side offer packet",
            "not yet a complete transaction-form library",
            "buyer representation agreements",
            "listing agreements",
            "seller disclosure notices",
            "brokerage-approved workflow",
        ):
            self.assertIn(text.lower(), LAUNCH_HTML.lower())

    def test_launch_requires_authenticated_checkout_and_terms_confirmation(self):
        self.assertIn('"Authorization": `Bearer ${state.session.access_token}`', LAUNCH_HTML)
        self.assertIn('id="terms" type="checkbox"', LAUNCH_HTML)
        self.assertIn('emailRedirectTo: `${window.location.origin}/ondemand`', LAUNCH_HTML)

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
