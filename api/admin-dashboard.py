import os
import json
import uuid
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_SERVICE_KEY") or ""
ADMIN_EMAILS = {e.strip().lower() for e in (os.environ.get("ADMIN_EMAILS") or os.environ.get("HOF_ADMIN_EMAILS") or "").split(",") if e.strip()}
DEFAULT_ADMIN_EMAILS = {"andrew@ondemanddfw.com", "andrewchri@gmail.com", "support@homeofferflow.com"}
ALLOWED_PARTNER_LEAD_STATUSES = {"new", "contacted", "qualified", "waitlist", "converted", "declined"}
ALLOWED_PARTNER_ONBOARDING_STATUSES = {"not_started", "ready", "in_progress", "complete"}
ALLOWED_PARTNER_PLACEMENT_TIERS = {"founding", "premier", "exclusive_market"}
ALLOWED_PARTNER_TYPES = {
    "title", "lender", "inspection", "surveyor", "home_warranty", "insurance",
    "roofing", "hvac", "plumbing", "electrical", "foundation_structural",
    "general_contractor", "pest_termite", "septic_well", "restoration",
    "photography_video", "staging", "repairs_handyman", "cleaning",
    "moving_storage", "lawn_pool", "security_smart_home", "other",
}
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


async def _brokerage_admin_context(user):
    if not user:
        return None
    profiles = await _get(
        "hof_profiles?"
        f"id=eq.{urllib.parse.quote(user['id'])}"
        "&select=id,brokerage_id,is_brokerage_admin,role&limit=1"
    )
    if not profiles:
        return None
    profile = profiles[0]
    brokerage_id = profile.get("brokerage_id")
    if not brokerage_id:
        return None
    role = str(profile.get("role") or "").lower()
    is_admin = bool(profile.get("is_brokerage_admin")) or role == "brokerage_admin"
    if not is_admin:
        memberships = await _get(
            "hof_brokerage_members?"
            f"brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
            f"&user_id=eq.{urllib.parse.quote(user['id'])}"
            "&status=eq.active&role=in.(broker_admin,owner)&select=id&limit=1"
        )
        is_admin = bool(memberships)
    if not is_admin:
        return None
    brokerages = await _get(
        "hof_brokerages?"
        f"id=eq.{urllib.parse.quote(str(brokerage_id))}"
        "&is_active=eq.true&select=id,name,dba_name,slug,logo_url,brand_color,"
        "website_url,license_number,plan_name,billing_status,user_cap&limit=1"
    )
    if not brokerages:
        return None
    return {"profile": profile, "brokerage": brokerages[0]}


def _offer_status_bucket(status):
    status = str(status or "").lower()
    if "signed" in status:
        return "signed"
    if "partial" in status:
        return "partial"
    if "view" in status:
        return "viewed"
    if "await" in status or "sent" in status or "created" in status:
        return "awaiting"
    if "draft" in status:
        return "draft"
    return "other"


async def _brokerage_dashboard_payload(context):
    brokerage = context["brokerage"]
    brokerage_id = str(brokerage["id"])
    members = await _get(
        "hof_brokerage_members?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&select=user_id,email,role,status,created_at,updated_at"
        "&order=created_at.asc&limit=500"
    )
    user_ids = [str(row.get("user_id")) for row in members if row.get("user_id")]
    agent_profiles = []
    subscriptions = []
    offers = []
    if user_ids:
        encoded_ids = ",".join(urllib.parse.quote(user_id) for user_id in user_ids)
        agent_profiles = await _get_optional(
            "hof_agent_profiles?"
            f"user_id=in.({encoded_ids})"
            "&select=user_id,agent_name,agent_email,license_number"
        )
        subscriptions = await _get_optional(
            "hof_subscriptions?"
            f"user_id=in.({encoded_ids})"
            "&select=user_id,status,plan,trial_ends_at,current_period_end"
        )
        offers = await _get_optional(
            "hof_offers?"
            f"user_id=in.({encoded_ids})"
            "&deleted_at=is.null&select=user_id,status,signwell_status,created_at,updated_at"
            "&order=created_at.desc&limit=2000"
        )

    profile_by_user = {str(row.get("user_id")): row for row in agent_profiles}
    subscription_by_user = {str(row.get("user_id")): row for row in subscriptions}
    activity_by_user = {}
    for row in offers:
        user_id = str(row.get("user_id") or "")
        if not user_id:
            continue
        activity = activity_by_user.setdefault(
            user_id,
            {
                "offerCount": 0,
                "signedCount": 0,
                "awaitingCount": 0,
                "draftCount": 0,
                "lastOfferAt": None,
            },
        )
        activity["offerCount"] += 1
        bucket = _offer_status_bucket(row.get("signwell_status") or row.get("status"))
        if bucket == "signed":
            activity["signedCount"] += 1
        elif bucket == "awaiting":
            activity["awaitingCount"] += 1
        elif bucket == "draft":
            activity["draftCount"] += 1
        activity["lastOfferAt"] = activity["lastOfferAt"] or row.get("updated_at") or row.get("created_at")

    safe_agents = []
    for member in members:
        user_id = str(member.get("user_id") or "")
        profile = profile_by_user.get(user_id, {})
        subscription = subscription_by_user.get(user_id, {})
        safe_agents.append(
            {
                "userId": user_id,
                "name": profile.get("agent_name"),
                "email": profile.get("agent_email") or member.get("email"),
                "licenseNumber": profile.get("license_number"),
                "role": member.get("role") or "agent",
                "membershipStatus": member.get("status") or "pending",
                "subscriptionStatus": subscription.get("status"),
                "plan": subscription.get("plan"),
                "trialEndsAt": subscription.get("trial_ends_at"),
                "currentPeriodEnd": subscription.get("current_period_end"),
                "activity": activity_by_user.get(
                    user_id,
                    {
                        "offerCount": 0,
                        "signedCount": 0,
                        "awaitingCount": 0,
                        "draftCount": 0,
                        "lastOfferAt": None,
                    },
                ),
            }
        )

    return {
        "brokerage": brokerage,
        "metrics": {
            "memberCount": len(members),
            "activeMemberCount": len([row for row in members if row.get("status") == "active"]),
            "trialingCount": len([row for row in subscriptions if row.get("status") == "trialing"]),
            "activeSubscriptionCount": len(
                [row for row in subscriptions if row.get("status") in {"active", "trialing"}]
            ),
            "offerCount": len(offers),
            "signedCount": len(
                [
                    row
                    for row in offers
                    if _offer_status_bucket(row.get("signwell_status") or row.get("status")) == "signed"
                ]
            ),
        },
        "agents": safe_agents,
        "privacy": {
            "buyerDetailsIncluded": False,
            "propertyDetailsIncluded": False,
            "offerTermsIncluded": False,
            "documentContentsIncluded": False,
        },
    }


def _parse_partner_lead_update(data):
    lead_id = str(data.get("lead_id") or "").strip()
    status = str(data.get("status") or "").strip().lower()
    try:
        lead_id = str(uuid.UUID(lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("A valid partner lead ID is required.")
    if status not in ALLOWED_PARTNER_LEAD_STATUSES:
        raise ValueError("Choose a valid partner lead status.")
    onboarding_status = str(data.get("onboarding_status") or "").strip().lower()
    if onboarding_status and onboarding_status not in ALLOWED_PARTNER_ONBOARDING_STATUSES:
        raise ValueError("Choose a valid partner onboarding status.")
    return lead_id, status, onboarding_status or None


async def _update_partner_lead(lead_id, status, onboarding_status=None):
    payload = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if onboarding_status:
        payload["onboarding_status"] = onboarding_status
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


def _clean_text(value, maximum):
    value = " ".join(str(value or "").strip().split())
    return value[:maximum] if value else None


def _parse_partner_placement(data):
    partner_name = _clean_text(data.get("partner_name"), 250)
    partner_type = _clean_text(data.get("partner_type"), 80)
    market_area = _clean_text(data.get("market_area"), 300)
    placement_tier = _clean_text(data.get("placement_tier"), 80)
    website_url = _clean_text(data.get("website_url"), 500)
    logo_url = _clean_text(data.get("logo_url"), 500)
    if not partner_name or not market_area:
        raise ValueError("Partner name and market area are required.")
    if partner_type not in ALLOWED_PARTNER_TYPES:
        raise ValueError("Choose a valid partner category.")
    if placement_tier not in ALLOWED_PARTNER_PLACEMENT_TIERS:
        raise ValueError("Choose a valid placement tier.")
    if website_url and not website_url.startswith(("https://", "http://")):
        raise ValueError("Website URL must start with https:// or http://.")
    if logo_url and not logo_url.startswith(("https://", "http://")):
        raise ValueError("Logo URL must start with https:// or http://.")
    try:
        monthly_fee = float(data.get("monthly_fee")) if data.get("monthly_fee") not in (None, "") else None
    except (TypeError, ValueError):
        raise ValueError("Monthly fee must be a number.")
    if monthly_fee is not None and (monthly_fee < 0 or monthly_fee > 100000):
        raise ValueError("Monthly fee is outside the allowed range.")
    return {
        "brokerage_id": None,
        "partner_name": partner_name,
        "partner_type": partner_type,
        "market_area": market_area,
        "placement_tier": placement_tier,
        "website_url": website_url,
        "logo_url": logo_url,
        "monthly_fee": monthly_fee,
        "is_active": True,
    }


async def _create_platform_partner_placement(payload):
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/hof_partner_placements",
            headers={**_headers(), "Prefer": "return=representation"},
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not create the partner placement.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Partner placement was not returned after saving.")
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
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            scope = str((query.get("scope") or [""])[0]).strip().lower()
            if scope == "brokerage":
                context = asyncio.run(_brokerage_admin_context(user))
                if not context:
                    _json(self, 403, {"error": "Brokerage admin access is not enabled for this account."})
                    return
                payload = asyncio.run(_brokerage_dashboard_payload(context))
                _json(self, 200, payload)
                return
            if not asyncio.run(_is_platform_admin(user)):
                _json(self, 403, {"error": "Admin access is not enabled for this account."})
                return
            offers = asyncio.run(_get("hof_offers?select=*&order=created_at.desc&limit=100"))
            events = asyncio.run(_get("hof_offer_events?select=*&order=created_at.desc&limit=50"))
            subs = asyncio.run(_get("hof_subscriptions?select=*&order=created_at.desc&limit=50")) if True else []
            brokerages = asyncio.run(_get("hof_brokerages?select=*&order=created_at.desc&limit=50"))
            partner_leads = asyncio.run(_get_optional("hof_partner_leads?select=*&order=created_at.desc&limit=100"))
            partner_placements = asyncio.run(_get_optional("hof_partner_placements?select=id,partner_type,partner_name,website_url,logo_url,market_area,placement_tier,monthly_fee,is_active,created_at&brokerage_id=is.null&order=created_at.desc&limit=100"))
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
                "activePartnerPlacementCount": len([placement for placement in partner_placements if placement.get("is_active")]),
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
                "partnerPlacements": partner_placements,
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
            if data.get("action") == "create_platform_partner_placement":
                payload = _parse_partner_placement(data)
                row = asyncio.run(_create_platform_partner_placement(payload))
                _json(self, 200, {"ok": True, "partnerPlacement": row})
                return
            lead_id, status, onboarding_status = _parse_partner_lead_update(data)
            row = asyncio.run(_update_partner_lead(lead_id, status, onboarding_status))
            _json(self, 200, {"ok": True, "lead": row})
        except ValueError as exc:
            _json(self, 400, {"error": str(exc)[:300]})
        except json.JSONDecodeError:
            _json(self, 400, {"error": "Invalid JSON."})
        except Exception as exc:
            print("Admin partner lead update error:", str(exc))
            _json(self, 500, {"error": "Could not update the partner lead."})
