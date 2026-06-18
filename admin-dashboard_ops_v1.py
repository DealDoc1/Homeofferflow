import os
import json
import base64
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone
import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_SERVICE_KEY") or ""
ADMIN_EMAILS = {e.strip().lower() for e in (os.environ.get("ADMIN_EMAILS") or os.environ.get("HOF_ADMIN_EMAILS") or "").split(",") if e.strip()}
DEFAULT_ADMIN_EMAILS = {"andrew@ondemanddfw.com", "andrewchri@gmail.com", "support@homeofferflow.com"}


def _json(handler, code, payload):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.end_headers()
    handler.wfile.write(body)


def _decode_jwt_email(auth_header):
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return ""
    token = auth_header.split(" ", 1)[1].strip()
    try:
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(part.encode()).decode())
        return (payload.get("email") or payload.get("user_metadata", {}).get("email") or "").lower()
    except Exception:
        return ""


def _headers():
    return {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "Content-Type": "application/json"}


async def _get(path):
    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=_headers())
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase {path} failed: {r.status_code} {r.text[:300]}")
        return r.json()


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _json(self, 200, {"status": "ok"})

    def do_GET(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            _json(self, 500, {"error": "Supabase env vars missing"})
            return
        email = _decode_jwt_email(self.headers.get("authorization", ""))
        allowed = ADMIN_EMAILS or DEFAULT_ADMIN_EMAILS
        if email and email not in allowed:
            _json(self, 403, {"error": "Admin access is not enabled for this account."})
            return
        try:
            import asyncio
            offers = asyncio.run(_get("hof_offers?select=*&order=created_at.desc&limit=100"))
            events = asyncio.run(_get("hof_offer_events?select=*&order=created_at.desc&limit=50"))
            subs = asyncio.run(_get("hof_subscriptions?select=*&order=created_at.desc&limit=50")) if True else []
            brokerages = asyncio.run(_get("hof_brokerages?select=*&order=created_at.desc&limit=50"))
            total_volume = sum(float(o.get("offer_price") or 0) for o in offers)
            def bucket(s):
                s = str(s or "").lower()
                if "buyer signatures complete" in s or "buyer signed" in s or "signed" in s: return "signed"
                if "partial" in s: return "partial"
                if "view" in s: return "viewed"
                if "await" in s or "sent" in s or "created" in s: return "awaiting"
                return "other"
            metrics = {
                "offerCount": len(offers),
                "homebuyerOfferCount": len([o for o in offers if o.get("role") == "homebuyer"]),
                "agentOfferCount": len([o for o in offers if o.get("role") == "agent"]),
                "investorOfferCount": len([o for o in offers if o.get("role") == "investor"]),
                "signedCount": len([o for o in offers if bucket(o.get("signwell_status") or o.get("status")) == "signed"]),
                "awaitingCount": len([o for o in offers if bucket(o.get("signwell_status") or o.get("status")) == "awaiting"]),
                "offerVolume": total_volume,
                "subscriptionCount": len(subs),
                "brokerageCount": len(brokerages),
                "eventCount": len(events),
            }
            _json(self, 200, {"metrics": metrics, "offers": offers, "events": events, "subscriptions": subs, "brokerages": brokerages, "showings": [], "feedback": []})
        except Exception as e:
            _json(self, 500, {"error": str(e)})
