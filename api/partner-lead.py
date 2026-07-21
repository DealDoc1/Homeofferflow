import json
import os
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

import httpx


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE")
    or os.environ.get("SUPABASE_SERVICE_KEY")
    or ""
)
MAX_BODY_BYTES = 60_000
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
ALLOWED_PARTNER_TYPES = {
    "title",
    "lender",
    "inspection",
    "home_warranty",
    "insurance",
    "photography_video",
    "staging",
    "repairs_handyman",
    "cleaning",
    "moving_storage",
    "lawn_pool",
    "other",
}
ALLOWED_MODELS = {"founding_pilot", "monthly_placement", "market_exclusive", "discuss"}
ALLOWED_BUDGETS = {"under_250", "250_499", "500_999", "1000_plus", "discuss"}


def _send(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _text(value, max_len=500):
    if value is None:
        return None
    cleaned = " ".join(str(value).strip().split())
    return cleaned[:max_len] if cleaned else None


def _choice(value, allowed, default):
    value = _text(value, 80)
    return value if value in allowed else default


def _build_payload(data):
    company_name = _text(data.get("company_name"), 250)
    contact_name = _text(data.get("contact_name"), 250)
    contact_email = _text(data.get("contact_email"), 250)
    market_area = _text(data.get("market_area"), 300)

    if not company_name or not contact_name or not contact_email or not market_area:
        raise ValueError("Company, contact name, email, and market area are required.")
    if not EMAIL_RE.match(contact_email):
        raise ValueError("Enter a valid contact email.")

    now = datetime.now(timezone.utc).isoformat()
    return {
        "partner_type": _choice(data.get("partner_type"), ALLOWED_PARTNER_TYPES, "other"),
        "company_name": company_name,
        "contact_name": contact_name,
        "contact_email": contact_email.lower(),
        "contact_phone": _text(data.get("contact_phone"), 80),
        "website_url": _text(data.get("website_url"), 500),
        "market_area": market_area,
        "customer_focus": _text(data.get("customer_focus"), 300),
        "monthly_budget_range": _choice(data.get("monthly_budget_range"), ALLOWED_BUDGETS, "discuss"),
        "preferred_model": _choice(data.get("preferred_model"), ALLOWED_MODELS, "founding_pilot"),
        "message": _text(data.get("message"), 2000),
        "source": _text(data.get("source"), 120) or "website_partner_modal",
        "utm_source": _text(data.get("utm_source"), 120),
        "utm_medium": _text(data.get("utm_medium"), 120),
        "utm_campaign": _text(data.get("utm_campaign"), 160),
        "utm_content": _text(data.get("utm_content"), 160),
        "landing_page": _text(data.get("landing_page"), 800),
        "status": "new",
        "created_at": now,
        "updated_at": now,
    }


def _insert_partner_lead(payload):
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    with httpx.Client(timeout=12.0) as client:
        response = client.post(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads",
            headers=headers,
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError(f"Supabase insert failed with status {response.status_code}.")
    rows = response.json() if response.text else []
    return rows[0] if isinstance(rows, list) and rows else {}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _send(self, 204, {})

    def do_POST(self):
        try:
            if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
                return _send(self, 500, {"error": "Partner intake is not configured."})

            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > MAX_BODY_BYTES:
                return _send(self, 400, {"error": "Invalid request size."})

            data = json.loads(self.rfile.read(length).decode("utf-8"))

            # Quietly accept bots that fill the hidden field without polluting the CRM.
            if _text(data.get("company_website_confirm"), 250):
                return _send(self, 200, {"ok": True})

            payload = _build_payload(data)
            row = _insert_partner_lead(payload)
            return _send(
                self,
                200,
                {
                    "ok": True,
                    "partner_lead_id": row.get("id"),
                    "message": "Partner interest received.",
                },
            )
        except ValueError as exc:
            return _send(self, 400, {"error": str(exc)[:300]})
        except json.JSONDecodeError:
            return _send(self, 400, {"error": "Invalid JSON."})
        except Exception as exc:
            print("Partner lead error:", str(exc)[:500])
            return _send(self, 500, {"error": "Could not save partner interest."})
