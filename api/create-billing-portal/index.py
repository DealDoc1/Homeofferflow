import json
import os
from http.server import BaseHTTPRequestHandler

import httpx

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")


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

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(raw or "{}")

            customer_id = (data.get("customerId") or data.get("customer_id") or "").strip()
            return_url = (data.get("returnUrl") or data.get("return_url") or "https://www.homeofferflow.com").strip()

            if not customer_id:
                self._json(400, {"error": "Missing Stripe customer ID"})
                return

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
