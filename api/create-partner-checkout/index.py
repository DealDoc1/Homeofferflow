import json
import os
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler

import httpx


STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

PRICE_ENV_BY_TIER = {
    "founding_pilot": "STRIPE_FOUNDING_PARTNER_LISTING_PRICE_ID",
    "monthly_placement": "STRIPE_FOUNDING_PARTNER_FEATURED_PRICE_ID",
    "market_exclusive": "STRIPE_FOUNDING_PARTNER_PREMIER_PRICE_ID",
}
MONTHLY_PRICE_ENV_BY_TIER = {
    "founding_pilot": "STRIPE_FOUNDING_PARTNER_LISTING_MONTHLY_PRICE_ID",
    "monthly_placement": "STRIPE_FOUNDING_PARTNER_FEATURED_MONTHLY_PRICE_ID",
    "market_exclusive": "STRIPE_FOUNDING_PARTNER_PREMIER_MONTHLY_PRICE_ID",
}
LEAD_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)


def _json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def _origin(headers):
    # Derive the return target from the deployed request host, not a caller-supplied URL.
    host = (headers.get("host") or "www.homeofferflow.com").split(",", 1)[0].strip()
    if not host or any(char in host for char in "/\\@"):
        host = "www.homeofferflow.com"
    proto = headers.get("x-forwarded-proto") or "https"
    proto = proto.split(",", 1)[0].strip().lower()
    if proto not in {"http", "https"}:
        proto = "https"
    return f"{proto}://{host}"


def _supabase_headers():
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }


def _get_partner_lead(lead_id):
    query = urllib.parse.urlencode({
        "id": f"eq.{lead_id}",
        "select": "id,company_name,contact_name,contact_email,partner_type,market_area,preferred_model,status,payment_status",
        "limit": "1",
    })
    with httpx.Client(timeout=15) as client:
        response = client.get(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{query}",
            headers=_supabase_headers(),
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not load the partner application.")
    rows = response.json() if response.text else []
    return rows[0] if isinstance(rows, list) and rows else None


def _mark_checkout_started(lead_id):
    with httpx.Client(timeout=15) as client:
        response = client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?id=eq.{lead_id}",
            headers={**_supabase_headers(), "Content-Type": "application/json", "Prefer": "return=minimal"},
            json={"payment_status": "checkout_started"},
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not save the checkout state.")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _json(self, 200, {"ok": True})

    def do_POST(self):
        try:
            if not STRIPE_SECRET_KEY or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
                _json(self, 500, {"error": "Partner checkout is not configured."})
                return

            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > 4_000:
                _json(self, 400, {"error": "Invalid request."})
                return
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            lead_id = str(body.get("partnerLeadId") or "").strip()
            if not LEAD_ID_RE.match(lead_id):
                _json(self, 400, {"error": "A valid partner application is required."})
                return

            lead = _get_partner_lead(lead_id)
            if not lead:
                _json(self, 404, {"error": "Partner application was not found."})
                return
            if lead.get("status") in {"declined", "waitlist"}:
                _json(self, 409, {"error": "This application is not eligible for checkout."})
                return
            if lead.get("payment_status") == "paid":
                _json(self, 409, {"error": "This partner application has already been paid."})
                return

            tier = lead.get("preferred_model") or ""
            launch_price_id = os.environ.get(PRICE_ENV_BY_TIER.get(tier, ""), "")
            monthly_price_id = os.environ.get(MONTHLY_PRICE_ENV_BY_TIER.get(tier, ""), "")
            if not launch_price_id or not monthly_price_id:
                _json(self, 500, {"error": "This founding-partner tier is not configured for checkout."})
                return

            origin = _origin(self.headers)
            success_url = f"{origin}/?partner=1&partner_checkout=success&session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{origin}/?partner=1&partner_checkout=cancelled"
            form = {
                # Charge the 90-day launch offer now, then start the recurring
                # standard-price subscription after the 90-day trial.
                "mode": "subscription",
                "customer_email": lead["contact_email"],
                "client_reference_id": lead_id,
                "line_items[0][price]": launch_price_id,
                "line_items[0][quantity]": "1",
                "line_items[1][price]": monthly_price_id,
                "line_items[1][quantity]": "1",
                "allow_promotion_codes": "true",
                "payment_method_collection": "always",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata[source]": "homeofferflow_founding_partner",
                "metadata[partner_lead_id]": lead_id,
                "metadata[partner_tier]": tier,
                "metadata[partner_email]": lead["contact_email"],
                "metadata[partner_type]": lead.get("partner_type") or "other",
                "metadata[market_area]": lead.get("market_area") or "",
                "subscription_data[trial_period_days]": "90",
                "subscription_data[metadata][source]": "homeofferflow_founding_partner",
                "subscription_data[metadata][partner_lead_id]": lead_id,
                "subscription_data[metadata][partner_tier]": tier,
            }
            with httpx.Client(timeout=20) as client:
                response = client.post(
                    "https://api.stripe.com/v1/checkout/sessions",
                    data=form,
                    headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"},
                )
            result = response.json() if response.text else {}
            if response.status_code >= 400 or not result.get("url"):
                message = result.get("error", {}).get("message") if isinstance(result.get("error"), dict) else None
                _json(self, response.status_code if response.status_code >= 400 else 502, {"error": message or "Could not create Stripe Checkout."})
                return

            _mark_checkout_started(lead_id)
            _json(self, 200, {"url": result["url"]})
        except json.JSONDecodeError:
            _json(self, 400, {"error": "Invalid JSON."})
        except Exception as exc:
            print("Partner checkout error:", str(exc))
            _json(self, 500, {"error": "Could not start partner checkout."})
