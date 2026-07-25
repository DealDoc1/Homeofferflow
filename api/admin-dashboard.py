import os
import json
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_SERVICE_KEY") or ""
ADMIN_EMAILS = {e.strip().lower() for e in (os.environ.get("ADMIN_EMAILS") or os.environ.get("HOF_ADMIN_EMAILS") or "").split(",") if e.strip()}
DEFAULT_ADMIN_EMAILS = {"andrew@ondemanddfw.com", "andrewchri@gmail.com", "support@homeofferflow.com"}
ALLOWED_PARTNER_LEAD_STATUSES = {"new", "contacted", "qualified", "waitlist", "converted", "declined"}
MAX_BODY_BYTES = 12_000


def _json(handler, code, payload):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.end_headers()
    handler.wfile.write(body)


def _headers():
    return {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "Content-Type": "application/json"}


async def _get(path):
    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=_headers())
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase {path} failed: {r.status_code} {r.text[:300]}")
        return r.json()


async def _get_optional(path):
    try:
        return await _get(path)
    except Exception as exc:
        print(f"Optional admin dataset unavailable ({path}): {str(exc)[:300]}")
        return []


async def _verified_user(auth_header):
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
        if response.status_code != 200:
            return None
        payload = response.json()
        if not payload.get("id") or not payload.get("email"):
            return None
        return {"id": str(payload["id"]), "email": str(payload["email"]).strip().lower()}


async def _is_platform_admin(user):
    if not user:
        return False
    allowed = ADMIN_EMAILS or DEFAULT_ADMIN_EMAILS
    if user["email"] in allowed:
        return True
    rows = await _get(f"hof_platform_admins?user_id=eq.{user['id']}&select=user_id&limit=1")
    return bool(rows)


def _parse_partner_lead_update(data):
    lead_id = str(data.get("lead_id") or "").strip()
    status = str(data.get("status") or "").strip().lower()
    try:
        lead_id = str(uuid.UUID(lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("A valid partner lead ID is required.")
    if status not in ALLOWED_PARTNER_LEAD_STATUSES:
        raise ValueError("Choose a valid partner lead status.")
    return lead_id, status


async def _update_partner_lead(lead_id, status):
    payload = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?id=eq.{lead_id}",
            headers={**_headers(), "Prefer": "return=representation"},
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not update the partner lead.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise ValueError("Partner lead was not found.")
    return rows[0]


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _json(self, 200, {"status": "ok"})

    def do_GET(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            _json(self, 500, {"error": "Supabase env vars missing"})
            return
        try:
            import asyncio
            user = asyncio.run(_verified_user(self.headers.get("authorization", "")))
            if not user:
                _json(self, 401, {"error": "A valid signed-in session is required."})
                return
            if not asyncio.run(_is_platform_admin(user)):
                _json(self, 403, {"error": "Admin access is not enabled for this account."})
                return
            offers = asyncio.run(_get("hof_offers?select=*&order=created_at.desc&limit=100"))
            events = asyncio.run(_get("hof_offer_events?select=*&order=created_at.desc&limit=50"))
            subs = asyncio.run(_get("hof_subscriptions?select=*&order=created_at.desc&limit=50")) if True else []
            brokerages = asyncio.run(_get("hof_brokerages?select=*&order=created_at.desc&limit=50"))
            partner_leads = asyncio.run(_get_optional("hof_partner_leads?select=*&order=created_at.desc&limit=100"))
            roadmap = asyncio.run(_get("hof_roadmap_items?select=*&order=priority.asc&limit=100"))
            qa_scenarios = asyncio.run(_get("hof_qa_scenarios?select=*&active=eq.true&order=priority.asc&limit=100"))
            qa_runs = asyncio.run(_get("hof_qa_runs?select=*&order=created_at.desc&limit=50"))
            releases = asyncio.run(_get("hof_releases?select=*&order=created_at.desc&limit=20"))
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
                "partnerLeadCount": len(partner_leads),
                "qualifiedPartnerLeadCount": len([lead for lead in partner_leads if lead.get("status") in {"qualified", "converted"}]),
                "eventCount": len(events),
                "roadmapCount": len(roadmap),
                "roadmapBlockedCount": len([item for item in roadmap if item.get("status") == "blocked"]),
                "qaScenarioCount": len(qa_scenarios),
                "qaVerifiedCount": len([item for item in qa_scenarios if item.get("current_status") in {"passed", "staging_passed", "production"}]),
                "releaseCount": len(releases),
            }
            _json(self, 200, {
                "metrics": metrics,
                "offers": offers,
                "events": events,
                "subscriptions": subs,
                "brokerages": brokerages,
                "partnerLeads": partner_leads,
                "roadmap": roadmap,
                "qaScenarios": qa_scenarios,
                "qaRuns": qa_runs,
                "releases": releases,
                "showings": [],
                "feedback": [],
            })
        except Exception as e:
            _json(self, 500, {"error": str(e)})

    def do_POST(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            _json(self, 500, {"error": "Supabase env vars missing"})
            return
        try:
            import asyncio
            user = asyncio.run(_verified_user(self.headers.get("authorization", "")))
            if not user:
                _json(self, 401, {"error": "A valid signed-in session is required."})
                return
            if not asyncio.run(_is_platform_admin(user)):
                _json(self, 403, {"error": "Admin access is not enabled for this account."})
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > MAX_BODY_BYTES:
                _json(self, 400, {"error": "Invalid request size."})
                return
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            lead_id, status = _parse_partner_lead_update(data)
            row = asyncio.run(_update_partner_lead(lead_id, status))
            _json(self, 200, {"ok": True, "lead": row})
        except ValueError as exc:
            _json(self, 400, {"error": str(exc)[:300]})
        except json.JSONDecodeError:
            _json(self, 400, {"error": "Invalid JSON."})
        except Exception as exc:
            print("Admin partner lead update error:", str(exc))
            _json(self, 500, {"error": "Could not update the partner lead."})
