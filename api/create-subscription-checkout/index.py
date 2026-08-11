import json
import os
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

import httpx


STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
AGENT_MONTHLY_PRICE_ID = os.environ.get("STRIPE_AGENT_MONTHLY_PRICE_ID", "")
AGENT_ANNUAL_PRICE_ID = os.environ.get("STRIPE_AGENT_ANNUAL_PRICE_ID", "")
INVESTOR_MONTHLY_PRICE_ID = os.environ.get("STRIPE_INVESTOR_MONTHLY_PRICE_ID", "")
INVESTOR_ANNUAL_PRICE_ID = os.environ.get("STRIPE_INVESTOR_ANNUAL_PRICE_ID", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE")
    or os.environ.get("SUPABASE_SERVICE_KEY")
    or ""
)
ONDEMAND_BROKER_EMAIL = os.environ.get("ONDEMAND_BROKER_EMAIL", "").strip().lower()
ONDEMAND_SLUG = "ondemand"
ONDEMAND_TRIAL_DAYS = 60
LEGAL_POLICY_VERSION = "2026-07-30"
MAX_BODY_BYTES = 12_000


def _service_headers(prefer=None):
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _safe_origin(value):
    fallback = "https://www.homeofferflow.com"
    try:
        parsed = urllib.parse.urlparse((value or "").strip())
        hostname = (parsed.hostname or "").lower()
        allowed = (
            hostname in {"homeofferflow.com", "www.homeofferflow.com", "localhost", "127.0.0.1"}
            or hostname.endswith(".vercel.app")
        )
        if parsed.scheme not in {"http", "https"} or not allowed:
            return fallback
        port = f":{parsed.port}" if parsed.port else ""
        return f"{parsed.scheme}://{hostname}{port}"
    except Exception:
        return fallback


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._json(200, {"ok": True})

    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        launch = str((query.get("launch") or [""])[0]).strip().lower()
        if launch != ONDEMAND_SLUG:
            self._json(200, {"ok": True, "route": "create-subscription-checkout"})
            return
        try:
            brokerage = self._get_brokerage(ONDEMAND_SLUG)
            self._json(
                200,
                {
                    "ok": True,
                    "launch": ONDEMAND_SLUG,
                    "trialDays": ONDEMAND_TRIAL_DAYS,
                    "monthlyPrice": 29,
                    "brokerage": self._public_brokerage(brokerage),
                },
            )
        except Exception as exc:
            self._json(500, {"error": str(exc)[:300]})

    def do_POST(self):
        try:
            if not STRIPE_SECRET_KEY:
                self._json(500, {"error": "Missing STRIPE_SECRET_KEY"})
                return

            # Checkout must always be tied to the authenticated HomeOfferFlow
            # account. Never trust a user ID or email supplied in the browser
            # request body: those are customer-facing fields, not authority.
            self._require_supabase()
            verified_user = self._verified_user(self.headers.get("authorization", ""))
            if not verified_user:
                self._json(401, {"error": "Sign in before starting subscription checkout."})
                return

            length = int(self.headers.get("Content-Length", 0))
            if length <= 0 or length > MAX_BODY_BYTES:
                self._json(400, {"error": "Invalid request size."})
                return
            raw = self.rfile.read(length).decode("utf-8")
            body = json.loads(raw or "{}")

            launch = (body.get("launch") or "").strip().lower()
            is_ondemand = launch == ONDEMAND_SLUG
            plan = (body.get("plan") or "agent").strip().lower()
            billing = (body.get("billing") or "monthly").strip().lower()
            role = (body.get("role") or plan).strip().lower()
            email = verified_user["email"]
            user_id = verified_user["id"]
            brokerage = None

            if is_ondemand:
                plan = "agent"
                billing = "monthly"
                role = "agent"
                email = verified_user["email"]
                user_id = verified_user["id"]
                brokerage = self._get_brokerage(ONDEMAND_SLUG)
                # An invite link is a convenient way to activate this
                # membership, but the server must be the authorization
                # boundary. Without this check, a direct POST could start the
                # brokerage-only 60-day trial for any signed-in account.
                if not self._has_active_brokerage_membership(user_id, brokerage["id"]):
                    self._json(
                        403,
                        {
                            "error": (
                                "This OnDemand launch is available to active invited agents. "
                                "Use the invitation link from your broker, then sign in with "
                                "the invited email before checkout."
                            )
                        },
                    )
                    return

            if self._has_current_subscription(user_id):
                self._json(
                    409,
                    {
                        "error": (
                            "This account already has a subscription that can be recovered. "
                            "Open HomeOfferFlow billing instead of starting a duplicate plan."
                        )
                    },
                )
                return

            if plan not in ["agent", "investor"]:
                self._json(400, {"error": "Invalid plan. Use agent or investor."})
                return

            if billing not in ["monthly", "annual"]:
                self._json(400, {"error": "Invalid billing. Use monthly or annual."})
                return

            if not email or "@" not in email:
                self._json(400, {"error": "Valid email is required."})
                return

            # The browser prompt is useful UX, but it is not an authorization
            # boundary. Enforce the current versioned acceptance here too so a
            # direct request cannot start a recurring subscription without it.
            if not self._has_current_legal_acceptance(user_id):
                self._json(
                    403,
                    {
                        "error": (
                            "Accept the current Terms, Privacy Policy, Disclaimer, and "
                            "Electronic Communications and E-Sign Consent before checkout."
                        )
                    },
                )
                return

            price_key = f"{plan}_{billing}"
            price_map = {
                "agent_monthly": AGENT_MONTHLY_PRICE_ID,
                "agent_annual": AGENT_ANNUAL_PRICE_ID,
                "investor_monthly": INVESTOR_MONTHLY_PRICE_ID,
                "investor_annual": INVESTOR_ANNUAL_PRICE_ID,
            }
            price_id = price_map.get(price_key)

            if not price_id:
                self._json(500, {"error": f"Missing Stripe price env var for {price_key}"})
                return

            origin = _safe_origin(self.headers.get("origin") or self.headers.get("referer"))
            if is_ondemand:
                success_url = f"{origin}/ondemand?checkout=success&session_id={{CHECKOUT_SESSION_ID}}"
                cancel_url = f"{origin}/ondemand?checkout=cancelled"
            else:
                success_url = f"{origin}/?subscription=success&plan={urllib.parse.quote(plan)}&billing={urllib.parse.quote(billing)}&session_id={{CHECKOUT_SESSION_ID}}"
                cancel_url = f"{origin}/?subscription=cancelled"

            metadata = {
                "source": "homeofferflow_ondemand_launch" if is_ondemand else "homeofferflow",
                "plan": plan,
                "billing": billing,
                "role": role,
                "user_id": user_id,
                "email": email,
            }
            if brokerage:
                metadata.update(
                    {
                        "brokerage_id": str(brokerage["id"]),
                        "brokerage_slug": ONDEMAND_SLUG,
                        "launch_source": ONDEMAND_SLUG,
                        "trial_days": str(ONDEMAND_TRIAL_DAYS),
                    }
                )

            form = {
                "mode": "subscription",
                "customer_email": email,
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": "1",
                "success_url": success_url,
                "cancel_url": cancel_url,
            }
            for key, value in metadata.items():
                form[f"metadata[{key}]"] = value
                form[f"subscription_data[metadata][{key}]"] = value

            if is_ondemand:
                form.update(
                    {
                        "payment_method_collection": "always",
                        "payment_method_types[0]": "card",
                        "subscription_data[trial_period_days]": str(ONDEMAND_TRIAL_DAYS),
                        "subscription_data[trial_settings][end_behavior][missing_payment_method]": "cancel",
                    }
                )
            else:
                form["allow_promotion_codes"] = "true"

            with httpx.Client(timeout=20) as client:
                response = client.post(
                    "https://api.stripe.com/v1/checkout/sessions",
                    data=form,
                    headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"},
                )

            try:
                data = response.json()
            except Exception:
                data = {"raw": response.text}

            if response.status_code >= 400:
                message = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else None
                self._json(response.status_code, {"error": message or "Stripe checkout session failed.", "details": data})
                return

            self._json(
                200,
                {
                    "url": data.get("url"),
                    "id": data.get("id"),
                    "launch": launch or None,
                    "trialDays": ONDEMAND_TRIAL_DAYS if is_ondemand else 0,
                    "brokerage": self._public_brokerage(brokerage) if brokerage else None,
                },
            )

        except json.JSONDecodeError:
            self._json(400, {"error": "Invalid JSON."})
        except Exception as exc:
            self._json(500, {"error": str(exc)[:500]})

    def _verified_user(self, auth_header):
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return None
        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return None
        with httpx.Client(timeout=12) as client:
            response = client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {token}",
                },
            )
        if response.status_code != 200:
            return None
        payload = response.json()
        if not payload.get("id") or not payload.get("email"):
            return None
        return {
            "id": str(payload["id"]),
            "email": str(payload["email"]).strip().lower(),
        }

    def _get_brokerage(self, slug):
        self._require_supabase()
        with httpx.Client(timeout=12) as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/hof_brokerages",
                params={"slug": f"eq.{slug}", "is_active": "eq.true", "select": "*", "limit": "1"},
                headers=_service_headers(),
            )
        if response.status_code >= 300:
            raise RuntimeError("Could not load the OnDemand brokerage launch.")
        rows = response.json()
        if not rows:
            raise RuntimeError("OnDemand brokerage launch is not configured.")
        return rows[0]

    def _has_current_subscription(self, user_id):
        self._require_supabase()
        with httpx.Client(timeout=12) as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/hof_subscriptions",
                params={
                    "user_id": f"eq.{user_id}",
                    # A past-due or otherwise payable subscription belongs in
                    # Stripe's billing portal. Starting a second Checkout
                    # subscription here can create duplicate billing state.
                    # Canceled and expired subscriptions are deliberately not
                    # included so a former customer can choose a new plan.
                    "status": "in.(active,trialing,free_admin,past_due,incomplete,unpaid,paused)",
                    "select": "id",
                    "limit": "1",
                },
                headers=_service_headers(),
            )
        if response.status_code >= 300:
            raise RuntimeError("Could not verify the current subscription.")
        return bool(response.json())

    def _has_active_brokerage_membership(self, user_id, brokerage_id):
        self._require_supabase()
        with httpx.Client(timeout=12) as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/hof_brokerage_members",
                params={
                    "brokerage_id": f"eq.{brokerage_id}",
                    "user_id": f"eq.{user_id}",
                    "role": "eq.agent",
                    "status": "eq.active",
                    "select": "id",
                    "limit": "1",
                },
                headers=_service_headers(),
            )
        if response.status_code >= 300:
            raise RuntimeError("Could not verify the OnDemand brokerage membership.")
        return bool(response.json())

    def _has_current_legal_acceptance(self, user_id):
        self._require_supabase()
        with httpx.Client(timeout=12) as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/hof_legal_acceptances",
                params={
                    "user_id": f"eq.{user_id}",
                    "policy_version": f"eq.{LEGAL_POLICY_VERSION}",
                    "select": "id",
                    "limit": "1",
                },
                headers=_service_headers(),
            )
        if response.status_code >= 300:
            raise RuntimeError("Could not verify the current legal acceptance.")
        return bool(response.json())

    def _public_brokerage(self, brokerage):
        if not brokerage:
            return None
        return {
            "id": brokerage.get("id"),
            "name": brokerage.get("name"),
            "dbaName": brokerage.get("dba_name"),
            "slug": brokerage.get("slug"),
            "logoUrl": brokerage.get("logo_url"),
            "brandColor": brokerage.get("brand_color"),
            "websiteUrl": brokerage.get("website_url"),
            "planName": brokerage.get("plan_name"),
        }

    def _require_supabase(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Supabase brokerage enrollment is not configured.")

    def _json(self, code, data):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)
