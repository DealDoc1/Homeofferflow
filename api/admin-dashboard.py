import os
import json
import uuid
import re
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
TXR_1501_FORM_CODE = "TXR-1501"
TXR_1507_FORM_CODE = "TXR-1507"
TXR_1508_FORM_CODE = "TXR-1508"


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


def _agreement_text(value, field, maximum=400):
    value = " ".join(str(value or "").strip().split())
    if not value:
        raise ValueError(f"{field} is required.")
    if len(value) > maximum:
        raise ValueError(f"{field} is too long.")
    return value


def _agreement_money(value, field):
    """Keep agreement draft fee values bounded and machine-readable.

    The agent, not HomeOfferFlow, decides which broker-approved compensation
    terms apply. This helper only rejects malformed values before they become a
    private draft; it does not calculate, choose, or alter a fee.
    """
    value = str(value or "").strip().replace(",", "")
    if not value:
        return ""
    if not re.fullmatch(r"\d{1,9}(?:\.\d{1,2})?", value):
        raise ValueError(f"{field} must be a dollar amount with no more than two decimals.")
    return value


def _agreement_percentage(value, field):
    """Validate an explicitly supplied percentage without inferring a term."""
    value = str(value or "").strip().replace("%", "")
    if not value:
        return ""
    if not re.fullmatch(r"\d{1,3}(?:\.\d{1,3})?", value):
        raise ValueError(f"{field} must be a percentage.")
    if float(value) > 100:
        raise ValueError(f"{field} cannot be greater than 100%.")
    return value


def _agreement_date_range(data):
    term_start = _agreement_text(data.get("termStart"), "Term start date", 30)
    term_end = _agreement_text(data.get("termEnd"), "Term end date", 30)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", term_start) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", term_end):
        raise ValueError("Use YYYY-MM-DD for both term dates.")
    try:
        start_date = datetime.strptime(term_start, "%Y-%m-%d").date()
        end_date = datetime.strptime(term_end, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Use valid calendar dates for both term dates.")
    if end_date < start_date:
        raise ValueError("Term end date cannot be before the term start date.")
    return term_start, term_end


def _agreement_clients(data):
    client_values = data.get("clientNames")
    if not isinstance(client_values, list) or not (1 <= len(client_values) <= 2):
        raise ValueError("Add one or two client names.")
    client_names = [_agreement_text(value, "Each client name", 180) for value in client_values]
    if len({name.casefold() for name in client_names}) != len(client_names):
        raise ValueError("Each client must be listed only once.")
    return client_names


def _agreement_compensation(compensation):
    if not isinstance(compensation, dict):
        raise ValueError("Compensation data is invalid.")
    values = {
        "purchase_percentage": _agreement_percentage(compensation.get("purchasePercentage"), "Purchase compensation"),
        "purchase_flat_fee": _agreement_money(compensation.get("purchaseFlatFee"), "Purchase flat fee"),
        "lease_one_month_percentage": _agreement_percentage(compensation.get("leaseOneMonthPercentage"), "Lease one-month-rent compensation"),
        "lease_total_rents_percentage": _agreement_percentage(compensation.get("leaseTotalRentsPercentage"), "Lease total-rents compensation"),
        "lease_flat_fee": _agreement_money(compensation.get("leaseFlatFee"), "Lease flat fee"),
    }
    if not any(values.values()):
        raise ValueError("Choose at least one broker-approved purchase or lease compensation term.")
    return values


def _parse_txr_1507_draft(data):
    if data.get("formCode") != TXR_1507_FORM_CODE:
        raise ValueError("Only TXR-1507 is available through this action.")
    client_names = _agreement_clients(data)
    market_area = _agreement_text(data.get("marketArea"), "Market area", 800)
    term_start, term_end = _agreement_date_range(data)
    service_level = str(data.get("serviceLevel") or "").strip()
    if service_level not in {"full_services", "showing_services"}:
        raise ValueError("Choose Full Services or Showing Services.")
    showing_fee = _agreement_money(data.get("showingFee"), "Showing Services execution fee")
    if service_level == "showing_services" and not showing_fee:
        raise ValueError("Showing Services requires the execution fee.")
    intermediary = str(data.get("intermediary") or "").strip()
    if intermediary not in {"authorized", "not_authorized"}:
        raise ValueError("Choose whether intermediary is authorized.")
    form_source_id = _agreement_text(data.get("formSourceId"), "Approved TXR-1507 source", 80)
    try:
        form_source_id = str(uuid.UUID(form_source_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose an approved TXR-1507 source from your brokerage.")
    compensation = _agreement_compensation(data.get("compensation") or {})
    return {
        "form_source_id": form_source_id,
        "client_names": client_names,
        "agreement_data": {
            "market_area": market_area,
            "term_start": term_start,
            "term_end": term_end,
            "service_level": service_level,
            "showing_fee": showing_fee,
            **compensation,
            "intermediary": intermediary,
        },
    }


def _parse_txr_1501_draft(data):
    if data.get("formCode") != TXR_1501_FORM_CODE:
        raise ValueError("Only TXR-1501 is available through this action.")
    client_names = _agreement_clients(data)
    form_source_id = _agreement_text(data.get("formSourceId"), "Approved TXR-1501 source", 80)
    try:
        form_source_id = str(uuid.UUID(form_source_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose an approved TXR-1501 source from your brokerage.")
    market_area = _agreement_text(data.get("marketArea"), "Market area", 800)
    term_start, term_end = _agreement_date_range(data)
    client_address = _agreement_text(data.get("clientAddress"), "Client address", 300)
    client_city_state_zip = _agreement_text(data.get("clientCityStateZip"), "Client city, state, and ZIP", 180)
    client_phone = _agreement_text(data.get("clientPhone"), "Client phone", 80)
    client_email = _agreement_text(data.get("clientEmail"), "Client email", 180)
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", client_email):
        raise ValueError("Client email must be valid.")
    compensation = _agreement_compensation(data.get("compensation") or {})
    retainer_amount = _agreement_money(data.get("retainerAmount"), "Retainer")
    retainer_treatment = str(data.get("retainerTreatment") or "").strip()
    if retainer_amount and retainer_treatment not in {"apply", "not_apply"}:
        raise ValueError("Choose how the broker-approved retainer is treated.")
    if not retainer_amount:
        retainer_treatment = ""
    protection_days = str(data.get("protectionDays") or "").strip()
    if protection_days:
        if not re.fullmatch(r"\d{1,4}", protection_days) or not (1 <= int(protection_days) <= 9999):
            raise ValueError("Protection period days must be a whole number from 1 to 9999.")
    payment_county = _agreement_text(data.get("paymentCounty"), "Payment county", 100)
    intermediary = str(data.get("intermediary") or "").strip()
    if intermediary not in {"authorized", "not_authorized"}:
        raise ValueError("Choose whether intermediary is authorized.")
    return {
        "form_source_id": form_source_id,
        "client_names": client_names,
        "agreement_data": {
            "market_area": market_area,
            "term_start": term_start,
            "term_end": term_end,
            "client_address": client_address,
            "client_city_state_zip": client_city_state_zip,
            "client_phone": client_phone,
            "client_email": client_email,
            **compensation,
            "retainer_amount": retainer_amount,
            "retainer_treatment": retainer_treatment,
            "protection_days": protection_days,
            "payment_county": payment_county,
            "intermediary": intermediary,
        },
    }


def _parse_txr_1508_draft(data):
    """Validate a private TXR-1508 showing draft without inferring agency.

    TXR-1508 is intentionally limited to an unrepresented customer showing.
    This record is only a broker-approved-source draft; it is not a completed
    form, a showing authorization, or a representation agreement.
    """
    if data.get("formCode") != TXR_1508_FORM_CODE:
        raise ValueError("Only TXR-1508 is available through this action.")
    client_names = _agreement_clients(data)
    form_source_id = _agreement_text(data.get("formSourceId"), "Approved TXR-1508 source", 80)
    try:
        form_source_id = str(uuid.UUID(form_source_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose an approved TXR-1508 source from your brokerage.")
    property_address = _agreement_text(data.get("propertyAddress"), "Property address and city", 400)
    other_broker_values = data.get("otherBrokerAgreement")
    if not isinstance(other_broker_values, list) or len(other_broker_values) != len(client_names):
        raise ValueError("Confirm each customer's current representation-agreement status.")
    other_broker_agreement = []
    for value in other_broker_values:
        if value not in {"yes", "no"}:
            raise ValueError("Confirm each customer's current representation-agreement status.")
        other_broker_agreement.append(value)
    if data.get("unrepresentedAcknowledgment") is not True:
        raise ValueError("Confirm the no-representation, no-compensation, and no-advice limits.")
    return {
        "form_source_id": form_source_id,
        "client_names": client_names,
        "agreement_data": {
            "property_address": property_address,
            "other_broker_agreement": other_broker_agreement,
            "unrepresented_acknowledgment": True,
        },
    }


async def _active_brokerage_member(user):
    profiles = await _get(
        "hof_profiles?"
        f"id=eq.{urllib.parse.quote(user['id'])}"
        "&select=id,brokerage_id&limit=1"
    )
    if not profiles or not profiles[0].get("brokerage_id"):
        raise PermissionError("An active brokerage membership is required for this agreement.")
    brokerage_id = str(profiles[0]["brokerage_id"])
    memberships = await _get(
        "hof_brokerage_members?"
        f"user_id=eq.{urllib.parse.quote(user['id'])}"
        f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&status=eq.active&select=id&limit=1"
    )
    if not memberships:
        raise PermissionError("Your brokerage membership is not active.")
    return brokerage_id


async def _create_representation_draft(user, data, form_code, parser):
    draft = parser(data)
    brokerage_id = await _active_brokerage_member(user)
    sources = await _get(
        "hof_brokerage_form_sources?"
        f"id=eq.{urllib.parse.quote(draft['form_source_id'])}"
        f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&form_code=eq.{urllib.parse.quote(form_code)}&status=eq.approved"
        "&authorization_attested=is.true&select=id,source_revision&limit=1"
    )
    if not sources:
        raise ValueError(f"Choose an approved {form_code} source from your brokerage.")
    source = sources[0]
    record = {
        "brokerage_id": brokerage_id,
        "agent_user_id": user["id"],
        "form_source_id": source["id"],
        "form_code": form_code,
        "source_revision": source["source_revision"],
        "status": "draft",
        "client_names": draft["client_names"],
        "agreement_data": draft["agreement_data"],
    }
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/hof_standalone_agreements",
            headers={**_headers(), "Prefer": "return=representation"},
            json=record,
        )
    if response.status_code not in {200, 201}:
        raise RuntimeError("Could not save the agreement draft.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Agreement draft was not returned after saving.")
    return rows[0]


async def _create_txr_1507_draft(user, data):
    return await _create_representation_draft(user, data, TXR_1507_FORM_CODE, _parse_txr_1507_draft)


async def _create_txr_1501_draft(user, data):
    return await _create_representation_draft(user, data, TXR_1501_FORM_CODE, _parse_txr_1501_draft)


async def _create_txr_1508_draft(user, data):
    return await _create_representation_draft(user, data, TXR_1508_FORM_CODE, _parse_txr_1508_draft)


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
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > MAX_BODY_BYTES:
                _json(self, 400, {"error": "Invalid request size."})
                return
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if data.get("action") == "create_txr_1507_draft":
                draft = asyncio.run(_create_txr_1507_draft(user, data))
                _json(self, 201, {"status": "ok", "agreement": draft})
                return
            if data.get("action") == "create_txr_1501_draft":
                draft = asyncio.run(_create_txr_1501_draft(user, data))
                _json(self, 201, {"status": "ok", "agreement": draft})
                return
            if data.get("action") == "create_txr_1508_draft":
                draft = asyncio.run(_create_txr_1508_draft(user, data))
                _json(self, 201, {"status": "ok", "agreement": draft})
                return
            if not asyncio.run(_is_platform_admin(user)):
                _json(self, 403, {"error": "Admin access is not enabled for this account."})
                return
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
