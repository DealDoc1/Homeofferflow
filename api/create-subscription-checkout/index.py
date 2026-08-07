import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler

import httpx

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
AGENT_MONTHLY_PRICE_ID = os.environ.get("STRIPE_AGENT_MONTHLY_PRICE_ID", "")
AGENT_ANNUAL_PRICE_ID = os.environ.get("STRIPE_AGENT_ANNUAL_PRICE_ID", "")
INVESTOR_MONTHLY_PRICE_ID = os.environ.get("STRIPE_INVESTOR_MONTHLY_PRICE_ID", "")
INVESTOR_ANNUAL_PRICE_ID = os.environ.get("STRIPE_INVESTOR_ANNUAL_PRICE_ID", "")


def build_stripe_checkout_form(body, origin):
    """Build a Stripe Checkout form without making a network request.

    Keeping this pure makes the trial/coupon contract directly testable and
    prevents the dedicated brokerage launch from accidentally sharing beta
    coupon behavior.
    """
    plan = (body.get("plan") or "agent").strip().lower()
    billing = (body.get("billing") or "monthly").strip().lower()
    email = (body.get("email") or "").strip()
    role = (body.get("role") or plan).strip().lower()
    user_id = (body.get("userId") or body.get("user_id") or "").strip()
    launch = (body.get("launch") or "").strip().lower()
    is_ondemand_launch = launch == "ondemand"

    if plan not in ["agent", "investor"]:
        raise ValueError("Invalid plan. Use agent or investor.")
    if billing not in ["monthly", "annual"]:
        raise ValueError("Invalid billing. Use monthly or annual.")
    if is_ondemand_launch and (plan != "agent" or billing != "monthly"):
        raise ValueError("The OnDemand launch uses the monthly Agent plan.")
    if not email or "@" not in email:
        raise ValueError("Valid email is required.")

    price_key = f"{plan}_{billing}"
    price_map = {
        "agent_monthly": AGENT_MONTHLY_PRICE_ID,
        "agent_annual": AGENT_ANNUAL_PRICE_ID,
        "investor_monthly": INVESTOR_MONTHLY_PRICE_ID,
        "investor_annual": INVESTOR_ANNUAL_PRICE_ID,
    }
    price_id = price_map.get(price_key)
    if not price_id:
        raise ValueError(f"Missing Stripe price env var for {price_key}")

    success_url = f"{origin}/?subscription=success&plan={urllib.parse.quote(plan)}&billing={urllib.parse.quote(billing)}&session_id={{CHECKOUT_SESSION_ID}}"
    form = {
        "mode": "subscription",
        "customer_email": email,
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "allow_promotion_codes": "false" if is_ondemand_launch else "true",
        "success_url": success_url,
        "cancel_url": f"{origin}/?subscription=cancelled",
        "metadata[source]": "homeofferflow",
        "metadata[plan]": plan,
        "metadata[billing]": billing,
        "metadata[role]": role,
        "metadata[user_id]": user_id,
        "metadata[email]": email,
        "metadata[launch]": launch,
        "subscription_data[metadata][source]": "homeofferflow",
        "subscription_data[metadata][plan]": plan,
        "subscription_data[metadata][billing]": billing,
        "subscription_data[metadata][role]": role,
        "subscription_data[metadata][user_id]": user_id,
        "subscription_data[metadata][email]": email,
        "subscription_data[metadata][launch]": launch,
    }
    if is_ondemand_launch:
        form["payment_method_collection"] = "always"
        form["subscription_data[trial_period_days]"] = "60"
    return form


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._json(200, {"ok": True})

    def do_POST(self):
        try:
            if not STRIPE_SECRET_KEY:
                self._json(500, {"error": "Missing STRIPE_SECRET_KEY"})
                return

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            body = json.loads(raw or "{}")

            origin = self.headers.get("origin") or "https://www.homeofferflow.com"
            try:
                form = build_stripe_checkout_form(body, origin)
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
                return

            with httpx.Client(timeout=20) as client:
                r = client.post(
                    "https://api.stripe.com/v1/checkout/sessions",
                    data=form,
                    headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"},
                )

            try:
                data = r.json()
            except Exception:
                data = {"raw": r.text}

            if r.status_code >= 400:
                message = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else None
                self._json(r.status_code, {"error": message or "Stripe checkout session failed.", "details": data})
                return

            self._json(200, {"url": data.get("url"), "id": data.get("id")})

        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
