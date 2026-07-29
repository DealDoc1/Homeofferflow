import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler

import httpx

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE")
    or os.environ.get("SUPABASE_SERVICE_KEY")
    or ""
)


def _service_headers():
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def _safe_return_url(value):
    fallback = "https://www.homeofferflow.com/"
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
        path = parsed.path or "/"
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{parsed.scheme}://{hostname}{port}{path}{query}"
    except Exception:
        return fallback


class handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._json(200, {"ok": True})

    def do_GET(self):
        self._json(200, {"ok": True, "route": "create-billing-portal"})

    def do_POST(self):
        try:
            if not STRIPE_SECRET_KEY:
                self._json(500, {"error": "Missing STRIPE_SECRET_KEY"})
                return
            if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
                self._json(500, {"error": "Billing portal is not configured."})
                return

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(raw or "{}")

            user = self._verified_user(self.headers.get("authorization", ""))
            if not user:
                self._json(401, {"error": "Sign in before opening billing."})
                return

            customer_id = self._customer_id_for_user(user["id"])
            if not customer_id:
                self._json(409, {"error": "This account does not have a Stripe billing profile yet."})
                return

            return_url = _safe_return_url(data.get("returnUrl") or data.get("return_url"))

            form = {
                "customer": customer_id,
                "return_url": return_url,
            }

            with httpx.Client(timeout=20.0) as client:
                resp = client.post(
                    "https://api.stripe.com/v1/billing_portal/sessions",
                    data=form,
                    headers={
                        "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )

            result = resp.json()
            if resp.status_code >= 400:
                self._json(resp.status_code, {"error": result.get("error", {}).get("message", "Stripe billing portal error"), "stripe": result})
                return

            self._json(200, {"url": result.get("url"), "id": result.get("id")})

        except Exception as e:
            self._json(500, {"error": str(e)})

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
        if not payload.get("id"):
            return None
        return {"id": str(payload["id"]), "email": str(payload.get("email") or "").strip().lower()}

    def _customer_id_for_user(self, user_id):
        with httpx.Client(timeout=12) as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/hof_subscriptions",
                params={
                    "user_id": f"eq.{user_id}",
                    "select": "stripe_customer_id",
                    "limit": "1",
                },
                headers=_service_headers(),
            )
        if response.status_code >= 300:
            raise RuntimeError("Could not load the billing profile.")
        rows = response.json()
        if not rows:
            return ""
        return str(rows[0].get("stripe_customer_id") or "").strip()
