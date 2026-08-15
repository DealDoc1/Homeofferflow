import os
import json
import uuid
import re
import hashlib
import secrets
import html
import base64
import urllib.parse
from datetime import datetime, timedelta, timezone
from io import BytesIO
from http.server import BaseHTTPRequestHandler
import httpx
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas
from lib import platform_form_source_upload as platform_source
from lib import seller_disclosure_draft
from lib import seller_review_access

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_SERVICE_KEY") or ""
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
PARTNER_ONBOARDING_FROM_EMAIL = os.environ.get("PARTNER_ONBOARDING_FROM_EMAIL", "offers@homeofferflow.com")
PARTNER_AGREEMENT_COPY_EMAIL = os.environ.get("PARTNER_AGREEMENT_COPY_EMAIL", "support@homeofferflow.com").strip().lower()
PARTNER_AGREEMENT_SIGNING_ENABLED = str(os.environ.get("HOF_PARTNER_AGREEMENT_SIGNING_ENABLED", "false")).lower() in {"1", "true", "yes", "on"}
PARTNER_AGREEMENT_SIGNWELL_TEST_MODE = str(os.environ.get("HOF_PARTNER_AGREEMENT_SIGNWELL_TEST_MODE", "false")).lower() in {"1", "true", "yes", "on"}
SIGNWELL_API_KEY = os.environ.get("SIGNWELL_API_KEY", "")
SIGNWELL_ENABLED = str(os.environ.get("SIGNWELL_ENABLED", "false")).lower() in {"1", "true", "yes", "on"}
SIGNWELL_TEST_MODE = str(os.environ.get("SIGNWELL_TEST_MODE", "true")).lower() in {"1", "true", "yes", "on"}
# This is deliberately a boolean-only health signal. The dashboard must never
# receive the webhook identifier or verification key itself.
SIGNWELL_WEBHOOK_VERIFICATION_CONFIGURED = bool(os.environ.get("SIGNWELL_WEBHOOK_ID"))
# Restricted TXR signing is deliberately opt-in.  A source/authorization gate
# alone is not enough; the completed signed-PDF release gate must remain in
# force before this is enabled in production.
TXR_SIGNING_ENABLED = str(os.environ.get("HOF_TXR_SIGNING_ENABLED", "false")).lower() in {"1", "true", "yes", "on"}
BROKERAGE_INVITE_FROM_EMAIL = (
    os.environ.get("BROKERAGE_INVITE_FROM_EMAIL")
    or os.environ.get("FEEDBACK_FROM_EMAIL")
    or os.environ.get("FROM_EMAIL")
    or "offers@homeofferflow.com"
)
BROKERAGE_INVITE_REPLY_TO = os.environ.get("BROKERAGE_INVITE_REPLY_TO", "").strip()
ADMIN_EMAILS = {e.strip().lower() for e in (os.environ.get("ADMIN_EMAILS") or os.environ.get("HOF_ADMIN_EMAILS") or "").split(",") if e.strip()}
DEFAULT_ADMIN_EMAILS = {"andrew@ondemanddfw.com", "andrewchri@gmail.com", "support@homeofferflow.com"}
ALLOWED_PARTNER_LEAD_STATUSES = {"new", "contacted", "qualified", "waitlist", "converted", "declined"}
ALLOWED_PARTNER_ONBOARDING_STATUSES = {"not_started", "ready", "in_progress", "complete"}
SANDBOX_PARTNER_LEAD_SOURCES = {"sandbox_checkout_test", "sandbox_webhook_end_to_end"}
ALLOWED_SELLER_LEAD_STATUSES = {"new", "contacted", "qualified", "converted", "archived"}
ALLOWED_BROKERAGE_MEMBER_STATUSES = {"active", "suspended"}
MAX_BROKERAGE_TEAM_NAME_LENGTH = 80
ALLOWED_PARTNER_PLACEMENT_TIERS = {"founding", "premier", "exclusive_market"}
ALLOWED_PARTNER_TYPES = {
    "title", "lender", "inspection", "surveyor", "home_warranty", "insurance",
    "roofing", "hvac", "plumbing", "electrical", "foundation_structural",
    "general_contractor", "pest_termite", "septic_well", "restoration",
    "photography_video", "staging", "repairs_handyman", "cleaning",
    "moving_storage", "lawn_pool", "security_smart_home", "other",
}
AI_CALIBRATION_REVIEWER_ROLES = {"agent", "broker", "brokerage_admin"}
AI_CALIBRATION_SCENARIOS = {
    "AI-CAL-01",
    "AI-CAL-02",
    "AI-CAL-03",
    "AI-CAL-04",
    "AI-CAL-05",
}
MAX_BODY_BYTES = 12_000
MAX_SOURCE_UPLOAD_BODY_BYTES = 15 * 1024 * 1024
PUBLIC_APP_ORIGIN = (os.environ.get("PUBLIC_APP_URL") or "https://www.homeofferflow.com").rstrip("/")
BROKERAGE_INVITE_EMAIL_RE = re.compile(r"(?=.{3,254}$)[^@\s]+@[^@\s]+\.[^@\s]+$")
BROKERAGE_BRAND_COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}$")
BROKERAGE_BRANDING_BUCKET = "brokerage-branding"
TXR_1501_FORM_CODE = "TXR-1501"
TXR_1506_FORM_CODE = "TXR-1506"
TXR_1507_FORM_CODE = "TXR-1507"
TXR_1508_FORM_CODE = "TXR-1508"
TREC_55_1_FORM_CODE = "TREC-55-1"
TREC_61_0_FORM_CODE = "TREC-61-0"
BROKERAGE_TXR_FORM_CODES = (
    "TXR-1507",
    "TXR-1501",
    "TXR-1508",
    "TXR-1506",
    "TXR-1101",
    "TXR-1102",
    "TXR-1406",
    "TXR-1418",
)


def _is_sandbox_partner_lead(lead):
    """Keep Stripe sandbox artifacts out of live partner revenue reporting."""
    source = str((lead or {}).get("source") or "").strip().lower()
    if source in SANDBOX_PARTNER_LEAD_SOURCES:
        return True
    # Older sandbox rows may lack the source marker, but Stripe test-mode
    # Checkout identifiers remain a provider-authored, unambiguous signal.
    session_id = str((lead or {}).get("stripe_checkout_session_id") or "").strip().lower()
    return session_id.startswith("cs_test_")


def _partner_activation_readiness(lead, now=None):
    """Return a non-secret, stage-specific paid-partner activation state."""
    lead = lead or {}
    now = now or datetime.now(timezone.utc)
    onboarding = str(lead.get("onboarding_status") or "not_started").lower()
    agreement = str(lead.get("partner_agreement_status") or "not_started").lower()
    setup_complete = onboarding in {"complete", "completed"}

    if not setup_complete:
        expires_at = _parse_timestamp(lead.get("onboarding_token_expires_at"))
        setup_link_valid = bool(lead.get("onboarding_token_hash")) and bool(expires_at and expires_at > now)
        if onboarding == "in_progress":
            return {"code": "awaiting_setup", "label": "Awaiting partner setup", "tone": "warn", "next_action": "Partner needs to finish setup details.", "partner_message": "finish the remaining onboarding details so we can prepare the written agreement"}
        if setup_link_valid:
            return {"code": "setup_link_sent", "label": "Setup link sent", "tone": "warn", "next_action": "Await partner setup completion.", "partner_message": "complete the secure setup details so we can prepare the written agreement"}
        return {"code": "setup_link_needed", "label": "Fresh setup link needed", "tone": "warn", "next_action": "Issue a new secure setup link.", "partner_message": "complete the secure setup details so we can prepare the written agreement"}

    if agreement == "signed" and lead.get("partner_agreement_signed_at"):
        return {"code": "ready_to_activate", "label": "Ready to activate", "tone": "good", "next_action": "Create the approved public placement.", "partner_message": "confirm the planned public placement activation"}
    if agreement == "sent":
        return {"code": "awaiting_agreement", "label": "Awaiting agreement signature", "tone": "warn", "next_action": "Await completed SignWell agreement.", "partner_message": "review and sign the HomeOfferFlow Partner Marketplace Agreement sent through SignWell"}
    if agreement in {"declined", "expired", "void"}:
        return {"code": "agreement_needs_resolution", "label": "Agreement needs resolution", "tone": "warn", "next_action": "Resolve the agreement before activation.", "partner_message": "contact us about the HomeOfferFlow Partner Marketplace Agreement before placement activation"}
    if not PARTNER_AGREEMENT_SIGNING_ENABLED:
        return {"code": "agreement_review_pending", "label": "Agreement review pending", "tone": "warn", "next_action": "Complete agreement approval before sending through SignWell.", "partner_message": "we will send the HomeOfferFlow Partner Marketplace Agreement after its final review"}
    return {"code": "agreement_ready_to_send", "label": "Send agreement", "tone": "warn", "next_action": "Send the agreement through SignWell.", "partner_message": "expect the HomeOfferFlow Partner Marketplace Agreement for signature"}


def _pdf_response(handler, pdf_bytes, filename):
    body = bytes(pdf_bytes or b"")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/pdf")
    handler.send_header("Content-Disposition", f'inline; filename="{filename}"')
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "private, no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _json(handler, code, payload):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _headers():
    return {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "Content-Type": "application/json"}


def _is_ai_calibration_evidence(item):
    """Count only anonymized AI notes from an agent or brokerage professional.

    The feedback endpoint enforces anonymization before persistence. The
    dashboard must still avoid treating a homebuyer/investor comment as the
    documented broker/agent calibration evidence threshold.
    """
    return (
        str((item or {}).get("issue_type") or "").lower() == "ai_review"
        and str((item or {}).get("role") or "").lower() in AI_CALIBRATION_REVIEWER_ROLES
        and str((item or {}).get("calibration_scenario") or "").upper() in AI_CALIBRATION_SCENARIOS
    )


def _ai_calibration_scenario_ids(items):
    return sorted({
        str((item or {}).get("calibration_scenario") or "").upper()
        for item in (items or [])
        if _is_ai_calibration_evidence(item)
    })


def _missing_form_request_code_counts(items):
    """Return only normalized form-code demand counts, never feedback text."""
    counts = {}
    code_patterns = (
        (re.compile(r"\bTXR\s*-?\s*(\d{4})\b", re.IGNORECASE), lambda match: f"TXR-{match.group(1)}"),
        (re.compile(r"\bTREC\s*-?\s*(\d{2})\s*-?\s*(\d)\b", re.IGNORECASE), lambda match: f"TREC-{match.group(1)}-{match.group(2)}"),
    )
    for item in (items or []):
        if str((item or {}).get("issue_type") or "").lower() != "missing_addendum":
            continue
        message = str((item or {}).get("message") or "")
        for pattern, normalize in code_patterns:
            for match in pattern.finditer(message):
                code = normalize(match)
                counts[code] = counts.get(code, 0) + 1
    return dict(sorted(counts.items(), key=lambda entry: (-entry[1], entry[0])))


def _missing_form_request_recent_code_counts(items, days=30):
    """Return recent normalized demand counts without exposing feedback text."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    counts = {}
    code_patterns = (
        (re.compile(r"\bTXR\s*-?\s*(\d{4})\b", re.IGNORECASE), lambda match: f"TXR-{match.group(1)}"),
        (re.compile(r"\bTREC\s*-?\s*(\d{2})\s*-?\s*(\d)\b", re.IGNORECASE), lambda match: f"TREC-{match.group(1)}-{match.group(2)}"),
    )
    for item in (items or []):
        if str((item or {}).get("issue_type") or "").lower() != "missing_addendum":
            continue
        created_at = _parse_timestamp((item or {}).get("created_at"))
        if not created_at or created_at < cutoff:
            continue
        message = str((item or {}).get("message") or "")
        for pattern, normalize in code_patterns:
            for match in pattern.finditer(message):
                code = normalize(match)
                counts[code] = counts.get(code, 0) + 1
    return dict(sorted(counts.items(), key=lambda entry: (-entry[1], entry[0])))


def _missing_form_request_priority(items, recent_days=30):
    """Rank normalized missing-form demand for source-intake decisions.

    Recent requests receive a 2x recency boost on top of lifetime demand so a
    short launch surge can outrank an older, larger backlog. The result only
    contains normalized codes and counts; request text is never exposed.
    """
    total_counts = _missing_form_request_code_counts(items)
    recent_counts = _missing_form_request_recent_code_counts(items, days=recent_days)
    rows = []
    for code, total in total_counts.items():
        recent = int(recent_counts.get(code) or 0)
        rows.append({
            "code": code,
            "total": int(total),
            "recent": recent,
            "score": int(total) + (recent * 2),
        })
    rows.sort(key=lambda row: (-row["score"], -row["recent"], row["code"]))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


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


async def _record_offer_event(user_id, event_type, message, metadata=None):
    """Best-effort aggregate telemetry for authenticated or verified workflows."""
    if not user_id or not event_type:
        return
    payload = {
        "offer_id": None,
        "user_id": str(user_id),
        "event_type": str(event_type),
        "status": "completed",
        "message": str(message or "")[:240],
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/hof_offer_events",
                headers={**_headers(), "Prefer": "return=minimal"},
                json=payload,
            )
            if response.status_code >= 300:
                return
    except Exception:
        return


async def _patch(table, query, payload):
    """Patch a service-owned row and fail closed on non-success responses."""
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/{table}?{query}",
            headers={**_headers(), "Prefer": "return=minimal"},
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError(f"Supabase update failed: {table} {response.status_code} {response.text[:300]}")


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
    # The environment list can add controlled operations accounts, but it must
    # never silently remove the core HomeOfferFlow platform-admin accounts.
    # This keeps support access recoverable if a production env update omits an
    # address by mistake.
    allowed = DEFAULT_ADMIN_EMAILS | ADMIN_EMAILS
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

    # A profile flag alone must never outlive a suspended or removed brokerage
    # membership. Brokerage-visible dashboards expose roster and aggregate offer
    # activity, so every broker context requires an active broker/owner
    # membership in addition to the profile's brokerage association.
    memberships = await _get(
        "hof_brokerage_members?"
        f"brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
        f"&user_id=eq.{urllib.parse.quote(user['id'])}"
        "&status=eq.active&role=in.(broker_admin,owner)&select=id&limit=1"
    )
    if not memberships:
        return None

    brokerages = await _get(
        "hof_brokerages?"
        f"id=eq.{urllib.parse.quote(str(brokerage_id))}"
        "&is_active=eq.true&select=id,name,dba_name,slug,logo_url,brand_color,"
        "website_url,license_number,plan_name,billing_status,user_cap,"
        "default_title_company,default_title_contact,txr_all_agents_authorized,"
        "txr_authorization_attested_by,txr_authorization_attested_at&limit=1"
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
        "&select=user_id,email,role,status,txr_agent_authorized,txr_agent_attested_at,created_at,updated_at"
        "&order=created_at.asc&limit=500"
    )
    pending_invites = await _get_optional(
        "hof_brokerage_invites?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&status=eq.pending&select=id,email,role,status,created_at,expires_at"
        "&order=created_at.desc&limit=100"
    )
    invite_history = await _get_optional(
        "hof_brokerage_invites?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&select=status,email,created_at,accepted_at"
        "&order=created_at.desc&limit=500"
    )
    accepted_invite_count = len([
        invite for invite in invite_history if str(invite.get("status") or "").lower() == "accepted"
    ])
    invite_acceptance_rate = round((accepted_invite_count / len(invite_history)) * 100) if invite_history else 0
    accepted_invite_emails = {
        str(invite.get("email") or "").strip().lower()
        for invite in invite_history
        if str(invite.get("status") or "").lower() == "accepted" and str(invite.get("email") or "").strip()
    }
    active_member_emails = {
        str(member.get("email") or "").strip().lower()
        for member in members
        if str(member.get("status") or "").lower() == "active" and str(member.get("email") or "").strip()
    }
    accepted_invite_active_count = len(accepted_invite_emails & active_member_emails)
    accepted_invite_needing_activation_count = max(0, accepted_invite_count - accepted_invite_active_count)
    accepted_invite_needing_activation_aged_count = len([
        invite for invite in invite_history
        if str(invite.get("status") or "").lower() == "accepted"
        and str(invite.get("email") or "").strip().lower() not in active_member_emails
        and (accepted_at := _parse_timestamp(invite.get("accepted_at") or invite.get("created_at")))
        and accepted_at <= datetime.now(timezone.utc) - timedelta(days=3)
    ])
    accepted_invite_activation_rate = round(
        (accepted_invite_active_count / accepted_invite_count) * 100, 1
    ) if accepted_invite_count else 0
    now = datetime.now(timezone.utc)
    pending_invites_expiring_soon = [
        invite for invite in pending_invites
        if (expires_at := _parse_timestamp(invite.get("expires_at")))
        and now <= expires_at <= now + timedelta(days=3)
    ]
    pending_invites_expired = [
        invite for invite in pending_invites
        if (expires_at := _parse_timestamp(invite.get("expires_at"))) and expires_at < now
    ]
    pending_invites_aged = [
        invite for invite in pending_invites
        if (created_at := _parse_timestamp(invite.get("created_at")))
        and created_at <= now - timedelta(days=7)
    ]
    # Oldest pending invitations are the most likely to go stale and should
    # appear first in the broker's follow-up workspace.
    pending_invites.sort(
        key=lambda invite: _parse_timestamp(invite.get("created_at"))
        or datetime.max.replace(tzinfo=timezone.utc)
    )
    # Expose only source-readiness metadata to the broker dashboard. Never
    # return storage paths, filenames, fingerprints, or source URLs here.
    # Agents do not receive this payload, and source PDFs remain private.
    form_sources = await _get_optional(
        "hof_brokerage_form_sources?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&status=neq.retired"
        "&select=form_code,source_revision,status,authorization_attested,updated_at"
        "&order=updated_at.desc&limit=500"
    )
    # Brokerage administrators receive only aggregate listing-workspace counts.
    # Seller names, property addresses, notes, and requested workflows remain in
    # the agent-owned workspace and are never returned by this dashboard route.
    listing_workspaces = await _get_optional(
        "hof_listing_workspaces?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&select=listing_kind,status&limit=5000"
    )
    user_ids = [str(row.get("user_id")) for row in members if row.get("user_id")]
    agent_profiles = []
    brokerage_profiles = []
    subscriptions = []
    offers = []
    usage_events = []
    billing_month = datetime.now(timezone.utc).strftime("%Y-%m")
    if user_ids:
        encoded_ids = ",".join(urllib.parse.quote(user_id) for user_id in user_ids)
        agent_profiles = await _get_optional(
            "hof_agent_profiles?"
            f"user_id=in.({encoded_ids})"
            "&select=user_id,agent_name,agent_email,license_number"
        )
        # Team labels live on the account profile. They are an organizational
        # convenience only; membership roles remain support-managed.
        brokerage_profiles = await _get_optional(
            "hof_profiles?"
            f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
            f"&id=in.({encoded_ids})"
            "&select=id,team_name"
        )
        subscriptions = await _get_optional(
            "hof_subscriptions?"
            f"user_id=in.({encoded_ids})"
            "&select=user_id,status,plan,packet_limit,trial_ends_at,current_period_end"
        )
        # Usage telemetry is loaded after the core roster queries so older
        # deployments without this optional table remain compatible.
        offers = await _get_optional(
            "hof_offers?"
            f"user_id=in.({encoded_ids})"
            "&deleted_at=is.null&select=user_id,status,signwell_status,created_at,updated_at"
            "&order=created_at.desc&limit=2000"
        )
        try:
            usage_events = await _get_optional(
                "hof_usage_events?"
                f"user_id=in.({encoded_ids})&billing_month=eq.{billing_month}"
                "&event_type=eq.signed_packet&select=user_id,quantity&limit=100000"
            )
        except Exception:
            # A missing or temporarily unavailable telemetry table must not
            # hide the core brokerage roster and activity payload.
            usage_events = []

    profile_by_user = {str(row.get("user_id")): row for row in agent_profiles}
    team_by_user = {
        str(row.get("id")): row.get("team_name")
        for row in brokerage_profiles
        if str(row.get("id") or "")
    }
    subscription_by_user = {str(row.get("user_id")): row for row in subscriptions}
    usage_by_user = {}
    for event in usage_events:
        user_id = str(event.get("user_id") or "")
        if not user_id:
            continue
        try:
            quantity = max(0, int(event.get("quantity") or 0))
        except (TypeError, ValueError):
            quantity = 0
        usage_by_user[user_id] = usage_by_user.get(user_id, 0) + quantity
    accepted_invite_user_ids = {
        str(member.get("user_id"))
        for member in members
        if str(member.get("user_id") or "")
        and str(
            member.get("email")
            or profile_by_user.get(str(member.get("user_id")), {}).get("agent_email")
            or ""
        ).strip().lower() in accepted_invite_emails
    }
    accepted_invite_subscribed_count = len({
        user_id for user_id in accepted_invite_user_ids
        if str(subscription_by_user.get(user_id, {}).get("status") or "").lower()
        in {"active", "trialing", "free_admin"}
    })
    accepted_invite_subscription_rate = round(
        (accepted_invite_subscribed_count / accepted_invite_count) * 100, 1
    ) if accepted_invite_count else 0
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

    listing_workspace_summary_by_key = {}
    for workspace in listing_workspaces:
        listing_kind = str(workspace.get("listing_kind") or "other")
        workspace_status = str(workspace.get("status") or "other")
        key = (listing_kind, workspace_status)
        listing_workspace_summary_by_key[key] = listing_workspace_summary_by_key.get(key, 0) + 1
    listing_workspace_summary = [
        {
            "listingKind": listing_kind,
            "status": workspace_status,
            "workspaceCount": count,
        }
        for (listing_kind, workspace_status), count in sorted(listing_workspace_summary_by_key.items())
    ]

    latest_source_by_code = {}
    for source in form_sources:
        code = str(source.get("form_code") or "")
        if code and code not in latest_source_by_code:
            latest_source_by_code[code] = source
    brokerage_gate_ready = (
        brokerage.get("txr_all_agents_authorized") is True
        and brokerage.get("txr_authorization_attested_at") is not None
    )
    source_readiness = []
    for form_code in BROKERAGE_TXR_FORM_CODES:
        source = latest_source_by_code.get(form_code) or {}
        status = str(source.get("status") or "not_uploaded")
        source_attested = source.get("authorization_attested") is True
        source_readiness.append({
            "formCode": form_code,
            "sourceRevision": source.get("source_revision"),
            "status": status,
            "sourceAttested": source_attested,
            "brokerageAuthorized": brokerage_gate_ready,
            "readyForRestrictedDraft": brokerage_gate_ready and status == "approved" and source_attested,
            "updatedAt": source.get("updated_at"),
        })

    safe_agents = []
    now = datetime.now(timezone.utc)
    activation_count = 0
    active_access_membership_pending_count = 0
    trials_ending_soon = 0
    for member in members:
        user_id = str(member.get("user_id") or "")
        profile = profile_by_user.get(user_id, {})
        subscription = subscription_by_user.get(user_id, {})
        member_email = str(member.get("email") or profile.get("agent_email") or "").strip().lower()
        invite_accepted = member_email in accepted_invite_emails
        activity = activity_by_user.get(
            user_id,
            {"offerCount": 0, "signedCount": 0, "awaitingCount": 0, "draftCount": 0, "lastOfferAt": None},
        )
        subscription_status = str(subscription.get("status") or "").lower()
        monthly_used = usage_by_user.get(user_id, 0)
        try:
            monthly_limit = max(0, int(subscription.get("packet_limit") or 0))
        except (TypeError, ValueError):
            monthly_limit = 0
        has_active_access = subscription_status in {"active", "trialing", "free_admin"}
        billing_attention = subscription_status in {"past_due", "canceled", "incomplete", "incomplete_expired"}
        membership_status = str(member.get("status") or "pending").lower()
        # A user can have valid platform access while their brokerage seat was
        # never activated (for example, an admin-granted account or a legacy
        # seat). Surface this separately so an administrator can resolve the
        # mismatch deliberately without changing billing.
        if membership_status != "active" and has_active_access:
            engagement = "needs_activation"
            next_action = "Activate brokerage membership"
            activation_count += 1
            active_access_membership_pending_count += 1
        elif invite_accepted and membership_status != "active":
            engagement = "needs_activation"
            next_action = "Finish account activation"
            activation_count += 1
        elif activity["offerCount"] > 0 and billing_attention:
            engagement = "needs_billing"
            next_action = "Fix billing before the next offer"
            activation_count += 1
        elif activity["offerCount"] > 0 and not has_active_access:
            engagement = "needs_subscription"
            next_action = "Review access before the next offer"
            activation_count += 1
        elif activity["offerCount"] == 0 and membership_status == "active":
            engagement = "needs_activation"
            next_action = "Create the first offer"
            activation_count += 1
        else:
            last_offer = _parse_timestamp(activity.get("lastOfferAt"))
            if last_offer and (now - last_offer).days <= 30:
                engagement = "active"
                next_action = "Keep building client offers"
            else:
                engagement = "needs_follow_up"
                next_action = "Follow up on the workspace"
        trial_end = _parse_timestamp(subscription.get("trial_ends_at"))
        if trial_end and now <= trial_end <= now + timedelta(days=14):
            trials_ending_soon += 1
            if engagement != "needs_activation":
                next_action = "Review trial before renewal"
        safe_agents.append(
            {
                "userId": user_id,
                "name": profile.get("agent_name"),
                "email": profile.get("agent_email") or member.get("email"),
                "licenseNumber": profile.get("license_number"),
                "role": member.get("role") or "agent",
                "teamName": team_by_user.get(user_id),
                "membershipStatus": membership_status,
                "inviteAccepted": invite_accepted,
                "txrAgentAuthorized": member.get("txr_agent_authorized") is True,
                "txrAgentAttestedAt": member.get("txr_agent_attested_at"),
                "subscriptionStatus": subscription.get("status"),
                "plan": subscription.get("plan"),
                "trialEndsAt": subscription.get("trial_ends_at"),
                "currentPeriodEnd": subscription.get("current_period_end"),
                "usage": {
                    "billingMonth": billing_month,
                    "used": monthly_used,
                    "limit": monthly_limit,
                    "remaining": max(0, monthly_limit - monthly_used) if monthly_limit else None,
                },
                "activity": activity,
                "engagement": engagement,
                "nextAction": next_action,
            }
        )

    # Team labels are organization-only. The cohort view intentionally keeps
    # buyer, property, offer-term, and document details out of broker reports.
    team_cohorts_by_name = {}
    for agent in safe_agents:
        if (agent.get("role") or "agent") != "agent":
            continue
        team_name = str(agent.get("teamName") or "").strip() or "Unassigned"
        cohort = team_cohorts_by_name.setdefault(
            team_name,
            {
                "teamName": team_name,
                "unassigned": team_name == "Unassigned",
                "agentCount": 0,
                "activeAgentCount": 0,
                "activeAccessCount": 0,
                "needsActivationCount": 0,
                "needsBillingCount": 0,
                "offerCount": 0,
                "signedCount": 0,
            },
        )
        cohort["agentCount"] += 1
        is_active_member = agent.get("membershipStatus") == "active"
        if is_active_member:
            cohort["activeAgentCount"] += 1
        if is_active_member and str(agent.get("subscriptionStatus") or "").lower() in {"active", "trialing", "free_admin"}:
            cohort["activeAccessCount"] += 1
        if agent.get("engagement") in {"needs_activation", "needs_subscription"}:
            cohort["needsActivationCount"] += 1
        if agent.get("engagement") == "needs_billing":
            cohort["needsBillingCount"] += 1
        cohort["offerCount"] += int(agent.get("activity", {}).get("offerCount") or 0)
        cohort["signedCount"] += int(agent.get("activity", {}).get("signedCount") or 0)
    team_cohorts = sorted(
        team_cohorts_by_name.values(),
        key=lambda cohort: (cohort["unassigned"], cohort["teamName"].lower()),
    )

    return {
        "brokerage": brokerage,
        "sourceReadiness": source_readiness,
        "metrics": {
            "memberCount": len(members),
            "activeMemberCount": len([row for row in members if row.get("status") == "active"]),
            "agentSeatCount": len([
                row for row in members
                if row.get("status") == "active" and (row.get("role") or "agent") == "agent"
            ]),
            "agentSeatCap": brokerage.get("user_cap"),
            "teamCount": len({
                str(agent.get("teamName")).strip()
                for agent in safe_agents
                if agent.get("membershipStatus") == "active" and str(agent.get("teamName") or "").strip()
            }),
            "unassignedAgentCount": len([
                agent for agent in safe_agents
                if agent.get("membershipStatus") == "active"
                and (agent.get("role") or "agent") == "agent"
                and not str(agent.get("teamName") or "").strip()
            ]),
            "trialingCount": len([row for row in subscriptions if row.get("status") == "trialing"]),
            "activeSubscriptionCount": len(
                [row for row in subscriptions if row.get("status") in {"active", "trialing"}]
            ),
            "offerCount": len(offers),
            "agentsNeedingSubscription": len([
                agent for agent in safe_agents if agent.get("engagement") == "needs_subscription"
            ]),
            "agentsNeedingBilling": len([
                agent for agent in safe_agents if agent.get("engagement") == "needs_billing"
            ]),
            "signedCount": len(
                [
                    row
                    for row in offers
                    if _offer_status_bucket(row.get("signwell_status") or row.get("status")) == "signed"
                ]
            ),
            "agentsNeedingActivation": activation_count,
            "membersAwaitingActivationWithActiveAccess": active_access_membership_pending_count,
            "agentsNeedingFollowUp": len([
                agent for agent in safe_agents if agent.get("engagement") == "needs_follow_up"
            ]),
            "trialsEndingSoon": trials_ending_soon,
            "pendingInviteCount": len(pending_invites),
            "pendingInvitesExpiringSoon": len(pending_invites_expiring_soon),
            "pendingInvitesExpired": len(pending_invites_expired),
            "pendingInvitesAged": len(pending_invites_aged),
            "inviteTotalCount": len(invite_history),
            "acceptedInviteCount": accepted_invite_count,
            "inviteAcceptanceRate": invite_acceptance_rate,
            "acceptedInviteActiveCount": accepted_invite_active_count,
            "acceptedInviteNeedingActivationCount": accepted_invite_needing_activation_count,
            "acceptedInviteNeedingActivationAgedCount": accepted_invite_needing_activation_aged_count,
            "acceptedInviteActivationRate": accepted_invite_activation_rate,
            "acceptedInviteSubscribedCount": accepted_invite_subscribed_count,
            "acceptedInviteSubscriptionRate": accepted_invite_subscription_rate,
            "usageBillingMonth": billing_month,
            "teamPacketUsage": sum(usage_by_user.values()),
            "teamPacketLimit": sum(
                max(0, int(row.get("packet_limit") or 0))
                for row in subscriptions
                if str(row.get("status") or "").lower() in {"active", "trialing", "free_admin"}
            ),
        },
        "agents": safe_agents,
        "teamCohorts": team_cohorts,
        "listingWorkspaceSummary": listing_workspace_summary,
        "pendingInvites": [
            {
                "id": str(invite.get("id") or ""),
                "email": invite.get("email"),
                "role": invite.get("role") or "agent",
                "status": invite.get("status") or "pending",
                "createdAt": invite.get("created_at"),
                "expiresAt": invite.get("expires_at"),
            }
            for invite in pending_invites
        ],
        "privacy": {
            "buyerDetailsIncluded": False,
            "propertyDetailsIncluded": False,
            "offerTermsIncluded": False,
            "documentContentsIncluded": False,
        },
    }


def _normalized_invite_email(value):
    email = str(value or "").strip().lower()
    if not BROKERAGE_INVITE_EMAIL_RE.fullmatch(email):
        raise ValueError("Enter a valid agent email address.")
    return email


def _normalized_brokerage_team_name(value):
    """Return a compact private roster label, or None when cleared."""
    team_name = " ".join(str(value or "").strip().split())
    if len(team_name) > MAX_BROKERAGE_TEAM_NAME_LENGTH:
        raise ValueError("Keep the team name to 80 characters or fewer.")
    return team_name or None


def _brokerage_agent_seat_cap(brokerage):
    """Return the configured agent-seat cap, or None when the brokerage is uncapped."""
    raw_cap = (brokerage or {}).get("user_cap")
    if raw_cap in (None, ""):
        return None
    try:
        cap = int(raw_cap)
    except (TypeError, ValueError):
        raise RuntimeError("This brokerage has an invalid agent-seat limit.")
    if cap < 0:
        raise RuntimeError("This brokerage has an invalid agent-seat limit.")
    return cap


async def _brokerage_agent_seat_counts(brokerage_id):
    """Count active agent seats and pending agent invitations server-side."""
    active_agents = await _get(
        "hof_brokerage_members?"
        f"brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
        "&role=eq.agent&status=eq.active&select=id&limit=10001"
    )
    pending_agent_invites = await _get(
        "hof_brokerage_invites?"
        f"brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
        "&role=eq.agent&status=eq.pending&select=id&limit=10001"
    )
    return len(active_agents), len(pending_agent_invites)


async def _require_available_agent_seat(brokerage, include_pending):
    """Fail before a new invite or membership would exceed an agent-seat cap."""
    cap = _brokerage_agent_seat_cap(brokerage)
    if cap is None:
        return
    brokerage_id = str((brokerage or {}).get("id") or "")
    if not brokerage_id:
        raise RuntimeError("This brokerage is not configured correctly.")
    active_count, pending_count = await _brokerage_agent_seat_counts(brokerage_id)
    occupied = active_count + (pending_count if include_pending else 0)
    if occupied >= cap:
        raise ValueError(
            f"This brokerage has reached its {cap}-agent seat limit. "
            "Suspend an agent or revoke an unused invitation before adding another."
        )


def _parse_timestamp(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def _brokerage_invite_url(token):
    token = str(token or "").strip()
    if not re.fullmatch(r"[a-f0-9]{32,128}", token):
        raise RuntimeError("The invite link could not be created.")
    return f"{PUBLIC_APP_ORIGIN}/ondemand?invite={urllib.parse.quote(token, safe='')}"


def _invite_html_escape(value):
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


async def _deliver_brokerage_invite_email(email, brokerage, invite_url):
    """Email a broker-created invite without making delivery an access gate."""
    if not RESEND_API_KEY:
        return {"status": "not_configured"}

    brokerage_name = str(
        (brokerage or {}).get("dba_name")
        or (brokerage or {}).get("name")
        or "your brokerage"
    ).strip()
    safe_name = _invite_html_escape(brokerage_name)
    safe_url = _invite_html_escape(invite_url)
    payload = {
        "from": f"HomeOfferFlow <{BROKERAGE_INVITE_FROM_EMAIL}>",
        "to": [email],
        "subject": f"You’re invited to join {brokerage_name} on HomeOfferFlow",
        "text": (
            f"Your broker invited you to join {brokerage_name} on HomeOfferFlow.\n\n"
            f"Accept your invitation: {invite_url}\n\n"
            "Sign in or create your account using this email address. "
            "The invitation is personal and should not be forwarded."
        ),
        "html": (
            '<div style="font-family:Arial,sans-serif;line-height:1.5;color:#172033;">'
            f"<h2>You’re invited to join {safe_name}</h2>"
            "<p>Your broker invited you to connect your HomeOfferFlow account to the brokerage.</p>"
            f'<p><a href="{safe_url}" style="display:inline-block;padding:12px 18px;'
            'border-radius:8px;background:#123047;color:#ffffff;text-decoration:none;font-weight:700;">'
            "Accept invitation</a></p>"
            "<p style=\"font-size:13px;color:#5f6b7a;\">Sign in or create your account using this email address. "
            "This invitation is personal and should not be forwarded.</p>"
            "</div>"
        ),
    }
    if BROKERAGE_INVITE_REPLY_TO:
        payload["reply_to"] = BROKERAGE_INVITE_REPLY_TO

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code >= 300:
            print(f"Brokerage invite email failed: {response.status_code}")
            return {"status": "failed"}
        data = response.json() if response.text else {}
        return {"status": "sent", "emailId": data.get("id")}
    except Exception as exc:
        print(f"Brokerage invite email failed: {str(exc)[:300]}")
        return {"status": "failed"}


async def _create_brokerage_invite(actor, data):
    """Create or return one pending agent-only invite for the broker's own brokerage.

    The token is returned only to the authorized broker who created the invite.
    It never gives the browser direct database access, does not alter billing,
    and acceptance later requires an authenticated account with the same email.
    """
    context = await _brokerage_admin_context(actor)
    if not context:
        raise PermissionError("Brokerage admin access is not enabled for this account.")
    email = _normalized_invite_email(data.get("email"))
    brokerage_id = str(context["brokerage"]["id"])

    active_members = await _get(
        "hof_brokerage_members?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&email=eq.{urllib.parse.quote(email)}&status=eq.active"
        "&select=id&limit=1"
    )
    if active_members:
        raise ValueError("That agent already has active access to this brokerage.")

    pending = await _get(
        "hof_brokerage_invites?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&email=eq.{urllib.parse.quote(email)}&status=eq.pending"
        "&select=id,email,role,status,invite_token,expires_at&limit=1"
    )
    now = datetime.now(timezone.utc)
    if pending:
        invite = pending[0]
        expiry = _parse_timestamp(invite.get("expires_at"))
        if expiry and expiry > now and invite.get("invite_token"):
            invite_url = _brokerage_invite_url(invite["invite_token"])
            return {
                "email": email,
                "expiresAt": invite.get("expires_at"),
                "inviteUrl": invite_url,
                "reused": True,
                "emailDelivery": await _deliver_brokerage_invite_email(
                    email, context["brokerage"], invite_url
                ),
            }
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/hof_brokerage_invites?"
                f"id=eq.{urllib.parse.quote(str(invite['id']))}&status=eq.pending",
                headers={**_headers(), "Prefer": "return=representation"},
                json={"status": "expired"},
            )
        if response.status_code >= 300:
            raise RuntimeError("Could not refresh the expired invite.")

    # Pending invitations reserve seats so a broker cannot create a larger
    # launch cohort than the brokerage plan allows. Reusing an existing invite
    # above does not consume another seat.
    await _require_available_agent_seat(context["brokerage"], include_pending=True)

    record = {
        "brokerage_id": brokerage_id,
        "email": email,
        "role": "agent",
        "status": "pending",
        "invited_by": actor["id"],
    }
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/hof_brokerage_invites",
            headers={**_headers(), "Prefer": "return=representation"},
            json=record,
        )
    if response.status_code not in {200, 201}:
        raise RuntimeError("Could not create the brokerage invite.")
    rows = response.json()
    if not isinstance(rows, list) or not rows or not rows[0].get("invite_token"):
        raise RuntimeError("The invite link could not be created.")
    invite = rows[0]
    invite_url = _brokerage_invite_url(invite["invite_token"])
    return {
        "email": email,
        "expiresAt": invite.get("expires_at"),
        "inviteUrl": invite_url,
        "reused": False,
        "emailDelivery": await _deliver_brokerage_invite_email(
            email, context["brokerage"], invite_url
        ),
    }


async def _revoke_brokerage_invite(actor, data):
    """Revoke one pending agent invite belonging to the caller's brokerage."""
    context = await _brokerage_admin_context(actor)
    if not context:
        raise PermissionError("Brokerage admin access is not enabled for this account.")
    try:
        invite_id = str(uuid.UUID(str(data.get("invite_id") or "")))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid pending brokerage invite.")
    brokerage_id = str(context["brokerage"]["id"])
    invites = await _get(
        "hof_brokerage_invites?"
        f"id=eq.{urllib.parse.quote(invite_id)}"
        f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&role=eq.agent&status=eq.pending&select=id,email,status&limit=1"
    )
    if not invites:
        raise ValueError("That pending brokerage invite is no longer available.")
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_brokerage_invites?"
            f"id=eq.{urllib.parse.quote(invite_id)}&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}&status=eq.pending",
            headers={**_headers(), "Prefer": "return=representation"},
            json={"status": "revoked"},
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not revoke the brokerage invite.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("The brokerage invite was not found after revocation.")
    return {"inviteId": invite_id, "email": rows[0].get("email"), "status": rows[0].get("status") or "revoked"}


def _parse_brokerage_branding_update(data, brokerage_id):
    """Validate only public, brokerage-owned brand presentation fields.

    The browser uploads a logo to the fixed public Storage folder after Storage
    RLS verifies the caller is an active broker admin.  This API then accepts
    only that brokerage's resulting URL, never an arbitrary remote URL.
    """
    updates = {}
    if "brand_color" in data:
        color = str(data.get("brand_color") or "").strip()
        if color and not BROKERAGE_BRAND_COLOR_RE.fullmatch(color):
            raise ValueError("Brand color must use the format #RRGGBB.")
        updates["brand_color"] = color or None
    if "logo_url" in data:
        logo_url = str(data.get("logo_url") or "").strip()
        if logo_url:
            allowed_prefix = (
                f"{SUPABASE_URL}/storage/v1/object/public/"
                f"{BROKERAGE_BRANDING_BUCKET}/{brokerage_id}/"
            )
            if not SUPABASE_URL or not logo_url.startswith(allowed_prefix):
                raise ValueError("Logo must be uploaded through the brokerage branding tool.")
        updates["logo_url"] = logo_url or None
    if not updates:
        raise ValueError("Choose a brand color or upload a logo first.")
    return updates


async def _update_brokerage_branding(actor, data):
    """Let an active broker admin update only their own public branding."""
    context = await _brokerage_admin_context(actor)
    if not context:
        raise PermissionError("Brokerage admin access is not enabled for this account.")
    brokerage_id = str(context["brokerage"]["id"])
    updates = _parse_brokerage_branding_update(data, brokerage_id)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_brokerages?"
            f"id=eq.{urllib.parse.quote(brokerage_id)}",
            headers={**_headers(), "Prefer": "return=representation"},
            json=updates,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not save brokerage branding.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Brokerage branding was not found after saving.")
    brokerage = rows[0]
    return {
        "id": str(brokerage.get("id") or brokerage_id),
        "name": brokerage.get("name"),
        "dbaName": brokerage.get("dba_name"),
        "logoUrl": brokerage.get("logo_url"),
        "brandColor": brokerage.get("brand_color"),
    }


def _parse_brokerage_txr_authorization(data):
    """Validate the broker-admin organization-level TXR/NAR gate."""
    status = str(data.get("status") or "").strip()
    if status not in {"unknown", "all_agents_authorized", "not_all"}:
        raise ValueError("Choose a valid Texas REALTORS® / NAR authorization status.")
    if status == "unknown":
        return False, None
    if data.get("attestation") is not True:
        raise ValueError("The brokerage administrator must attest to this Texas REALTORS® / NAR status.")
    return status == "all_agents_authorized", True


async def _update_brokerage_txr_authorization(actor, data):
    """Record the organization gate for a brokerage admin or platform owner.

    Brokerage admins may attest only for their own brokerage. A HomeOfferFlow
    platform admin may attest for a specific active brokerage by supplying its
    brokerage_id; this keeps brokerage authority scoped while allowing the
    product owner to configure a launch before the broker creates an account.
    """
    context = await _brokerage_admin_context(actor)
    if context:
        brokerage_id = str(context["brokerage"]["id"])
    else:
        if not await _is_platform_admin(actor):
            raise PermissionError("Brokerage admin access is not enabled for this account.")
        brokerage_id = str(data.get("brokerage_id") or "").strip()
        try:
            brokerage_id = str(uuid.UUID(brokerage_id))
        except (TypeError, ValueError, AttributeError):
            raise ValueError("A valid brokerage_id is required for platform-admin authorization.")
        rows = await _get(
            "hof_brokerages?"
            f"id=eq.{urllib.parse.quote(brokerage_id)}"
            "&is_active=eq.true&select=id&limit=1"
        )
        if not rows:
            raise ValueError("That brokerage is not active.")
    authorized, attested = _parse_brokerage_txr_authorization(data)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "txr_all_agents_authorized": authorized,
        "txr_authorization_attested_by": actor["id"] if attested else None,
        "txr_authorization_attested_at": now if attested else None,
        "updated_at": now,
    }
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_brokerages?"
            f"id=eq.{urllib.parse.quote(brokerage_id)}",
            headers={**_headers(), "Prefer": "return=representation"},
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not save the brokerage Texas REALTORS® / NAR authorization status.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("The brokerage authorization status was not found after saving.")
    row = rows[0]
    return {
        "allAgentsAuthorized": row.get("txr_all_agents_authorized") is True,
        "attestedAt": row.get("txr_authorization_attested_at"),
        "attestedBy": row.get("txr_authorization_attested_by"),
    }


def _shared_default_text(value, field, maximum=250):
    value = " ".join(str(value or "").strip().split())
    if len(value) > maximum:
        raise ValueError(f"{field} is too long.")
    return value or None


async def _update_brokerage_shared_defaults(actor, data):
    """Save non-transactional brokerage suggestions for agent opt-in only."""
    context = await _brokerage_admin_context(actor)
    if not context:
        raise PermissionError("Brokerage admin access is not enabled for this account.")
    title_company = _shared_default_text(data.get("default_title_company"), "Title company")
    title_contact = _shared_default_text(data.get("default_title_contact"), "Title contact")
    if not title_company and not title_contact:
        raise ValueError("Enter a title company or escrow contact first.")
    brokerage_id = str(context["brokerage"]["id"])
    payload = {
        "default_title_company": title_company,
        "default_title_contact": title_contact,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_brokerages?"
            f"id=eq.{urllib.parse.quote(brokerage_id)}",
            headers={**_headers(), "Prefer": "return=representation"},
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not save brokerage defaults.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Brokerage defaults were not found after saving.")
    row = rows[0]
    return {
        "defaultTitleCompany": row.get("default_title_company"),
        "defaultTitleContact": row.get("default_title_contact"),
    }


async def _apply_brokerage_shared_defaults(actor):
    """Copy a connected brokerage's title suggestions into the agent's profile.

    This is deliberately opt-in. It does not overwrite a contract, select a
    transaction term, or grant access to a brokerage the agent does not have.
    """
    profiles = await _get(
        "hof_profiles?"
        f"id=eq.{urllib.parse.quote(actor['id'])}"
        "&select=id,brokerage_id&limit=1"
    )
    if not profiles or not profiles[0].get("brokerage_id"):
        raise ValueError("Connect to a brokerage before using brokerage defaults.")
    brokerage_id = str(profiles[0]["brokerage_id"])
    memberships = await _get(
        "hof_brokerage_members?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&user_id=eq.{urllib.parse.quote(actor['id'])}"
        "&status=eq.active&select=id&limit=1"
    )
    if not memberships:
        raise PermissionError("Your active brokerage membership is required to use these defaults.")
    brokerages = await _get(
        "hof_brokerages?"
        f"id=eq.{urllib.parse.quote(brokerage_id)}"
        "&is_active=eq.true&select=default_title_company,default_title_contact&limit=1"
    )
    if not brokerages:
        raise ValueError("Your brokerage defaults are not available.")
    defaults = brokerages[0]
    title_company = defaults.get("default_title_company")
    title_contact = defaults.get("default_title_contact")
    if not title_company and not title_contact:
        raise ValueError("Your brokerage has not set title defaults yet.")
    payload = {
        "preferred_title_company": title_company,
        "preferred_escrow_agent": title_contact or title_company,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    existing = await _get(
        "hof_agent_profiles?"
        f"user_id=eq.{urllib.parse.quote(actor['id'])}&select=user_id&limit=1"
    )
    async with httpx.AsyncClient(timeout=12) as client:
        if existing:
            response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/hof_agent_profiles?"
                f"user_id=eq.{urllib.parse.quote(actor['id'])}",
                headers={**_headers(), "Prefer": "return=representation"},
                json=payload,
            )
        else:
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/hof_agent_profiles",
                headers={**_headers(), "Prefer": "return=representation"},
                json={**payload, "user_id": actor["id"], "agent_email": actor["email"]},
            )
    if response.status_code >= 300:
        raise RuntimeError("Could not apply brokerage defaults to your profile.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Your agent profile was not returned after updating.")
    return {
        "preferredTitleCompany": rows[0].get("preferred_title_company"),
        "preferredEscrowAgent": rows[0].get("preferred_escrow_agent"),
    }


async def _accept_brokerage_invite(actor, data):
    """Attach the signed-in, email-matched agent to one valid broker invite."""
    token = str(data.get("invite_token") or "").strip().lower()
    if not re.fullmatch(r"[a-f0-9]{32,128}", token):
        raise ValueError("This brokerage invite link is invalid.")
    invites = await _get(
        "hof_brokerage_invites?"
        f"invite_token=eq.{urllib.parse.quote(token)}&status=eq.pending"
        "&select=id,brokerage_id,email,role,status,expires_at&limit=1"
    )
    if not invites:
        raise ValueError("This brokerage invite is no longer available.")
    invite = invites[0]
    if _normalized_invite_email(actor.get("email")) != _normalized_invite_email(invite.get("email")):
        raise PermissionError("Sign in with the email address that received this brokerage invite.")
    expiry = _parse_timestamp(invite.get("expires_at"))
    if not expiry or expiry <= datetime.now(timezone.utc):
        async with httpx.AsyncClient(timeout=12) as client:
            await client.patch(
                f"{SUPABASE_URL}/rest/v1/hof_brokerage_invites?"
                f"id=eq.{urllib.parse.quote(str(invite['id']))}&status=eq.pending",
                headers=_headers(), json={"status": "expired"},
            )
        raise ValueError("This brokerage invite has expired. Ask your broker for a new link.")
    if str(invite.get("role") or "agent") != "agent":
        raise PermissionError("This invite does not grant agent access.")

    brokerage_id = str(invite.get("brokerage_id") or "")
    profiles = await _get(
        "hof_profiles?"
        f"id=eq.{urllib.parse.quote(actor['id'])}"
        "&select=id,email,role,brokerage_id,is_brokerage_admin&limit=1"
    )
    profile = profiles[0] if profiles else None
    if profile and profile.get("brokerage_id") and str(profile["brokerage_id"]) != brokerage_id:
        raise PermissionError("This account is already connected to another brokerage. Contact HomeOfferFlow support.")
    if profile and (str(profile.get("role") or "agent") != "agent" or profile.get("is_brokerage_admin")):
        raise PermissionError("Brokerage administrator accounts cannot accept an agent invite.")

    existing_members = await _get(
        "hof_brokerage_members?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&user_id=eq.{urllib.parse.quote(actor['id'])}"
        "&select=id,role,status&limit=1"
    )
    if existing_members and str(existing_members[0].get("role") or "agent") != "agent":
        raise PermissionError("Broker and owner memberships must be managed by HomeOfferFlow support.")
    if existing_members and str(existing_members[0].get("status") or "") == "suspended":
        raise PermissionError("This brokerage membership is suspended. Contact your broker.")

    # An existing active agent does not consume a new seat. A first-time invite
    # acceptance does, so give the broker a clear error before attempting the
    # change. The database trigger supplies the final concurrency-safe guard.
    if not existing_members:
        brokerages = await _get(
            "hof_brokerages?"
            f"id=eq.{urllib.parse.quote(brokerage_id)}"
            "&is_active=eq.true&select=id,user_cap&limit=1"
        )
        if not brokerages:
            raise ValueError("This brokerage is no longer active.")
        await _require_available_agent_seat(brokerages[0], include_pending=False)

    now_iso = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=12) as client:
        if profile:
            profile_response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/hof_profiles?id=eq.{urllib.parse.quote(actor['id'])}",
                headers={**_headers(), "Prefer": "return=representation"},
                json={"brokerage_id": brokerage_id, "updated_at": now_iso},
            )
        else:
            profile_response = await client.post(
                f"{SUPABASE_URL}/rest/v1/hof_profiles",
                headers={**_headers(), "Prefer": "return=representation"},
                json={"id": actor["id"], "email": actor["email"], "role": "agent", "brokerage_id": brokerage_id, "updated_at": now_iso},
            )
        if profile_response.status_code not in {200, 201}:
            raise RuntimeError("Could not connect this account to the brokerage.")

        if existing_members:
            membership_response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/hof_brokerage_members?"
                f"id=eq.{urllib.parse.quote(str(existing_members[0]['id']))}",
                headers={**_headers(), "Prefer": "return=representation"},
                json={"email": actor["email"], "status": "active", "updated_at": now_iso},
            )
        else:
            membership_response = await client.post(
                f"{SUPABASE_URL}/rest/v1/hof_brokerage_members",
                headers={**_headers(), "Prefer": "return=representation"},
                json={"brokerage_id": brokerage_id, "user_id": actor["id"], "email": actor["email"], "role": "agent", "status": "active", "updated_at": now_iso},
            )
        if membership_response.status_code not in {200, 201}:
            raise RuntimeError("Could not activate the brokerage membership.")

        invite_response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_brokerage_invites?"
            f"id=eq.{urllib.parse.quote(str(invite['id']))}&status=eq.pending",
            headers={**_headers(), "Prefer": "return=representation"},
            json={"status": "accepted", "accepted_by": actor["id"], "accepted_at": now_iso},
        )
    if invite_response.status_code >= 300:
        raise RuntimeError("Could not finalize the brokerage invite.")
    return {"brokerageId": brokerage_id, "accepted": True}


async def _set_brokerage_member_status(actor, data):
    """Let a brokerage administrator manage agent membership, never billing.

    This deliberately changes only the brokerage-membership record. A broker
    cannot alter a member's Stripe subscription, account credentials, offers,
    or another broker's role from this endpoint.
    """
    context = await _brokerage_admin_context(actor)
    if not context:
        raise PermissionError("Brokerage admin access is not enabled for this account.")

    target_user_id = str(data.get("user_id") or "").strip()
    try:
        target_user_id = str(uuid.UUID(target_user_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid brokerage member.")
    if target_user_id == str(actor["id"]):
        raise PermissionError("You cannot change your own brokerage-admin membership here.")

    desired_status = str(data.get("membership_status") or "").strip().lower()
    if desired_status not in ALLOWED_BROKERAGE_MEMBER_STATUSES:
        raise ValueError("Choose active or suspended brokerage access.")

    brokerage_id = str(context["brokerage"]["id"])
    members = await _get(
        "hof_brokerage_members?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&user_id=eq.{urllib.parse.quote(target_user_id)}"
        "&select=id,user_id,email,role,status,suspension_reason&limit=1"
    )
    if not members:
        raise ValueError("That agent is not a member of this brokerage.")
    member = members[0]
    if str(member.get("role") or "agent") != "agent":
        raise PermissionError("Broker and owner memberships must be managed by HomeOfferFlow support.")
    if str(member.get("status") or "") == desired_status:
        return {"userId": target_user_id, "membershipStatus": desired_status, "changed": False}

    membership_update = {
        "status": desired_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    # Suspension invalidates the prior point-of-use attestation. If the agent
    # is later restored, they must attest again before using a restricted form.
    if desired_status == "suspended":
        membership_update.update({
            "suspension_reason": "manual",
            "txr_agent_authorized": False,
            "txr_agent_attested_by": None,
            "txr_agent_attested_at": None,
        })
    elif desired_status == "active":
        membership_update["suspension_reason"] = None

    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_brokerage_members?"
            f"id=eq.{urllib.parse.quote(str(member['id']))}"
            f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}",
            headers={**_headers(), "Prefer": "return=representation"},
            json=membership_update,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not update this brokerage membership.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Brokerage membership was not found after updating.")
    return {"userId": target_user_id, "membershipStatus": rows[0].get("status") or desired_status, "changed": True}


async def _set_brokerage_member_team(actor, data):
    """Set a private roster label without changing access or account state."""
    context = await _brokerage_admin_context(actor)
    if not context:
        raise PermissionError("Brokerage admin access is not enabled for this account.")

    target_user_id = str(data.get("user_id") or "").strip()
    try:
        target_user_id = str(uuid.UUID(target_user_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid brokerage member.")
    team_name = _normalized_brokerage_team_name(data.get("team_name"))
    brokerage_id = str(context["brokerage"]["id"])
    members = await _get(
        "hof_brokerage_members?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&user_id=eq.{urllib.parse.quote(target_user_id)}"
        "&select=id,user_id,role,status&limit=1"
    )
    if not members:
        raise ValueError("That agent is not a member of this brokerage.")
    if str(members[0].get("role") or "agent") != "agent":
        raise PermissionError("Broker and owner team assignments must be managed by HomeOfferFlow support.")

    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_profiles?"
            f"id=eq.{urllib.parse.quote(target_user_id)}"
            f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}",
            headers={**_headers(), "Prefer": "return=representation"},
            json={"team_name": team_name, "updated_at": datetime.now(timezone.utc).isoformat()},
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not update this private team label.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise ValueError("That agent profile is not connected to this brokerage.")
    return {"userId": target_user_id, "teamName": rows[0].get("team_name"), "changed": True}


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


def _parse_seller_lead_update(data):
    lead_id = str(data.get("seller_lead_id") or "").strip()
    status = str(data.get("status") or "").strip().lower()
    try:
        lead_id = str(uuid.UUID(lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("A valid seller lead ID is required.")
    if status not in ALLOWED_SELLER_LEAD_STATUSES:
        raise ValueError("Choose a valid seller lead status.")
    return lead_id, status


async def _update_seller_lead(lead_id, status):
    payload = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_seller_leads?id=eq.{lead_id}",
            headers={**_headers(), "Prefer": "return=representation"},
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not update the seller lead.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise ValueError("Seller lead was not found.")
    return rows[0]


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


async def _create_partner_onboarding_link(data):
    lead_id = str(data.get("lead_id") or "").strip()
    try:
        lead_id = str(uuid.UUID(lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("A valid partner lead ID is required.")
    rows = await _get(
        "hof_partner_leads?"
        f"id=eq.{urllib.parse.quote(lead_id)}&select=id,payment_status,status&limit=1"
    )
    if not rows or str(rows[0].get("payment_status") or "") != "paid" or str(rows[0].get("status") or "") in {"declined", "waitlist"}:
        raise PermissionError("Only an eligible paid partner application can receive onboarding access.")
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    payload = {
        "onboarding_token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest(),
        "onboarding_token_expires_at": (now + timedelta(days=14)).isoformat(),
        "onboarding_status": "in_progress",
        "updated_at": now.isoformat(),
    }
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?id=eq.{urllib.parse.quote(lead_id)}",
            headers={**_headers(), "Prefer": "return=representation"},
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not create partner onboarding access.")
    saved = response.json()
    if not isinstance(saved, list) or not saved:
        raise ValueError("Partner lead was not found.")
    return {"onboardingUrl": f"{PUBLIC_APP_ORIGIN}/?partner_onboarding={urllib.parse.quote(token, safe='')}", "expiresAt": payload["onboarding_token_expires_at"]}


async def _email_partner_onboarding_link(data):
    """Create a fresh setup link only when a platform admin explicitly sends it."""
    lead_id = str(data.get("lead_id") or "").strip()
    try:
        lead_id = str(uuid.UUID(lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("A valid partner lead ID is required.")
    if not RESEND_API_KEY:
        raise RuntimeError("Partner setup email is not configured.")

    rows = await _get(
        "hof_partner_leads?"
        f"id=eq.{urllib.parse.quote(lead_id)}&select=id,company_name,contact_email,payment_status,status&limit=1"
    )
    if not rows or str(rows[0].get("payment_status") or "") != "paid" or str(rows[0].get("status") or "") in {"declined", "waitlist"}:
        raise PermissionError("Only an eligible paid partner application can receive onboarding access.")
    lead = rows[0]
    email = str(lead.get("contact_email") or "").strip()
    if not BROKERAGE_INVITE_EMAIL_RE.fullmatch(email):
        raise ValueError("This paid partner application has no valid contact email.")

    onboarding = await _create_partner_onboarding_link({"lead_id": lead_id})
    company_name = str(lead.get("company_name") or "your company").strip()
    safe_company = _invite_html_escape(company_name)
    safe_url = _invite_html_escape(onboarding["onboardingUrl"])
    payload = {
        "from": PARTNER_ONBOARDING_FROM_EMAIL,
        "to": [email],
        "subject": "Complete your HomeOfferFlow partner setup",
        "text": (
            f"Thanks for partnering with HomeOfferFlow. Complete your secure setup within 14 days: {onboarding['onboardingUrl']}\n\n"
            "This prepares your creative for review only. It does not activate advertising or replace the required written placement agreement."
        ),
        "html": (
            '<div style="font-family:Arial,sans-serif;line-height:1.5;color:#172033;">'
            f"<h2>Complete {safe_company}'s HomeOfferFlow setup</h2>"
            "<p>Use this secure setup link to provide your market, website, logo, and call to action.</p>"
            f'<p><a href="{safe_url}" style="display:inline-block;padding:12px 18px;border-radius:8px;background:#123047;color:#ffffff;text-decoration:none;font-weight:700;">Complete partner setup</a></p>'
            "<p style=\"font-size:13px;color:#5f6b7a;\">This link expires in 14 days. Setup prepares creative for review only; it does not activate advertising or replace the required written placement agreement.</p>"
            "</div>"
        ),
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                json=payload,
            )
        if response.status_code >= 300:
            raise RuntimeError("Partner setup email could not be delivered.")
    except RuntimeError:
        raise
    except Exception as exc:
        print(f"Partner setup email failed: {str(exc)[:300]}")
        raise RuntimeError("Partner setup email could not be delivered.")
    return {"expiresAt": onboarding["expiresAt"], "delivery": "sent"}


def _clean_text(value, maximum):
    value = " ".join(str(value or "").strip().split())
    return value[:maximum] if value else None


def _normalized_partner_market(value):
    """Match the database's Premier-market uniqueness normalization."""
    return " ".join(str(value or "").strip().split()).casefold()


def _parse_partner_placement(data):
    source_lead_id = str(data.get("partner_lead_id") or "").strip()
    try:
        source_lead_id = str(uuid.UUID(source_lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid paid partner application.")
    placement_tier = _clean_text(data.get("placement_tier"), 80)
    if placement_tier not in ALLOWED_PARTNER_PLACEMENT_TIERS:
        raise ValueError("Choose a valid placement tier.")
    try:
        monthly_fee = float(data.get("monthly_fee")) if data.get("monthly_fee") not in (None, "") else None
    except (TypeError, ValueError):
        raise ValueError("Monthly fee must be a number.")
    if monthly_fee is not None and (monthly_fee < 0 or monthly_fee > 100000):
        raise ValueError("Monthly fee is outside the allowed range.")
    return {
        "source_lead_id": source_lead_id,
        "placement_tier": placement_tier,
        "monthly_fee": monthly_fee,
    }


async def _paid_partner_lead_for_placement(lead_id):
    rows = await _get(
        "hof_partner_leads?"
        f"id=eq.{urllib.parse.quote(lead_id)}&"
        "select=id,company_name,contact_name,contact_email,contact_phone,website_url,partner_type,market_area,status,payment_status,onboarding_status,onboarding_website_url,onboarding_logo_url,onboarding_market_area,partner_agreement_status,partner_agreement_signed_at&limit=1"
    )
    if not rows:
        raise ValueError("The selected partner application was not found.")
    lead = rows[0]
    if str(lead.get("payment_status") or "") != "paid":
        raise PermissionError("Only a paid partner application can activate a public placement.")
    if str(lead.get("status") or "") in {"declined", "waitlist"}:
        raise PermissionError("This partner application is not eligible for a public placement.")
    if str(lead.get("onboarding_status") or "").lower() not in {"complete", "completed"}:
        raise PermissionError("Complete the secure partner onboarding before activating a public placement.")
    if str(lead.get("partner_agreement_status") or "").lower() != "signed" or not lead.get("partner_agreement_signed_at"):
        raise PermissionError("A completed HomeOfferFlow Partner Marketplace Agreement is required before activating a public placement.")
    partner_type = str(lead.get("partner_type") or "").strip()
    if partner_type not in ALLOWED_PARTNER_TYPES:
        raise ValueError("The selected partner application has an unsupported category.")
    if not _clean_text(lead.get("company_name"), 250) or not _clean_text(lead.get("market_area"), 300):
        raise ValueError("The selected partner application is missing its company name or market area.")
    return lead


async def _create_platform_partner_placement(payload):
    lead = await _paid_partner_lead_for_placement(payload["source_lead_id"])
    existing = await _get(
        "hof_partner_placements?"
        f"source_lead_id=eq.{urllib.parse.quote(payload['source_lead_id'])}&"
        "is_active=is.true&select=id&limit=1"
    )
    if existing:
        raise ValueError("This paid partner application already has an active placement.")
    if payload["placement_tier"] == "exclusive_market":
        # The partial unique index is the authoritative race-safe guard. This
        # preflight provides an immediate, plain-language admin response before
        # attempting the insert when another Premier placement has already
        # reserved the same category and normalized market.
        active_premier = await _get(
            "hof_partner_placements?"
            f"partner_type=eq.{urllib.parse.quote(str(lead['partner_type']))}&"
            "placement_tier=eq.exclusive_market&is_active=is.true&"
            "select=id,market_area&limit=100"
        )
        requested_market = _normalized_partner_market(
            lead.get("onboarding_market_area") or lead.get("market_area")
        )
        if any(_normalized_partner_market(row.get("market_area")) == requested_market for row in active_premier):
            raise ValueError(
                "An active Premier Partner placement already reserves this category and market. "
                "Choose a different market or tier."
            )
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "brokerage_id": None,
        "source_lead_id": payload["source_lead_id"],
        "partner_name": _clean_text(lead.get("company_name"), 250),
        "partner_type": str(lead.get("partner_type") or "").strip(),
        "contact_name": _clean_text(lead.get("contact_name"), 250),
        "contact_email": _clean_text(lead.get("contact_email"), 254),
        "contact_phone": _clean_text(lead.get("contact_phone"), 80),
        "website_url": _clean_text(lead.get("onboarding_website_url") or lead.get("website_url"), 500),
        "logo_url": _clean_text(lead.get("onboarding_logo_url"), 500),
        "market_area": _clean_text(lead.get("onboarding_market_area") or lead.get("market_area"), 300),
        "placement_tier": payload["placement_tier"],
        "monthly_fee": payload["monthly_fee"],
        "agreement_confirmed_at": now,
        "activated_at": now,
        "is_active": True,
    }
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/hof_partner_placements",
            headers={**_headers(), "Prefer": "return=representation"},
            json=record,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not create the partner placement.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Partner placement was not returned after saving.")
    return rows[0]


def _partner_agreement_pdf(lead):
    """Render the commercial agreement sent to an eligible paid partner.

    This is intentionally a HomeOfferFlow-authored commercial agreement, not a
    TREC or Texas REALTORS form. SignWell appends the signer page, avoiding
    fragile coordinate placement in the agreement body.
    """
    company = _clean_text(lead.get("company_name"), 250) or "Partner"
    contact = _clean_text(lead.get("contact_name"), 250) or "Authorized representative"
    market = _clean_text(lead.get("onboarding_market_area") or lead.get("market_area"), 300) or "the agreed market"
    category = (_clean_text(lead.get("partner_type"), 100) or "partner service").replace("_", " ")
    tier = (_clean_text(lead.get("preferred_model"), 100) or "paid partner").replace("_", " ")
    paragraphs = [
        ("HOME OFFER FLOW PARTNER MARKETPLACE AGREEMENT", True),
        ("This Agreement is between BrewBQ Investments LLC, a Texas limited liability company doing business as HomeOfferFlow (HomeOfferFlow), and the Partner identified below.", False),
        (f"Partner: {company} | Authorized representative: {contact}", False),
        (f"Category: {category} | Market: {market} | Selected commercial tier: {tier}", False),
        ("1. PURPOSE AND ORDER FORM. This Agreement governs Partner's paid digital marketplace placement with HomeOfferFlow. The checkout receipt and any signed Order Form identify the applicable fee, initial pilot or term, billing interval, placement tier, market, and any expressly agreed exclusivity. Payment or onboarding alone does not create a right to publication.", False),
        ("2. PLACEMENT; EDITORIAL CONTROL. HomeOfferFlow may display approved company, category, market, logo, website, and call-to-action information in its marketplace. HomeOfferFlow may format, label, defer, suspend, remove, or decline Content and a Placement to protect users, comply with law, maintain a neutral directory, or enforce this Agreement. No impressions, clicks, leads, transactions, revenue, ranking, availability, referral, recommendation, or exclusivity is guaranteed unless a signed Order Form expressly says otherwise.", False),
        ("3. SPONSORED DISCLOSURE AND NEUTRAL CHOICE. HomeOfferFlow may label the Placement Sponsored, Paid Partner, Advertisement, or similarly. Partner will not obscure that disclosure or state or imply that HomeOfferFlow has independently selected, endorsed, guaranteed, ranked, or recommended Partner. Users may choose any qualified provider; this Agreement creates no agency, fiduciary, brokerage, referral, or preferred-provider relationship with users.", False),
        ("4. PARTNER CONTENT AND COMPLIANCE. Partner represents that all submitted Content, licenses, qualifications, testimonials, offers, prices, websites, trademarks, and claims are accurate, current, substantiated, lawful, and non-misleading. Partner is solely responsible for its services, staff, professional licenses, insurance, permits, advertising, communications, privacy practices, taxes, and all legal or professional rules applicable to its business. Partner will promptly report a material change and will not submit unlawful, discriminatory, infringing, deceptive, privacy-invasive, or unsubstantiated Content.", False),
        ("5. NO PROFESSIONAL SERVICES BY HOMEOFFERFLOW. HomeOfferFlow is not providing real-estate brokerage, lending, title, appraisal, insurance, inspection, construction, legal, tax, or other regulated professional services through this Agreement. Partner may not state or imply otherwise.", False),
        ("6. CONTENT LICENSE. Partner grants HomeOfferFlow a non-exclusive, worldwide, royalty-free license during the Term to host, reproduce, technically format, make accessible, display, distribute, and link to approved Partner Content solely to operate, promote, measure, and improve the Placement. Partner retains its pre-existing Content rights; HomeOfferFlow retains the platform, marketplace, brands, aggregate analytics, and related intellectual property.", False),
        ("7. FEES, RENEWAL, AND CANCELLATION. Fees and renewal terms shown in the applicable checkout or signed Order Form control. Stripe's successful payment records control payment processing. HomeOfferFlow may suspend or remove a Placement for failed, reversed, disputed, expired, or overdue payment. Unless the Order Form says otherwise, either Party may cancel a month-to-month Placement on 30 days' written notice; cancellation stops future renewal after the paid period and does not create a pro-rata refund except as required by law or expressly stated in the Order Form.", False),
        ("8. DATA AND COMMUNICATIONS. Each Party is an independent controller of information it collects. This Agreement gives Partner no right to HomeOfferFlow user, offer, transaction, or account data. HomeOfferFlow may provide aggregate placement metrics. Partner will comply with applicable consent, opt-out, email, text, telemarketing, privacy, and advertising law and will not market to a HomeOfferFlow user merely because the user viewed or clicked a Placement.", False),
        ("9. INDEMNITY. Partner will defend, indemnify, and hold harmless HomeOfferFlow and its personnel from third-party claims, losses, liabilities, costs, and reasonable attorney fees arising from Partner Content, services, advertising, communications, data practices, licenses, professional conduct, breach of this Agreement, or an allegation that Partner Content is unlawful, deceptive, or infringes rights. HomeOfferFlow will promptly notify Partner of a claim and reasonably cooperate at Partner's expense; no settlement may impose non-monetary obligations on HomeOfferFlow without its consent.", False),
        ("10. DISCLAIMERS AND LIABILITY. EXCEPT FOR EXPRESS TERMS HERE, THE PLATFORM AND PLACEMENT ARE PROVIDED AS IS. TO THE MAXIMUM EXTENT PERMITTED BY LAW, NEITHER PARTY IS LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES OR LOST PROFITS, REVENUE, DATA, OR BUSINESS. EXCEPT FOR PARTNER'S PAYMENT AND INDEMNITY OBLIGATIONS, FRAUD, WILLFUL MISCONDUCT, OR LIABILITY THAT CANNOT BE LIMITED BY LAW, EACH PARTY'S TOTAL LIABILITY WILL NOT EXCEED THE FEES PAID OR PAYABLE UNDER THE APPLICABLE ORDER FORM IN THE TWELVE MONTHS BEFORE THE EVENT.", False),
        ("11. GENERAL. The Parties are independent contractors. Texas law governs, and for disputes not subject to arbitration or small claims, the Parties consent to the courts in the Texas county where BrewBQ Investments LLC maintains its principal place of business, unless nonwaivable law requires another venue. Notices must be written and sent to the Order Form addresses. This Agreement and the Order Form are the entire agreement on this subject and may be changed only in a writing accepted by both Parties. Electronic records and signatures are intended to be effective to the extent permitted by law.", False),
        ("By signing electronically, Partner's authorized representative confirms authority to bind Partner and accepts this Agreement. The Agreement becomes effective when HomeOfferFlow accepts it electronically, including by sending this request, recording the completed agreement, or activating an approved Placement. This signed agreement is required before any public Placement can be activated.", False),
        ("DRAFTING NOTICE: This commercial agreement must receive final Texas counsel approval before its first production use. It is not a Texas REALTORS or TREC form.", True),
    ]
    buffer = BytesIO()
    pdf = Canvas(buffer, pagesize=letter)
    width, height = letter
    left, right, top, bottom = 54, 54, height - 54, 54
    y = top
    def page_header():
        nonlocal y
        pdf.setFont("Helvetica", 8)
        pdf.setFillColorRGB(0.28, 0.32, 0.39)
        pdf.drawRightString(width - right, height - 34, "HomeOfferFlow Partner Marketplace Agreement")
        pdf.setFillColorRGB(0, 0, 0)
        y = height - 54
    def wrapped(text, font, size, leading):
        words = text.split()
        lines, line = [], ""
        available = width - left - right
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and stringWidth(candidate, font, size) > available:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines
    page_header()
    for text, emphasized in paragraphs:
        font = "Helvetica-Bold" if emphasized else "Helvetica"
        size = 11 if emphasized else 9
        leading = 14 if emphasized else 12
        for line in wrapped(text, font, size, leading):
            if y - leading < bottom:
                pdf.showPage()
                page_header()
            pdf.setFont(font, size)
            pdf.drawString(left, y, line)
            y -= leading
        y -= 7
    pdf.save()
    return buffer.getvalue()


async def _send_partner_agreement_for_signature(data):
    if not PARTNER_AGREEMENT_SIGNING_ENABLED:
        raise PermissionError("Partner agreement signing is not released. Complete Texas counsel review and the final HomeOfferFlow entity and venue details before enabling it.")
    if not SIGNWELL_ENABLED or not SIGNWELL_API_KEY:
        raise RuntimeError("SignWell signing is not configured for this environment.")
    lead_id = str(data.get("partner_lead_id") or "").strip()
    try:
        lead_id = str(uuid.UUID(lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid paid partner application.")
    rows = await _get(
        "hof_partner_leads?"
        f"id=eq.{urllib.parse.quote(lead_id)}&"
        "select=id,company_name,contact_name,contact_email,partner_type,market_area,preferred_model,status,payment_status,onboarding_status,onboarding_market_area,partner_agreement_status,partner_agreement_signwell_document_id&limit=1"
    )
    if not rows:
        raise ValueError("The selected partner application was not found.")
    lead = rows[0]
    if str(lead.get("payment_status") or "").lower() != "paid":
        raise PermissionError("Only a paid partner can receive the commercial agreement.")
    if str(lead.get("status") or "").lower() in {"declined", "waitlist"}:
        raise PermissionError("This partner application is not eligible for an agreement.")
    if str(lead.get("onboarding_status") or "").lower() not in {"complete", "completed"}:
        raise PermissionError("Complete secure partner onboarding before sending the commercial agreement.")
    if not _valid_email(str(lead.get("contact_email") or "")):
        raise ValueError("This partner application has no valid signing email.")
    if str(lead.get("partner_agreement_status") or "") == "signed":
        raise ValueError("This partner already has a completed commercial agreement.")
    if lead.get("partner_agreement_signwell_document_id") and str(lead.get("partner_agreement_status") or "") == "sent":
        raise ValueError("A commercial agreement is already awaiting this partner's signature.")
    agreement_pdf = _partner_agreement_pdf(lead)
    payload = {
        "test_mode": PARTNER_AGREEMENT_SIGNWELL_TEST_MODE,
        "draft": False,
        "reminders": True,
        "embedded_signing": False,
        "with_signature_page": True,
        "custom_requester_name": "HomeOfferFlow",
        "name": f"HomeOfferFlow Partner Marketplace Agreement — {str(lead['id'])[:8]}",
        "subject": "HomeOfferFlow Partner Marketplace Agreement for signature",
        "message": "Please review and sign the HomeOfferFlow Partner Marketplace Agreement. A completed PDF will be sent to you and HomeOfferFlow support. This agreement does not activate a public placement until HomeOfferFlow reviews the completed record.",
        "recipients": [{"id": "1", "name": str(lead.get("contact_name") or "Partner"), "email": str(lead["contact_email"])}],
        "copied_contacts": [{"name": "HomeOfferFlow Support", "email": PARTNER_AGREEMENT_COPY_EMAIL}],
        "files": [{"name": "HomeOfferFlow_Partner_Marketplace_Agreement.pdf", "file_base64": base64.b64encode(agreement_pdf).decode("ascii")}],
        "metadata": {"source": "HomeOfferFlow", "partner_lead_id": lead_id, "agreement_type": "partner_marketplace"},
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post("https://www.signwell.com/api/v1/documents", headers={"X-Api-Key": SIGNWELL_API_KEY, "Content-Type": "application/json"}, json=payload)
    if response.status_code not in {200, 201, 202}:
        raise RuntimeError(f"SignWell rejected the commercial agreement: HTTP {response.status_code}.")
    result = response.json()
    document_id = str(result.get("id") or result.get("document_id") or "").strip()
    if not document_id:
        raise RuntimeError("SignWell did not return a document id.")
    now = datetime.now(timezone.utc).isoformat()
    await _patch("hof_partner_leads", f"id=eq.{urllib.parse.quote(lead_id)}", {"partner_agreement_status": "sent", "partner_agreement_signwell_document_id": document_id, "partner_agreement_sent_at": now, "updated_at": now})
    return {"documentId": document_id, "status": result.get("status") or "sent", "testMode": PARTNER_AGREEMENT_SIGNWELL_TEST_MODE, "copiedTo": PARTNER_AGREEMENT_COPY_EMAIL}


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
    signer_plan = str(data.get("signerPlan") or "").strip()
    if signer_plan not in {"clients_and_associate", "clients_and_broker"}:
        raise ValueError("Choose an authorized broker or broker-associate signer for the TXR-1507 agreement.")
    if data.get("formUseAttested") is not True:
        raise ValueError("Confirm that you are a current Texas REALTORS® / NAR member (or otherwise individually authorized) and are currently authorized to use this TXR form for your brokerage.")
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
            "signer_plan": signer_plan,
            "form_use_attested": True,
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
    signer_plan = str(data.get("signerPlan") or "").strip()
    if signer_plan not in {"clients_and_associate", "clients_and_broker"}:
        raise ValueError("Choose an authorized broker or broker-associate signer for the TXR-1501 agreement.")
    if data.get("formUseAttested") is not True:
        raise ValueError("Confirm that you are a current Texas REALTORS® / NAR member (or otherwise individually authorized) and are currently authorized to use this TXR form for your brokerage.")
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
            "signer_plan": signer_plan,
            "form_use_attested": True,
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
    signer_plan = str(data.get("signerPlan") or "").strip()
    if signer_plan not in {"associate_and_clients", "broker_and_clients"}:
        raise ValueError("Choose whether the broker or associate will acknowledge TXR-1508.")
    if data.get("formUseAttested") is not True:
        raise ValueError("Confirm that you are a current Texas REALTORS® / NAR member (or otherwise individually authorized) and are currently authorized to use this TXR form for your brokerage.")
    return {
        "form_source_id": form_source_id,
        "client_names": client_names,
        "agreement_data": {
            "property_address": property_address,
            "other_broker_agreement": other_broker_agreement,
            "unrepresented_acknowledgment": True,
            "signer_plan": signer_plan,
            "form_use_attested": True,
        },
    }


def _parse_txr_1506_draft(data):
    """Validate a private general-information notice acknowledgement draft.

    The notice may be used with buyers, tenants, landlords, or sellers. It
    does not establish representation and remains draft-only until the
    brokerage approves a source-specific acknowledgment/signing workflow.
    """
    if data.get("formCode") != TXR_1506_FORM_CODE:
        raise ValueError("Only TXR-1506 is available through this action.")
    client_names = _agreement_clients(data)
    form_source_id = _agreement_text(data.get("formSourceId"), "Approved TXR-1506 source", 80)
    try:
        form_source_id = str(uuid.UUID(form_source_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose an approved TXR-1506 source from your brokerage.")
    consumer_role = str(data.get("consumerRole") or "").strip()
    if consumer_role not in {"buyer", "tenant", "seller", "landlord", "other"}:
        raise ValueError("Choose the consumer's transaction role.")
    additional_notice = " ".join(str(data.get("additionalNotice") or "").strip().split())
    if len(additional_notice) > 1000:
        raise ValueError("Additional notice is too long.")
    if data.get("noticeAcknowledgment") is not True:
        raise ValueError("Confirm that the consumer will review and acknowledge the notice.")
    signer_plan = str(data.get("signerPlan") or "").strip()
    if signer_plan not in {"consumers_and_associate", "consumers_and_broker"}:
        raise ValueError("Choose an authorized broker or broker-associate signer for the TXR-1506 notice.")
    if data.get("formUseAttested") is not True:
        raise ValueError("Confirm that you are a current Texas REALTORS® / NAR member (or otherwise individually authorized) and are currently authorized to use this TXR form for your brokerage.")
    return {
        "form_source_id": form_source_id,
        "client_names": client_names,
        "agreement_data": {
            "consumer_role": consumer_role,
            "additional_notice": additional_notice,
            "notice_acknowledgment": True,
            "signer_plan": signer_plan,
            "form_use_attested": True,
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


async def _brokerage_form_sources_payload(user, approved_only=False):
    """Return sanitized source metadata through the server, never raw table access.

    The source table contains private storage locators and upload fingerprints.
    Agents only need to know whether an approved, attested revision exists;
    brokerage administrators may see the private audit metadata in their own
    dashboard. Neither response ever exposes a PDF URL or storage path.
    """
    if approved_only:
        brokerage_id = await _active_brokerage_member(user)
        rows = await _get_optional(
            "hof_brokerage_form_sources?"
            f"brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
            "&status=eq.approved&authorization_attested=is.true"
            "&select=id,form_code,source_revision,status,authorization_attested,updated_at"
            "&order=updated_at.desc&limit=500"
        )
        return {"sources": rows}

    context = await _brokerage_admin_context(user)
    if not context:
        raise PermissionError("Brokerage admin access is not enabled for this account.")
    brokerage_id = str(context["brokerage"]["id"])
    rows = await _get_optional(
        "hof_brokerage_form_sources?"
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&status=neq.retired"
        "&select=id,form_code,source_revision,status,original_filename,source_sha256,updated_at"
        "&order=updated_at.desc&limit=500"
    )
    return {"sources": rows}


async def _require_brokerage_txr_authorization(brokerage_id):
    """Require the brokerage administrator's organization-level TXR gate.

    A brokerage attestation is not inferred from a license number and does not
    replace the agent's point-of-use checkbox. It is the server-side switch
    that keeps restricted Texas REALTORS® source workflows disabled until the
    brokerage has affirmatively confirmed that its participating agents are
    authorized members/users.
    """
    rows = await _get(
        "hof_brokerages?"
        f"id=eq.{urllib.parse.quote(str(brokerage_id))}"
        "&is_active=eq.true&txr_all_agents_authorized=is.true"
        "&txr_authorization_attested_by=not.is.null"
        "&txr_authorization_attested_at=not.is.null"
        "&select=id&limit=1"
    )
    if not rows:
        raise PermissionError(
            "Your brokerage must first confirm that its participating agents are authorized Texas REALTORS® / NAR users."
        )


async def _prepare_seller_disclosure_draft_record(user, data):
    """Validate an agent-owned seller disclosure draft, never a sendable packet."""
    draft = seller_disclosure_draft.parse_seller_disclosure_draft(data)
    brokerage_id = await _active_brokerage_member(user)
    if draft.get("listing_workspace_id"):
        workspace_rows = await _get(
            "hof_listing_workspaces?"
            f"id=eq.{urllib.parse.quote(str(draft['listing_workspace_id']))}"
            f"&agent_user_id=eq.{urllib.parse.quote(user['id'])}"
            f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
            "&select=id&limit=1"
        )
        if not workspace_rows:
            raise PermissionError("That private listing workspace is unavailable to this agent.")
    source_rows = await _get(
        "hof_brokerage_form_sources?"
        f"id=eq.{urllib.parse.quote(draft['disclosure_source_id'])}"
        f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
        f"&form_code=eq.{TREC_55_1_FORM_CODE}"
        "&status=eq.approved&authorization_attested=is.true"
        "&select=id,source_revision&limit=1"
    )
    if not source_rows:
        raise ValueError("Choose an approved TREC-55-1 source from your brokerage.")
    water_rows = []
    if draft.get("water_source_id"):
        water_rows = await _get(
            "hof_brokerage_form_sources?"
            f"id=eq.{urllib.parse.quote(draft['water_source_id'])}"
            f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
            f"&form_code=eq.{TREC_61_0_FORM_CODE}"
            "&status=eq.approved&authorization_attested=is.true"
            "&select=id,source_revision&limit=1"
        )
        if not water_rows:
            raise ValueError("Choose an approved TREC-61-0 source from your brokerage.")
    record = {
        "brokerage_id": brokerage_id,
        "agent_user_id": user["id"],
        "listing_workspace_id": draft.get("listing_workspace_id"),
        "disclosure_source_id": source_rows[0]["id"],
        "water_source_id": water_rows[0]["id"] if water_rows else None,
        "disclosure_source_revision": source_rows[0]["source_revision"],
        "water_source_revision": water_rows[0]["source_revision"] if water_rows else None,
        "status": "draft",
        "property_address": draft["property_address"],
        "seller_names": draft["seller_names"],
        "buyer_names": draft["buyer_names"],
        "response_data": draft["response_data"],
        "water_rights_data": draft["water_rights_data"],
        "seller_review_attested": False,
    }
    return brokerage_id, record


async def _create_seller_disclosure_draft(user, data):
    brokerage_id, record = await _prepare_seller_disclosure_draft_record(user, data)
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/hof_seller_disclosure_drafts",
            headers={**_headers(), "Prefer": "return=representation"},
            json=record,
        )
    if response.status_code not in {200, 201}:
        raise RuntimeError("Could not save the seller disclosure draft.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Seller disclosure draft was not returned after saving.")
    return rows[0]


async def _update_seller_disclosure_draft(user, data):
    """Update an existing agent-owned draft without enabling seller sending."""
    draft_id = str(data.get("draftId") or "").strip()
    try:
        draft_uuid = str(uuid.UUID(draft_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid seller disclosure draft.")
    brokerage_id, record = await _prepare_seller_disclosure_draft_record(user, data)
    existing = await _get(
        "hof_seller_disclosure_drafts?"
        f"id=eq.{urllib.parse.quote(draft_uuid)}"
        f"&agent_user_id=eq.{urllib.parse.quote(user['id'])}"
        f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
        "&status=eq.draft&select=id&limit=1"
    )
    if not existing:
        raise PermissionError("That private seller disclosure draft is unavailable.")
    record["updated_at"] = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_seller_disclosure_drafts?id=eq.{urllib.parse.quote(draft_uuid)}"
            f"&agent_user_id=eq.{urllib.parse.quote(user['id'])}"
            f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}&status=eq.draft",
            headers={**_headers(), "Prefer": "return=representation"},
            json=record,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not update the seller disclosure draft.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Seller disclosure draft was not returned after updating.")
    return rows[0]


async def _record_agent_txr_attestation(user, brokerage_id):
    """Record the authenticated agent's point-of-use TXR/NAR attestation.

    The browser checkbox is required by each restricted-form parser. This
    server-authored membership record makes the attestation auditable without
    trusting a client-supplied user id or inferring membership from a license.
    """
    now = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_brokerage_members?"
            f"brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
            f"&user_id=eq.{urllib.parse.quote(user['id'])}&status=eq.active",
            headers={**_headers(), "Prefer": "return=representation"},
            json={
                "txr_agent_authorized": True,
                "txr_agent_attested_by": user["id"],
                "txr_agent_attested_at": now,
                "updated_at": now,
            },
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not record the agent's Texas REALTORS® / NAR authorization attestation.")
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise PermissionError("Your active brokerage membership could not be updated for this restricted form.")
    return now


async def _create_representation_draft(user, data, form_code, parser):
    draft = parser(data)
    brokerage_id = await _active_brokerage_member(user)
    await _require_brokerage_txr_authorization(brokerage_id)
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
    agent_attested_at = await _record_agent_txr_attestation(user, brokerage_id)
    # Preserve the agent's point-of-use attestation as server-authored audit
    # metadata. The browser checkbox is required by each parser, but the
    # identity and timestamp must come from the authenticated request rather
    # than client-supplied fields. This does not infer membership from a
    # license number or replace the brokerage/source authorization gates.
    agreement_data = dict(draft["agreement_data"] or {})
    agreement_data["form_use_attested_by"] = user["id"]
    # Keep the agreement metadata server-authored as before; the membership
    # timestamp is the canonical audit value for this request.
    agreement_data["form_use_attested_at"] = datetime.now(timezone.utc).isoformat()
    agreement_data["form_use_attested_at"] = agent_attested_at
    record = {
        "brokerage_id": brokerage_id,
        "agent_user_id": user["id"],
        "form_source_id": source["id"],
        "form_code": form_code,
        "source_revision": source["source_revision"],
        "status": "draft",
        "client_names": draft["client_names"],
        "agreement_data": agreement_data,
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


async def _create_txr_1506_draft(user, data):
    return await _create_representation_draft(user, data, TXR_1506_FORM_CODE, _parse_txr_1506_draft)


async def _deliver_seller_review_email(email, review_url, verification_code, expires_at, property_address):
    if not RESEND_API_KEY:
        raise RuntimeError("Seller review email is not configured yet.")
    payload = {
        "from": BROKERAGE_INVITE_FROM_EMAIL,
        "to": [email],
        "subject": "Review your HomeOfferFlow seller disclosure",
        "html": (
            "<p>Your real estate professional prepared a seller disclosure for your review.</p>"
            f"<p><strong>Property:</strong> {html.escape(property_address)}</p>"
            f"<p>Open the private review page: <a href=\"{html.escape(review_url)}\">{html.escape(review_url)}</a></p>"
            f"<p>When prompted, enter this one-time verification code: <strong>{html.escape(verification_code)}</strong></p>"
            f"<p>This link expires {html.escape(expires_at)}. Do not forward the link or code.</p>"
            "<p>This is a review-only page. It is not an electronic signature request.</p>"
        ),
    }
    if BROKERAGE_INVITE_REPLY_TO:
        payload["reply_to"] = BROKERAGE_INVITE_REPLY_TO
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not send the seller review email.")


async def _create_seller_disclosure_review_link(user, data):
    try:
        draft_id = str(uuid.UUID(str(data.get("draftId") or "")))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid seller disclosure draft.")
    brokerage_id = await _active_brokerage_member(user)
    drafts = await _get(
        "hof_seller_disclosure_drafts?"
        f"id=eq.{urllib.parse.quote(draft_id)}"
        f"&agent_user_id=eq.{urllib.parse.quote(user['id'])}"
        f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
        "&status=eq.draft"
        "&select=id,property_address,seller_names&limit=1"
    )
    if not drafts:
        raise PermissionError("That private seller disclosure draft is unavailable.")
    seller_names = [" ".join(str(name).strip().split()) for name in (drafts[0].get("seller_names") or data.get("sellerNames") or []) if str(name).strip()]
    if not seller_names:
        # Preserve the original one-seller API contract for existing clients.
        seller_names = [None]
    if len(seller_names) > 2:
        raise ValueError("A seller disclosure can have no more than two seller review recipients.")
    requested_reviews = data.get("sellerReviews")
    if requested_reviews is None:
        requested_reviews = [{"sellerEmail": data.get("sellerEmail"), "sellerName": seller_names[0], "sellerIndex": 1}]
    if not isinstance(requested_reviews, list) or not requested_reviews or len(requested_reviews) > 2:
        raise ValueError("Provide one review recipient per seller.")
    if seller_names != [None] and len(requested_reviews) != len(seller_names):
        raise ValueError("Provide one review recipient per listed seller.")
    normalized_reviews = []
    seen_indexes = set()
    seen_emails = set()
    for position, review in enumerate(requested_reviews, start=1):
        if not isinstance(review, dict):
            raise ValueError("Each seller review recipient must be an object.")
        email = seller_review_access.normalize_email(review.get("sellerEmail"))
        seller_index = review.get("sellerIndex") or position
        try:
            seller_index = int(seller_index)
        except (TypeError, ValueError):
            raise ValueError("Seller review recipient index must be 1 or 2.")
        if seller_index < 1 or seller_index > len(seller_names) or seller_index in seen_indexes:
            raise ValueError("Provide one unique review recipient per seller.")
        seller_name = " ".join(str(review.get("sellerName") or (seller_names[seller_index - 1] if seller_names != [None] else "")).strip().split()) or None
        if seller_names != [None] and not seller_review_access.seller_name_matches(seller_name, [seller_names[seller_index - 1]]):
            raise ValueError("Seller review recipient names must match the saved seller names.")
        if email in seen_emails:
            raise ValueError("Each seller review recipient must use a different email address.")
        seen_indexes.add(seller_index)
        seen_emails.add(email)
        normalized_reviews.append({"email": email, "seller_name": seller_name, "seller_index": seller_index})
    # A follow-up must create a fresh credential, but must never leave an
    # earlier incomplete credential usable.  The partial unique index applied
    # with this behavior also prevents two active links for the same seller if
    # a request is retried.  Completed attestations are intentionally left as
    # the durable review record.
    outstanding = await _get(
        "hof_seller_disclosure_review_links?"
        f"draft_id=eq.{urllib.parse.quote(draft_id)}"
        "&revoked_at=is.null&seller_attested_at=is.null"
        "&select=id,seller_index&limit=10"
    )
    requested_indexes = {review["seller_index"] for review in normalized_reviews}
    created = []
    async with httpx.AsyncClient(timeout=12) as client:
        for existing in outstanding:
            existing_index = existing.get("seller_index")
            is_legacy_single_seller_link = len(seller_names) == 1 and existing_index is None
            if existing_index not in requested_indexes and not is_legacy_single_seller_link:
                continue
            response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/hof_seller_disclosure_review_links?"
                f"id=eq.{urllib.parse.quote(str(existing['id']))}"
                "&revoked_at=is.null&seller_attested_at=is.null",
                headers={**_headers(), "Prefer": "return=minimal"},
                json={"revoked_at": datetime.now(timezone.utc).isoformat()},
            )
            if response.status_code >= 300:
                raise RuntimeError("Could not retire the prior seller review request.")
        for review in normalized_reviews:
            issued = seller_review_access.issue_credentials()
            review_url = f"{PUBLIC_APP_ORIGIN}/seller-review.html?token={urllib.parse.quote(issued['token'], safe='')}"
            record = {
                "draft_id": draft_id,
                "brokerage_id": brokerage_id,
                "agent_user_id": user["id"],
                "seller_email": review["email"],
                "seller_name": review["seller_name"],
                "seller_index": review["seller_index"],
                "token_hash": issued["token_hash"],
                "verification_code_hash": issued["verification_code_hash"],
                "expires_at": issued["expires_at"],
            }
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/hof_seller_disclosure_review_links",
                headers={**_headers(), "Prefer": "return=representation"},
                json=record,
            )
            if response.status_code not in {200, 201}:
                raise RuntimeError("Could not create the seller review request. Apply the seller review migration first.")
            rows = response.json()
            try:
                await _deliver_seller_review_email(
                    review["email"], review_url, issued["code"], issued["expires_at"], drafts[0]["property_address"]
                )
            except Exception:
                if rows:
                    await client.patch(
                        f"{SUPABASE_URL}/rest/v1/hof_seller_disclosure_review_links?"
                        f"id=eq.{urllib.parse.quote(str(rows[0].get('id')))}",
                        headers=_headers(),
                        json={"revoked_at": datetime.now(timezone.utc).isoformat()},
                    )
                raise
            created.append({"id": rows[0].get("id") if rows else None, "sellerIndex": review["seller_index"], "expiresAt": issued["expires_at"]})
    return {"links": created, "id": created[0]["id"] if created else None, "expiresAt": created[0]["expiresAt"] if created else None, "workflowActivated": False}


async def _seller_review_pending(token):
    token_hash = seller_review_access.hash_secret(token)
    rows = await _get(
        "hof_seller_disclosure_review_links?"
        f"token_hash=eq.{urllib.parse.quote(token_hash)}"
        "&select=id,expires_at,revoked_at,verified_at&limit=1"
    )
    if not rows or not seller_review_access.is_active(rows[0].get("expires_at")):
        raise PermissionError("This seller review link is invalid or expired.")
    return rows[0]


async def _verify_seller_review(token, data):
    token_hash = seller_review_access.hash_secret(token)
    rows = await _get(
        "hof_seller_disclosure_review_links?"
        f"token_hash=eq.{urllib.parse.quote(token_hash)}"
        "&select=id,agent_user_id,seller_index,expires_at,revoked_at,verification_code_hash&limit=1"
    )
    if not rows or not seller_review_access.is_active(rows[0].get("expires_at")):
        raise PermissionError("This seller review link is invalid or expired.")
    row = rows[0]
    if not seller_review_access.code_matches(data.get("verificationCode"), token_hash, row.get("verification_code_hash")):
        raise PermissionError("The verification code is incorrect or expired.")
    session = seller_review_access.issue_session()
    now = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_seller_disclosure_review_links?"
            f"id=eq.{urllib.parse.quote(str(row['id']))}",
            headers={**_headers(), "Prefer": "return=representation"},
            json={
                "verified_at": now,
                "session_token_hash": session["token_hash"],
                "session_expires_at": session["expires_at"],
                "updated_at": now,
            },
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not verify the seller review request.")
    await _record_offer_event(
        row.get("agent_user_id"),
        "seller_review_verified",
        "Seller disclosure review recipient verified.",
        {"sellerIndex": row.get("seller_index")},
    )
    return {"sessionToken": session["token"], "sessionExpiresAt": session["expires_at"], "workflowActivated": False}


async def _seller_review_context(session_token):
    session_hash = seller_review_access.hash_secret(session_token)
    rows = await _get(
        "hof_seller_disclosure_review_links?"
        f"session_token_hash=eq.{urllib.parse.quote(session_hash)}"
        "&select=id,draft_id,brokerage_id,agent_user_id,seller_name,seller_index,session_expires_at,revoked_at,viewed_at,seller_attested_at,seller_attested_name&limit=1"
    )
    if not rows or rows[0].get("revoked_at") or not seller_review_access.is_active(rows[0].get("session_expires_at")):
        raise PermissionError("Your seller review session is invalid or expired.")
    link = rows[0]
    drafts = await _get(
        "hof_seller_disclosure_drafts?"
        f"id=eq.{urllib.parse.quote(str(link['draft_id']))}"
        f"&brokerage_id=eq.{urllib.parse.quote(str(link['brokerage_id']))}"
        "&status=eq.draft"
        "&select=id,property_address,seller_names,buyer_names,response_data,water_rights_data,"
        "disclosure_source_id,water_source_id,disclosure_source_revision,water_source_revision"
        "&limit=1"
    )
    if not drafts:
        raise PermissionError("The seller disclosure draft is no longer available.")
    if not link.get("viewed_at"):
        now = datetime.now(timezone.utc).isoformat()
        async with httpx.AsyncClient(timeout=12) as client:
            await client.patch(
                f"{SUPABASE_URL}/rest/v1/hof_seller_disclosure_review_links?"
                f"id=eq.{urllib.parse.quote(str(link['id']))}",
                headers=_headers(), json={"viewed_at": now, "updated_at": now}
            )
        await _record_offer_event(
            link.get("agent_user_id"),
            "seller_review_viewed",
            "Seller disclosure review opened.",
            {"sellerIndex": link.get("seller_index")},
        )
    return link, drafts[0]


async def _seller_review_payload(session_token):
    link, draft = await _seller_review_context(session_token)
    return {
        "id": link["id"],
        "propertyAddress": draft.get("property_address"),
        "sellerNames": draft.get("seller_names") or [],
        "sellerName": link.get("seller_name"),
        "sellerIndex": link.get("seller_index"),
        "buyerNames": draft.get("buyer_names") or [],
        "expiresAt": link.get("session_expires_at"),
        "sellerAttested": bool(link.get("seller_attested_at")),
        "workflowActivated": False,
    }


async def _refresh_seller_review_attestation(draft_id, brokerage_id):
    """Mark the draft reviewed only after every listed seller has attested."""
    drafts = await _get(
        "hof_seller_disclosure_drafts?"
        f"id=eq.{urllib.parse.quote(str(draft_id))}"
        f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
        "&status=eq.draft&select=id,seller_names,seller_review_attested&limit=1"
    )
    if not drafts:
        return False
    seller_names = [" ".join(str(name).strip().split()) for name in (drafts[0].get("seller_names") or []) if str(name).strip()]
    links = await _get(
        "hof_seller_disclosure_review_links?"
        f"draft_id=eq.{urllib.parse.quote(str(draft_id))}"
        f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
        "&revoked_at=is.null&select=seller_name,seller_index,seller_attested_at,agent_user_id"
    )
    if not seller_names:
        return False
    complete = True
    for index, expected_name in enumerate(seller_names, start=1):
        matching = [
            link for link in links
            if (link.get("seller_index") == index or (len(seller_names) == 1 and link.get("seller_index") is None))
            and seller_review_access.seller_name_matches(link.get("seller_name") or expected_name, [expected_name])
            and link.get("seller_attested_at")
        ]
        if not matching:
            complete = False
            break
    if complete and not drafts[0].get("seller_review_attested"):
        now = datetime.now(timezone.utc).isoformat()
        attested_by = next((link.get("agent_user_id") for link in links if link.get("agent_user_id")), None)
        if not attested_by:
            return False
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/hof_seller_disclosure_drafts?"
                f"id=eq.{urllib.parse.quote(str(draft_id))}&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}",
                headers={**_headers(), "Prefer": "return=minimal"},
                json={"seller_review_attested": True, "seller_review_attested_at": now, "seller_review_attested_by": attested_by, "updated_at": now},
            )
        if response.status_code >= 300:
            raise RuntimeError("Could not update the seller disclosure review status.")
    return complete


async def _attest_seller_review(session_token, data):
    link, draft = await _seller_review_context(session_token)
    if link.get("seller_attested_at"):
        return {"ok": True, "alreadyAttested": True, "workflowActivated": False}
    seller_name = " ".join(str(data.get("sellerName") or "").strip().split())
    expected_seller_names = [link.get("seller_name")] if link.get("seller_name") else (draft.get("seller_names") or [])
    if link.get("seller_name") is None and len(expected_seller_names) != 1:
        raise PermissionError("This review link is not assigned to a specific seller. Ask the agent to resend the seller review request.")
    if not seller_review_access.seller_name_matches(seller_name, expected_seller_names):
        raise PermissionError("Enter the name of one of the listed sellers exactly as it appears on the disclosure.")
    now = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_seller_disclosure_review_links?"
            f"id=eq.{urllib.parse.quote(str(link['id']))}&seller_attested_at=is.null",
            headers={**_headers(), "Prefer": "return=representation"},
            json={"seller_attested_at": now, "seller_attested_name": seller_name, "updated_at": now},
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not record the seller review attestation.")
    all_sellers_attested = await _refresh_seller_review_attestation(link["draft_id"], link["brokerage_id"])
    await _record_offer_event(
        link.get("agent_user_id"),
        "seller_review_attested",
        "Seller disclosure review attested.",
        {"sellerIndex": link.get("seller_index"), "allSellersAttested": all_sellers_attested},
    )
    return {"ok": True, "attestedAt": now, "attestedName": seller_name, "allSellersAttested": all_sellers_attested, "workflowActivated": False}


async def _render_seller_disclosure_draft_preview(user, draft_id, review_context=None):
    """Render an agent-owned or email-verified seller draft as an unsigned preview."""
    try:
        draft_uuid = str(uuid.UUID(str(draft_id)))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid private seller disclosure draft.")
    if review_context:
        brokerage_id = str(review_context["brokerage_id"])
        draft_query = (
            "hof_seller_disclosure_drafts?"
            f"id=eq.{urllib.parse.quote(draft_uuid)}"
            f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
            "&status=eq.draft"
        )
    else:
        brokerage_id = await _active_brokerage_member(user)
        draft_query = (
            "hof_seller_disclosure_drafts?"
            f"id=eq.{urllib.parse.quote(draft_uuid)}"
            f"&agent_user_id=eq.{urllib.parse.quote(user['id'])}"
            f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
            "&status=eq.draft"
        )
    drafts = await _get(
        draft_query +
        "&select=id,property_address,response_data,water_rights_data,"
        "disclosure_source_id,water_source_id,disclosure_source_revision,water_source_revision"
        "&limit=1"
    )
    if not drafts:
        raise PermissionError("That private seller disclosure draft is unavailable.")
    draft = drafts[0]

    async def _approved_source(source_id, form_code, expected_revision):
        if not source_id:
            return None
        rows = await _get(
            "hof_brokerage_form_sources?"
            f"id=eq.{urllib.parse.quote(str(source_id))}"
            f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
            f"&form_code=eq.{urllib.parse.quote(form_code)}"
            "&status=eq.approved&authorization_attested=is.true"
            "&select=id,source_revision,storage_bucket,storage_path&limit=1"
        )
        if not rows:
            raise ValueError(f"The approved {form_code} source is no longer available.")
        source = rows[0]
        if source.get("source_revision") != expected_revision:
            raise ValueError(f"The {form_code} draft source revision no longer matches the approved source.")
        return source

    async def _source_bytes(source):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{SUPABASE_URL}/storage/v1/object/"
                f"{urllib.parse.quote(str(source['storage_bucket']), safe='')}/"
                f"{urllib.parse.quote(str(source['storage_path']), safe='/')}",
                headers=_headers(),
            )
        if response.status_code != 200 or not response.content.startswith(b"%PDF"):
            raise RuntimeError("The approved seller-disclosure source could not be loaded.")
        return response.content

    disclosure_source = await _approved_source(
        draft.get("disclosure_source_id"), TREC_55_1_FORM_CODE,
        draft.get("disclosure_source_revision"),
    )
    if not disclosure_source:
        raise ValueError("The seller disclosure source is missing.")
    water_source = await _approved_source(
        draft.get("water_source_id"), TREC_61_0_FORM_CODE,
        draft.get("water_source_revision"),
    )

    from lib.trec_seller_disclosure import render_unsigned_preview

    response_values = dict(draft.get("response_data") or {})
    response_values["propertyAddress"] = draft.get("property_address") or ""
    preview = render_unsigned_preview(
        await _source_bytes(disclosure_source),
        TREC_55_1_FORM_CODE,
        response_values,
        qa_mode=True,
    )
    if water_source:
        water_values = dict(draft.get("water_rights_data") or {})
        water_values["propertyAddress"] = draft.get("property_address") or ""
        water_preview = render_unsigned_preview(
            await _source_bytes(water_source),
            TREC_61_0_FORM_CODE,
            water_values,
            qa_mode=True,
        )
        writer = PdfWriter()
        for payload in (preview, water_preview):
            reader = PdfReader(BytesIO(payload))
            for page in reader.pages:
                writer.add_page(page)
        merged = BytesIO()
        writer.write(merged)
        preview = merged.getvalue()
    return preview


async def _render_representation_draft_preview(user, agreement_id):
    """Render an agent's own approved-source representation draft privately.

    This endpoint intentionally stops at a PDF preview. It does not mutate the
    agreement, create a SignWell document, or expose the private source URL.
    Every request revalidates the agent's active membership, brokerage TXR
    authorization, approved source, and draft ownership.
    """
    try:
        agreement_uuid = str(uuid.UUID(str(agreement_id)))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid private agreement draft.")
    brokerage_id = await _active_brokerage_member(user)
    await _require_brokerage_txr_authorization(brokerage_id)
    agreements = await _get(
        "hof_standalone_agreements?"
        f"id=eq.{urllib.parse.quote(agreement_uuid)}"
        f"&agent_user_id=eq.{urllib.parse.quote(user['id'])}"
        f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&status=eq.draft"
        "&select=id,form_code,form_source_id,source_revision,client_names,agreement_data&limit=1"
    )
    if not agreements:
        raise PermissionError("That private agreement draft is unavailable.")
    agreement = agreements[0]
    sources = await _get(
        "hof_brokerage_form_sources?"
        f"id=eq.{urllib.parse.quote(str(agreement['form_source_id']))}"
        f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&form_code=eq.{urllib.parse.quote(str(agreement.get('form_code') or ''))}&status=eq.approved&authorization_attested=is.true"
        "&select=id,source_revision,storage_bucket,storage_path,original_filename&limit=1"
    )
    if not sources:
        raise ValueError("The approved source for this private agreement is no longer available.")
    source = sources[0]
    if source.get("source_revision") != agreement.get("source_revision"):
        raise ValueError("The draft source revision no longer matches the approved source.")
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/"
            f"{urllib.parse.quote(str(source['storage_bucket']), safe='')}/"
            f"{urllib.parse.quote(str(source['storage_path']), safe='/')}",
            headers=_headers(),
        )
    if response.status_code != 200 or not response.content.startswith(b"%PDF"):
        raise RuntimeError(
            f"The approved {agreement.get('form_code') or 'TXR'} source could not be loaded."
        )
    brokerage_rows = await _get(
        "hof_brokerages?"
        f"id=eq.{urllib.parse.quote(brokerage_id)}"
        "&select=id,name,dba_name,license_number&limit=1"
    )
    profile_rows = await _get(
        "hof_profiles?"
        f"id=eq.{urllib.parse.quote(user['id'])}"
        "&select=agent_name,license_number&limit=1"
    )
    if not brokerage_rows:
        raise RuntimeError("The brokerage record could not be loaded.")
    agreement_data = agreement.get("agreement_data") or {}
    compensation_keys = (
        "purchase_percentage", "purchase_flat_fee", "lease_one_month_percentage",
        "lease_total_rents_percentage", "lease_flat_fee"
    )
    render_data = {
        "client_names": agreement.get("client_names") or [],
        **agreement_data,
        "compensation": {key: agreement_data.get(key, "") for key in compensation_keys},
    }
    if agreement.get("form_code") == TXR_1507_FORM_CODE:
        from lib.txr_1507 import render_txr_1507
        return render_txr_1507(response.content, render_data, brokerage_rows[0], profile_rows[0] if profile_rows else {})
    if agreement.get("form_code") == TXR_1501_FORM_CODE:
        from lib.txr_1501 import render_txr_1501
        return render_txr_1501(response.content, render_data, brokerage_rows[0], profile_rows[0] if profile_rows else {})
    if agreement.get("form_code") == TXR_1508_FORM_CODE:
        from lib.txr_1508 import render_txr_1508
        return render_txr_1508(response.content, render_data, brokerage_rows[0], profile_rows[0] if profile_rows else {})
    if agreement.get("form_code") == TXR_1506_FORM_CODE:
        from lib.txr_1506 import render_txr_1506
        return render_txr_1506(response.content, render_data, brokerage_rows[0])
    raise ValueError("Private preview is not available for this form yet.")


async def _render_txr_1507_draft_preview(user, agreement_id):
    """Backward-compatible wrapper for the TXR-1507 private preview."""
    return await _render_representation_draft_preview(user, agreement_id)


def _valid_email(value):
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", str(value or "").strip()))


def _txr_signwell_fields(form_code, agreement_data, client_count):
    """Dispatch to the source-specific SignWell field map.

    Keeping this dispatch in the authenticated server route prevents a browser
    from selecting an arbitrary field map or mixing coordinates between forms.
    """
    if form_code == TXR_1501_FORM_CODE:
        from lib.txr_1501 import build_signwell_fields_txr1501
        return build_signwell_fields_txr1501(agreement_data, client_count=client_count)
    if form_code == TXR_1506_FORM_CODE:
        from lib.txr_1506 import build_signwell_fields_txr1506
        return build_signwell_fields_txr1506(agreement_data, client_count=client_count)
    if form_code == TXR_1507_FORM_CODE:
        from lib.txr_1507 import build_signwell_fields_txr1507
        return build_signwell_fields_txr1507(agreement_data, client_count=client_count)
    if form_code == TXR_1508_FORM_CODE:
        from lib.txr_1508 import build_signwell_fields_txr1508
        return build_signwell_fields_txr1508(agreement_data, client_count=client_count)
    raise ValueError("This standalone form is not available for signing.")


def _txr_signwell_recipients(agreement, client_emails, brokerage, agent_user):
    client_names = agreement.get("client_names") or []
    agreement_data = agreement.get("agreement_data") or {}
    form_code = str(agreement.get("form_code") or "")
    signer_plan = str(agreement_data.get("signer_plan") or "")
    recipients = [
        {"id": str(index), "name": client_names[index - 1], "email": client_emails[index - 1]}
        for index in range(1, len(client_names) + 1)
    ]
    if form_code == TXR_1508_FORM_CODE:
        role = "associate" if signer_plan == "associate_and_clients" else "broker"
    elif form_code == TXR_1506_FORM_CODE:
        role = "associate" if signer_plan == "consumers_and_associate" else "broker"
    else:
        role = "associate" if signer_plan == "clients_and_associate" else "broker"
    if role == "associate":
        associate_email = str(agent_user.get("email") or "").strip()
        associate_name = str(agent_user.get("name") or "Broker associate").strip()
        if not _valid_email(associate_email):
            raise ValueError("The authorized broker associate account needs a valid email before signing.")
        recipients.append({"id": role, "name": associate_name, "email": associate_email})
    else:
        broker_email = str(brokerage.get("contact_email") or "").strip()
        broker_name = str(brokerage.get("contact_name") or brokerage.get("name") or "Broker").strip()
        if not _valid_email(broker_email):
            raise ValueError("The brokerage needs a valid broker contact email before broker signing can be sent.")
        recipients.append({"id": role, "name": broker_name, "email": broker_email})
    return recipients


def _signwell_signing_urls(result):
    """Extract returned recipient signing URLs without persisting them."""
    recipients = result.get("recipients") if isinstance(result, dict) else None
    if not isinstance(recipients, list):
        return []
    urls = []
    for recipient in recipients:
        if not isinstance(recipient, dict):
            continue
        url = str(
            recipient.get("signing_url")
            or recipient.get("embedded_signing_url")
            or recipient.get("signingUrl")
            or ""
        ).strip()
        if url.startswith("https://") and url not in urls:
            urls.append(url)
    return urls


async def _send_txr_agreement_for_signature(user, data):
    """Create one gated SignWell request for an owned standalone TXR draft.

    This is intentionally separate from purchase-offer signing. It rechecks
    active membership, brokerage authorization, approved source revision,
    draft ownership, signer plan, and recipient emails on every send attempt.
    """
    if not TXR_SIGNING_ENABLED:
        raise PermissionError("Restricted TXR signing is not enabled yet; completed signed-PDF release QA is still required.")
    if not SIGNWELL_ENABLED or not SIGNWELL_API_KEY:
        raise RuntimeError("SignWell signing is not configured for this environment.")
    agreement_id = str(data.get("agreementId") or "").strip()
    try:
        agreement_uuid = str(uuid.UUID(agreement_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Choose a valid private agreement draft.")
    brokerage_id = await _active_brokerage_member(user)
    await _require_brokerage_txr_authorization(brokerage_id)
    rows = await _get(
        "hof_standalone_agreements?"
        f"id=eq.{urllib.parse.quote(agreement_uuid)}"
        f"&agent_user_id=eq.{urllib.parse.quote(user['id'])}"
        f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        "&status=eq.draft"
        "&select=id,form_code,form_source_id,source_revision,client_names,agreement_data"
        "&limit=1"
    )
    if not rows:
        raise PermissionError("That private agreement draft is unavailable or has already been sent.")
    agreement = rows[0]
    form_code = str(agreement.get("form_code") or "")
    if form_code not in {TXR_1501_FORM_CODE, TXR_1506_FORM_CODE, TXR_1507_FORM_CODE, TXR_1508_FORM_CODE}:
        raise ValueError("This standalone form is not available for signing.")
    client_names = agreement.get("client_names") or []
    client_emails = data.get("clientEmails")
    if not isinstance(client_emails, list):
        client_emails = []
    client_emails = [str(value or "").strip() for value in client_emails]
    stored_emails = (agreement.get("agreement_data") or {}).get("client_emails") or []
    if not client_emails and isinstance(stored_emails, list):
        client_emails = [str(value or "").strip() for value in stored_emails]
    if form_code == TXR_1501_FORM_CODE and not client_emails:
        legacy_email = str((agreement.get("agreement_data") or {}).get("client_email") or "").strip()
        if legacy_email:
            client_emails = [legacy_email]
    if len(client_emails) != len(client_names) or any(not _valid_email(email) for email in client_emails):
        raise ValueError("Provide one valid, unique signing email for each client.")
    if len({email.casefold() for email in client_emails}) != len(client_emails):
        raise ValueError("Each client must use a different signing email.")
    sources = await _get(
        "hof_brokerage_form_sources?"
        f"id=eq.{urllib.parse.quote(str(agreement['form_source_id']))}"
        f"&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&form_code=eq.{urllib.parse.quote(form_code)}"
        "&status=eq.approved&authorization_attested=is.true"
        "&select=id,source_revision,storage_bucket,storage_path&limit=1"
    )
    if not sources or sources[0].get("source_revision") != agreement.get("source_revision"):
        raise ValueError("The approved source revision for this draft is no longer available.")
    source = sources[0]
    async with httpx.AsyncClient(timeout=20) as client:
        source_response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/"
            f"{urllib.parse.quote(str(source['storage_bucket']), safe='')}/"
            f"{urllib.parse.quote(str(source['storage_path']), safe='/')}",
            headers=_headers(),
        )
    if source_response.status_code != 200 or not source_response.content.startswith(b"%PDF"):
        raise RuntimeError("The approved standalone source could not be loaded.")
    brokerage_rows = await _get(
        "hof_brokerages?"
        f"id=eq.{urllib.parse.quote(brokerage_id)}"
        "&select=id,name,dba_name,legal_name,license_number,contact_name,contact_email&limit=1"
    )
    profile_rows = await _get(
        "hof_profiles?"
        f"id=eq.{urllib.parse.quote(user['id'])}"
        "&select=id,agent_name,email,license_number&limit=1"
    )
    brokerage = brokerage_rows[0] if brokerage_rows else {}
    profile = profile_rows[0] if profile_rows else {}
    agreement_data = dict(agreement.get("agreement_data") or {})
    agreement_data["client_emails"] = client_emails
    client_count = len(client_names)
    fields = _txr_signwell_fields(form_code, {"client_names": client_names, **agreement_data}, client_count)
    rendered = await _render_representation_draft_preview(user, agreement_uuid)
    recipients = _txr_signwell_recipients(
        agreement,
        client_emails,
        brokerage,
        {"email": user.get("email") or profile.get("email"), "name": profile.get("agent_name") or user.get("email")},
    )
    address_label = form_code.replace("-", " ")
    payload = {
        "test_mode": SIGNWELL_TEST_MODE,
        "draft": False,
        "reminders": True,
        "apply_signing_order": True,
        "embedded_signing": False,
        "with_signature_page": False,
        "custom_requester_name": "HomeOfferFlow",
        "name": f"HomeOfferFlow {address_label} — {agreement_uuid[:8]}",
        "subject": f"HomeOfferFlow {address_label} for signature",
        "message": (
            "Please review and sign this brokerage-approved Texas REALTORS® form. "
            "HomeOfferFlow is a form-completion and signing workflow, not a law firm or brokerage. "
            "Confirm the terms with your authorized real-estate professional before signing."
        ),
        "recipients": recipients,
        "files": [{"name": f"HomeOfferFlow_{address_label.replace(' ', '_')}.pdf", "file_base64": base64.b64encode(rendered).decode("ascii")}],
        "fields": fields,
        "metadata": {
            "source": "HomeOfferFlow",
            "standalone_agreement_id": agreement_uuid,
            "form_code": form_code,
            "source_revision": str(agreement.get("source_revision") or "")[:80],
            "test_mode": str(SIGNWELL_TEST_MODE).lower(),
        },
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            "https://www.signwell.com/api/v1/documents",
            headers={"X-Api-Key": SIGNWELL_API_KEY, "Content-Type": "application/json"},
            json=payload,
        )
    if response.status_code not in {200, 201, 202}:
        await _patch("hof_standalone_agreements", f"id=eq.{urllib.parse.quote(agreement_uuid)}", {"status": "failed", "updated_at": datetime.now(timezone.utc).isoformat()})
        raise RuntimeError(f"SignWell rejected the signing request: HTTP {response.status_code}.")
    result = response.json()
    document_id = str(result.get("id") or result.get("document_id") or "").strip()
    if not document_id:
        raise RuntimeError("SignWell did not return a document id.")
    now = datetime.now(timezone.utc).isoformat()
    await _patch(
        "hof_standalone_agreements",
        f"id=eq.{urllib.parse.quote(agreement_uuid)}",
        {"status": "sent", "signwell_document_id": document_id, "signwell_status": str(result.get("status") or "sent"), "sent_at": now, "updated_at": now, "agreement_data": agreement_data},
    )
    return {
        "ok": True,
        "formCode": form_code,
        "documentId": document_id,
        "status": result.get("status") or "sent",
        "testMode": SIGNWELL_TEST_MODE,
        "recipientCount": len(recipients),
        # SignWell may omit these for email-only requests. If present, they
        # are returned only to the authenticated requester and never stored.
        "signingUrls": _signwell_signing_urls(result),
    }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _json(self, 200, {"status": "ok"})

    def do_GET(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            _json(self, 500, {"error": "Supabase env vars missing"})
            return
        try:
            import asyncio
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            review_token = str((query.get("review_seller_disclosure") or [""])[0]).strip()
            review_session = str((query.get("seller_review_session") or [""])[0]).strip()
            review_pdf_session = str((query.get("seller_review_pdf") or [""])[0]).strip()
            if review_token:
                _json(self, 200, asyncio.run(_seller_review_pending(review_token)))
                return
            if review_session:
                _json(self, 200, asyncio.run(_seller_review_payload(review_session)))
                return
            if review_pdf_session:
                link, _draft = asyncio.run(_seller_review_context(review_pdf_session))
                pdf = asyncio.run(_render_seller_disclosure_draft_preview(
                    None, link["draft_id"], review_context=link
                ))
                _pdf_response(self, pdf, "seller-disclosure-review-preview.pdf")
                return
            user = asyncio.run(_verified_user(self.headers.get("authorization", "")))
            if not user:
                _json(self, 401, {"error": "A valid signed-in session is required."})
                return
            preview_seller_disclosure = str((query.get("preview_seller_disclosure") or [""])[0]).strip()
            if preview_seller_disclosure:
                pdf = asyncio.run(_render_seller_disclosure_draft_preview(user, preview_seller_disclosure))
                _pdf_response(self, pdf, "seller-disclosure-private-draft-preview.pdf")
                return
            preview_agreement = str((query.get("preview_agreement") or [""])[0]).strip()
            if preview_agreement:
                pdf = asyncio.run(_render_representation_draft_preview(user, preview_agreement))
                _pdf_response(self, pdf, "standalone-agreement-private-draft-preview.pdf")
                return
            scope = str((query.get("scope") or [""])[0]).strip().lower()
            if scope == "brokerage_form_sources":
                try:
                    payload = asyncio.run(_brokerage_form_sources_payload(user, approved_only=False))
                except PermissionError as exc:
                    _json(self, 403, {"error": str(exc)})
                    return
                _json(self, 200, payload)
                return
            if scope == "approved_brokerage_sources":
                try:
                    payload = asyncio.run(_brokerage_form_sources_payload(user, approved_only=True))
                except PermissionError as exc:
                    _json(self, 403, {"error": str(exc)})
                    return
                _json(self, 200, payload)
                return
            if scope == "seller_disclosure_drafts":
                brokerage_id = asyncio.run(_active_brokerage_member(user))
                rows = asyncio.run(_get(
                    "hof_seller_disclosure_drafts?"
                    f"agent_user_id=eq.{urllib.parse.quote(user['id'])}"
                    f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
                    "&select=id,listing_workspace_id,disclosure_source_id,water_source_id,property_address,seller_names,buyer_names,response_data,water_rights_data,status,disclosure_source_revision,water_source_revision,seller_review_attested,created_at,updated_at"
                    "&order=updated_at.desc&limit=100"
                ))
                review_links = asyncio.run(_get_optional(
                    "hof_seller_disclosure_review_links?"
                    f"agent_user_id=eq.{urllib.parse.quote(user['id'])}"
                    f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
                    "&select=draft_id,seller_email,seller_name,seller_index,expires_at,revoked_at,viewed_at,verified_at,seller_attested_at,created_at"
                    "&order=created_at.desc&limit=300"
                ))
                links_by_draft = {}
                for link in review_links:
                    links_by_draft.setdefault(str(link.get("draft_id") or ""), []).append({
                        "sellerEmail": link.get("seller_email"),
                        "sellerName": link.get("seller_name"),
                        "sellerIndex": link.get("seller_index"),
                        "expiresAt": link.get("expires_at"),
                        "revokedAt": link.get("revoked_at"),
                        "viewedAt": link.get("viewed_at"),
                        "verifiedAt": link.get("verified_at"),
                        "sellerAttestedAt": link.get("seller_attested_at"),
                        "createdAt": link.get("created_at"),
                    })
                for row in rows:
                    links = links_by_draft.get(str(row.get("id") or ""), [])
                    row["sellerReviewLinks"] = links
                    row["sellerReviewProgress"] = {
                        "requested": len(links),
                        "verified": len([link for link in links if link.get("verifiedAt")]),
                        "attested": len([link for link in links if link.get("sellerAttestedAt")]),
                    }
                _json(self, 200, {"drafts": rows})
                return
            if scope == "standalone_agreements":
                brokerage_id = asyncio.run(_active_brokerage_member(user))
                rows = asyncio.run(_get(
                    "hof_standalone_agreements?"
                    f"agent_user_id=eq.{urllib.parse.quote(user['id'])}"
                    f"&brokerage_id=eq.{urllib.parse.quote(str(brokerage_id))}"
                    "&select=id,form_code,source_revision,client_names,status,signwell_status,signwell_document_id,created_at,updated_at,sent_at,signed_at"
                    "&order=updated_at.desc&limit=100"
                ))
                _json(self, 200, {"agreements": rows, "signingEnabled": TXR_SIGNING_ENABLED})
                return
            if scope == "platform_source_brokerages":
                try:
                    payload = asyncio.run(platform_source._active_brokerages(user))
                except PermissionError as exc:
                    _json(self, 403, {"error": str(exc)})
                    return
                _json(self, 200, payload)
                return
            if scope == "seller_leads":
                if not asyncio.run(_is_platform_admin(user)):
                    _json(self, 403, {"error": "Admin access is not enabled for this account."})
                    return
                rows = asyncio.run(_get_optional(
                    "hof_seller_leads?select=id,property_address,property_city,property_county,property_state,property_zip,"
                    "seller_name,seller_email,seller_phone,asking_price,service_level,package_name,package_price,"
                    "timeline,partner_categories,source,utm_source,utm_medium,utm_campaign,utm_content,notes,status,created_at,updated_at&order=created_at.desc&limit=200"
                ))
                _json(self, 200, {"sellerLeads": rows})
                return
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
            # Keep activation reporting aggregate-only. The platform dashboard already
            # has a separate, permission-checked recent-offers view; these rows are
            # intentionally limited to lifecycle fields so the funnel never needs
            # buyer, property, pricing, or document data.
            agent_profiles = asyncio.run(_get_optional(
                "hof_agent_profiles?select=user_id,agent_name,license_number,agent_email,agent_phone,brokerage_name&limit=2000"
            ))
            agent_lifecycle_offers = asyncio.run(_get_optional(
                "hof_offers?role=eq.agent&deleted_at=is.null&select=user_id,status,signwell_status,created_at,updated_at&limit=2000"
            ))
            # Keep funnel/cohort metrics representative beyond the most recent
            # page while bounding the admin payload for predictable latency.
            events = asyncio.run(_get("hof_offer_events?select=*&order=created_at.desc&limit=2000"))
            subs = asyncio.run(_get("hof_subscriptions?select=*&order=created_at.desc&limit=50")) if True else []
            brokerages = asyncio.run(_get("hof_brokerages?select=*&order=created_at.desc&limit=50"))
            brokerage_invites = asyncio.run(_get_optional(
                "hof_brokerage_invites?select=status,created_at,accepted_at,expires_at&order=created_at.desc&limit=2000"
            ))
            all_partner_leads = asyncio.run(_get_optional("hof_partner_leads?select=*&order=created_at.desc&limit=100"))
            # Test-mode Stripe records are useful QA evidence but must never
            # appear as paid partners, onboarding gaps, or follow-up work in
            # the live operations dashboard.
            sandbox_partner_lead_count = len([
                lead for lead in all_partner_leads if _is_sandbox_partner_lead(lead)
            ])
            partner_leads = [
                lead for lead in all_partner_leads if not _is_sandbox_partner_lead(lead)
            ]
            seller_leads = asyncio.run(_get_optional(
                "hof_seller_leads?select=id,property_address,property_city,property_county,property_state,property_zip,"
                "seller_name,seller_email,seller_phone,asking_price,service_level,package_name,package_price,"
                "timeline,partner_categories,source,utm_source,utm_medium,utm_campaign,utm_content,notes,status,created_at,updated_at&order=created_at.desc&limit=200"
            ))
            partner_placements = asyncio.run(_get_optional("hof_partner_placements?select=id,source_lead_id,partner_type,partner_name,website_url,logo_url,market_area,placement_tier,monthly_fee,is_active,created_at,activated_at,agreement_confirmed_at&brokerage_id=is.null&order=created_at.desc&limit=100"))
            active_partner_source_lead_ids = {
                str(placement.get("source_lead_id") or "")
                for placement in partner_placements
                if placement.get("is_active") and placement.get("source_lead_id")
            }
            # Agreement confirmation is recorded with the public placement at
            # activation time.  Include that canonical record when reporting
            # paid-partner agreement coverage, while retaining the legacy
            # lead-level fields for any earlier records.
            agreement_confirmed_source_lead_ids = {
                str(placement.get("source_lead_id") or "")
                for placement in partner_placements
                if placement.get("source_lead_id") and placement.get("agreement_confirmed_at")
            }
            partner_leads_by_id = {
                str(lead.get("id") or ""): lead
                for lead in partner_leads
                if lead.get("id")
            }
            partner_activation_durations = []
            for placement in partner_placements:
                if not placement.get("is_active"):
                    continue
                lead = partner_leads_by_id.get(str(placement.get("source_lead_id") or ""))
                created_at = _parse_timestamp((lead or {}).get("created_at"))
                activated_at = _parse_timestamp(placement.get("activated_at"))
                if created_at and activated_at and activated_at >= created_at:
                    partner_activation_durations.append((activated_at - created_at).total_seconds() / 86400)
            partner_activation_avg_days = round(
                sum(partner_activation_durations) / len(partner_activation_durations), 1
            ) if partner_activation_durations else 0
            paid_partner_activation_queue = [
                lead for lead in partner_leads
                if str(lead.get("payment_status") or "").lower() == "paid"
                and str(lead.get("status") or "").lower() not in {"declined", "waitlist"}
                and str(lead.get("id") or "") not in active_partner_source_lead_ids
            ]
            # Put the oldest paid applications first so admin follow-up starts
            # with the revenue most at risk of going stale.
            paid_partner_activation_queue.sort(
                key=lambda lead: _parse_timestamp(lead.get("created_at"))
                or datetime.max.replace(tzinfo=timezone.utc)
            )
            now = datetime.now(timezone.utc)
            for lead in paid_partner_activation_queue:
                lead["activation_readiness"] = _partner_activation_readiness(lead, now)
            paid_partner_lead_count = len([
                lead for lead in partner_leads
                if str(lead.get("payment_status") or "").lower() == "paid"
            ])
            partner_onboarding_ready_count = len([
                lead for lead in partner_leads
                if str(lead.get("payment_status") or "").lower() == "paid"
                and str(lead.get("onboarding_status") or "").lower() in {"ready", "complete", "completed"}
            ])
            partner_onboarding_in_progress_count = len([
                lead for lead in partner_leads
                if str(lead.get("payment_status") or "").lower() == "paid"
                and str(lead.get("onboarding_status") or "").lower() == "in_progress"
            ])
            partner_onboarding_completed_count = len([
                lead for lead in partner_leads
                if str(lead.get("payment_status") or "").lower() == "paid"
                and (lead.get("onboarding_completed_at") or str(lead.get("onboarding_status") or "").lower() in {"complete", "completed"})
            ])
            # A paid partner cannot complete setup without a current hashed
            # setup token. Count only this operational gap; never return the
            # token, its hash, expiry timestamp, or partner contact details.
            partner_onboarding_access_missing_count = len([
                lead for lead in partner_leads
                if str(lead.get("payment_status") or "").lower() == "paid"
                and str(lead.get("onboarding_status") or "").lower() in {"ready", "in_progress"}
                and (
                    not lead.get("onboarding_token_hash")
                    or not (expires_at := _parse_timestamp(lead.get("onboarding_token_expires_at")))
                    or expires_at <= now
                )
            ])
            paid_partner_agreement_confirmed_count = len([
                lead for lead in partner_leads
                if str(lead.get("payment_status") or "").lower() == "paid"
                and (
                    str(lead.get("partner_agreement_status") or "").lower() == "signed"
                    or
                    str(lead.get("id") or "") in agreement_confirmed_source_lead_ids
                    or
                    lead.get("agreement_confirmed_at")
                    or str(lead.get("agreement_status") or "").lower() in {"confirmed", "signed", "complete", "completed"}
                )
            ])
            paid_partner_activation_queue_aged_count = len([
                lead for lead in paid_partner_activation_queue
                if (created_at := _parse_timestamp(lead.get("created_at")))
                and created_at <= datetime.now(timezone.utc) - timedelta(days=7)
            ])
            paid_partner_activation_readiness_counts = {}
            for lead in paid_partner_activation_queue:
                code = str((lead.get("activation_readiness") or {}).get("code") or "unknown")
                paid_partner_activation_readiness_counts[code] = paid_partner_activation_readiness_counts.get(code, 0) + 1
            roadmap = asyncio.run(_get("hof_roadmap_items?select=*&order=priority.asc&limit=100"))
            qa_scenarios = asyncio.run(_get("hof_qa_scenarios?select=*&active=eq.true&order=priority.asc&limit=100"))
            qa_runs = asyncio.run(_get("hof_qa_runs?select=*&order=created_at.desc&limit=50"))
            releases = asyncio.run(_get("hof_releases?select=*&order=created_at.desc&limit=20"))
            stripe_webhook_events = asyncio.run(_get_optional(
                "hof_stripe_webhook_events?select=stripe_event_id,event_type,livemode,processing_state,error_code,received_at,processed_at&order=received_at.desc&limit=50"
            ))
            stripe_webhook_event_type_counts = {}
            for item in stripe_webhook_events:
                event_type = str(item.get("event_type") or "unknown").strip().lower()[:80] or "unknown"
                stripe_webhook_event_type_counts[event_type] = stripe_webhook_event_type_counts.get(event_type, 0) + 1
            # Platform-admin-only calibration feed. Keep direct account email,
            # user-agent, and page URL out of the dashboard response; the
            # existing feedback record remains available for support workflows.
            feedback = asyncio.run(_get_optional(
                "hof_feedback?select=id,issue_type,calibration_scenario,message,status,role,created_at&order=created_at.desc&limit=100"
            ))
            missing_form_request_count = len([
                item for item in feedback if str(item.get("issue_type") or "").lower() == "missing_addendum"
            ])
            missing_form_request_code_counts = _missing_form_request_code_counts(feedback)
            missing_form_recent_code_counts = _missing_form_request_recent_code_counts(feedback)
            missing_form_intake_brief_copy_count = len([
                item for item in events if item.get("event_type") == "missing_form_intake_brief_copied"
            ])
            partner_follow_up_email_start_count = len([
                item for item in events if item.get("event_type") == "partner_follow_up_email_started"
            ])
            # Public partner checkout telemetry deliberately contains only
            # funnel state and the selected tier. Surface aggregate counts so
            # commercial conversion can be improved without exposing applicant
            # contact, company, market, or payment data in the dashboard.
            partner_checkout_event_counts = {
                "intake_opened": 0,
                "tier_selected": 0,
                "checkout_started": 0,
                "application_saved": 0,
                "stripe_opened": 0,
                "cancelled": 0,
                "completed": 0,
                "failed": 0,
            }
            partner_checkout_event_keys = {
                "founding_partner_intake_opened": "intake_opened",
                "founding_partner_tier_selected": "tier_selected",
                "founding_partner_checkout_started": "checkout_started",
                "founding_partner_application_saved": "application_saved",
                "founding_partner_stripe_checkout_opened": "stripe_opened",
                "founding_partner_checkout_cancelled": "cancelled",
                "founding_partner_checkout_completed": "completed",
                "founding_partner_checkout_failed": "failed",
            }
            # Campaign parameters are UI-only, allowlisted choices. Count only
            # those known values from intake-open events, and never return an
            # applicant, company, market, URL, or payment value to the admin
            # dashboard just to assess acquisition performance.
            partner_campaign_categories = {
                "title", "lender", "inspection", "surveyor", "home_warranty",
                "insurance", "roofing", "hvac", "plumbing", "electrical",
                "foundation_structural", "general_contractor", "pest_termite",
                "septic_well", "restoration", "repairs_handyman",
                "photography_video", "staging", "cleaning", "moving_storage",
                "lawn_pool", "security_smart_home", "other",
            }
            partner_campaign_tiers = {"founding_pilot", "monthly_placement", "market_exclusive"}
            partner_campaign_channels = {"direct_outreach", "email", "social", "referral", "local_event", "print"}
            partner_campaign_category_counts = {}
            partner_campaign_tier_counts = {}
            partner_campaign_channel_counts = {}
            partner_checkout_recovery_stripe_open_count = 0
            for item in events:
                event_type = str(item.get("event_type") or "").strip().lower()
                event_key = partner_checkout_event_keys.get(event_type)
                if event_key:
                    partner_checkout_event_counts[event_key] += 1
                metadata = item.get("metadata") or {}
                if (
                    event_type == "founding_partner_stripe_checkout_opened"
                    and str(metadata.get("source") or "").strip().lower() == "partner_cancel_recovery"
                ):
                    partner_checkout_recovery_stripe_open_count += 1
                if event_type != "founding_partner_intake_opened":
                    continue
                category = str(metadata.get("campaignCategory") or "").strip().lower()
                tier = str(metadata.get("campaignTier") or "").strip().lower()
                channel = str(metadata.get("campaignChannel") or "").strip().lower()
                if category in partner_campaign_categories:
                    partner_campaign_category_counts[category] = partner_campaign_category_counts.get(category, 0) + 1
                if tier in partner_campaign_tiers:
                    partner_campaign_tier_counts[tier] = partner_campaign_tier_counts.get(tier, 0) + 1
                if channel in partner_campaign_channels:
                    partner_campaign_channel_counts[channel] = partner_campaign_channel_counts.get(channel, 0) + 1
            partner_campaign_category_counts = dict(sorted(
                partner_campaign_category_counts.items(), key=lambda item: (-item[1], item[0])
            ))
            partner_campaign_tier_counts = dict(sorted(
                partner_campaign_tier_counts.items(), key=lambda item: (-item[1], item[0])
            ))
            partner_campaign_channel_counts = dict(sorted(
                partner_campaign_channel_counts.items(), key=lambda item: (-item[1], item[0])
            ))
            # The public partner page records only an allowlisted stage, tier,
            # and category. This reveals whether the commercial landing page
            # earns application starts without returning company, contact,
            # market, campaign, or visitor details in the Admin response.
            partner_landing_event_types = {
                "partner_landing_viewed",
                "partner_landing_cta_selected",
                "partner_directory_application_selected",
                "partner_directory_empty_search",
            }
            partner_landing_events = [
                item for item in events if item.get("event_type") in partner_landing_event_types
            ]
            partner_landing_view_count = len([
                item for item in partner_landing_events if item.get("event_type") == "partner_landing_viewed"
            ])
            partner_landing_cta_count = len([
                item for item in partner_landing_events if item.get("event_type") == "partner_landing_cta_selected"
            ])
            partner_directory_application_start_count = len([
                item for item in partner_landing_events
                if item.get("event_type") == "partner_directory_application_selected"
            ])
            partner_directory_empty_search_count = len([
                item for item in partner_landing_events
                if item.get("event_type") == "partner_directory_empty_search"
            ])
            partner_directory_empty_search_category_counts = {}
            for item in partner_landing_events:
                if item.get("event_type") != "partner_directory_empty_search":
                    continue
                category = str((item.get("metadata") or {}).get("category") or "").strip().lower()
                if category in ALLOWED_PARTNER_TYPES:
                    partner_directory_empty_search_category_counts[category] = (
                        partner_directory_empty_search_category_counts.get(category, 0) + 1
                    )
            partner_directory_empty_search_category_counts = dict(sorted(
                partner_directory_empty_search_category_counts.items(), key=lambda item: (-item[1], item[0])
            ))
            partner_landing_tier_cta_counts = {}
            for item in partner_landing_events:
                if item.get("event_type") != "partner_landing_cta_selected":
                    continue
                tier = str((item.get("metadata") or {}).get("tier") or "").strip().lower()
                if tier in {"founding_pilot", "monthly_placement", "market_exclusive", "unspecified"}:
                    partner_landing_tier_cta_counts[tier] = partner_landing_tier_cta_counts.get(tier, 0) + 1
            partner_landing_tier_cta_counts = dict(sorted(
                partner_landing_tier_cta_counts.items(), key=lambda item: (-item[1], item[0])
            ))
            # Directory traffic is recorded server-side only as placement ID,
            # category, and tier. This lets operators evaluate paid-placement
            # value without retaining a visitor, search text, or destination URL.
            partner_directory_impression_count = 0
            partner_directory_outbound_click_count = 0
            partner_directory_fsbo_seller_plan_impression_count = 0
            partner_directory_fsbo_seller_plan_outbound_click_count = 0
            placement_ids = {str(placement.get("id") or "") for placement in partner_placements}
            partner_directory_traffic_by_placement = {
                placement_id: {"impressions": 0, "outboundClicks": 0}
                for placement_id in placement_ids if placement_id
            }
            for item in events:
                event_type = str(item.get("event_type") or "").strip().lower()
                if event_type not in {"partner_directory_impression", "partner_directory_outbound_click"}:
                    continue
                if event_type == "partner_directory_impression":
                    partner_directory_impression_count += 1
                else:
                    partner_directory_outbound_click_count += 1
                metadata = item.get("metadata") or {}
                if str(metadata.get("directorySurface") or "").strip() == "fsbo_seller_plan":
                    if event_type == "partner_directory_impression":
                        partner_directory_fsbo_seller_plan_impression_count += 1
                    else:
                        partner_directory_fsbo_seller_plan_outbound_click_count += 1
                partner_id = str(metadata.get("partnerId") or "").strip()
                traffic = partner_directory_traffic_by_placement.get(partner_id)
                if not traffic:
                    continue
                if event_type == "partner_directory_impression":
                    traffic["impressions"] += 1
                else:
                    traffic["outboundClicks"] += 1
            for placement in partner_placements:
                traffic = partner_directory_traffic_by_placement.get(
                    str(placement.get("id") or ""), {"impressions": 0, "outboundClicks": 0}
                )
                impressions = int(traffic["impressions"])
                outbound_clicks = int(traffic["outboundClicks"])
                placement["directoryTraffic"] = {
                    "impressions": impressions,
                    "outboundClicks": outbound_clicks,
                    "outboundClickRate": round((outbound_clicks / impressions) * 100, 1) if impressions else 0,
                }
            # A setup-link email is a deliberate platform-admin action. Keep this
            # aggregate separate from mailto follow-ups so the paid-partner
            # onboarding funnel shows whether secure access is actually being
            # delivered, without returning recipient or token details.
            partner_onboarding_email_sent_count = len([
                item for item in events if item.get("event_type") == "partner_onboarding_email_sent"
            ])
            # Automatic setup access is issued by the verified Stripe webhook.
            # Keep it separate from deliberate admin re-sends; counting only
            # the latter made a healthy checkout handoff look like zero.
            partner_onboarding_setup_issued_count = len([
                item for item in events if item.get("event_type") == "partner_onboarding_setup_issued"
            ])
            # Legacy paid rows predate this telemetry event. A setup token or
            # completion record is durable evidence that secure access issued.
            partner_onboarding_setup_issued_count = max(
                partner_onboarding_setup_issued_count,
                len([
                    lead for lead in partner_leads
                    if str(lead.get("payment_status") or "").lower() == "paid"
                    and (
                        lead.get("onboarding_token_hash")
                        or lead.get("onboarding_completed_at")
                        or str(lead.get("onboarding_status") or "").lower() in {"complete", "completed"}
                    )
                ]),
            )
            # A Checkout-return recovery is a separate, self-service path:
            # it replaces an expiring setup credential only after the signed
            # webhook has recorded the exact paid session. Keep it visible so
            # operators can compare automatic recovery with manual outreach.
            partner_checkout_setup_recovery_count = len([
                item for item in events if item.get("event_type") == "partner_checkout_setup_recovered"
            ])
            partner_onboarding_link_created_count = len([
                item for item in events if item.get("event_type") == "partner_onboarding_link_created"
            ])
            seller_follow_up_email_start_count = len([
                item for item in events if item.get("event_type") == "seller_follow_up_email_started"
            ])
            # Seller acquisition links deliberately carry only a fixed channel
            # and optional campaign label. Roll up channels here instead of
            # exposing free-form UTM values as dashboard dimensions.
            seller_campaign_medium_counts = {
                "direct_outreach": 0,
                "email": 0,
                "social": 0,
                "referral": 0,
                "local_event": 0,
                "print": 0,
                "other_tracked": 0,
            }
            tracked_seller_campaign_leads = [
                lead for lead in seller_leads
                if str(lead.get("source") or "").lower() == "tracked_seller_landing"
            ]
            for lead in tracked_seller_campaign_leads:
                medium = str(lead.get("utm_medium") or "").strip().lower()
                if medium in seller_campaign_medium_counts and medium != "other_tracked":
                    seller_campaign_medium_counts[medium] += 1
                else:
                    seller_campaign_medium_counts["other_tracked"] += 1
            # Landing path choices are aggregate product-routing signals only.
            # Accept a fixed audience vocabulary so event metadata can never
            # introduce free-form visitor data into the platform dashboard.
            landing_audience_selection_counts = {
                "homebuyer": 0,
                "agent": 0,
                "investor": 0,
                "fsbo": 0,
            }
            for item in events:
                if item.get("event_type") != "landing_audience_selected":
                    continue
                metadata = item.get("metadata") or {}
                audience = str(metadata.get("audience") or "").strip().lower()
                if audience in landing_audience_selection_counts:
                    landing_audience_selection_counts[audience] += 1
            ai_review_outputs = asyncio.run(_get_optional(
                "hof_ai_offer_reviews?select=id,created_at,review_mode&order=created_at.desc&limit=100"
            ))
            ai_review_output_mode_counts = {"live_ai": 0, "rules_fallback": 0}
            for output in ai_review_outputs:
                review_mode = str(output.get("review_mode") or "rules_fallback").strip().lower()
                if review_mode not in ai_review_output_mode_counts:
                    review_mode = "rules_fallback"
                ai_review_output_mode_counts[review_mode] += 1
            total_volume = sum(float(o.get("offer_price") or 0) for o in offers)
            def bucket(s):
                s = str(s or "").lower()
                if "buyer signatures complete" in s or "buyer signed" in s or "signed" in s: return "signed"
                if "partial" in s: return "partial"
                if "view" in s: return "viewed"
                if "await" in s or "sent" in s or "created" in s: return "awaiting"
                return "other"

            def _agent_profile_complete(profile):
                return all(
                    str(profile.get(field) or "").strip()
                    for field in (
                        "agent_name",
                        "license_number",
                        "agent_email",
                        "agent_phone",
                        "brokerage_name",
                    )
                )

            agent_offer_counts = {}
            agent_updated_draft_count = 0
            for offer in agent_lifecycle_offers:
                user_id = str(offer.get("user_id") or "")
                if user_id:
                    agent_offer_counts[user_id] = agent_offer_counts.get(user_id, 0) + 1
                offer_status = str(offer.get("signwell_status") or offer.get("status") or "").lower()
                if "draft" in offer_status and offer.get("updated_at") and offer.get("created_at") and offer.get("updated_at") != offer.get("created_at"):
                    agent_updated_draft_count += 1
            complete_agent_profile_ids = {
                str(profile.get("user_id") or "")
                for profile in agent_profiles
                if _agent_profile_complete(profile)
            }
            agent_profile_ids = {
                str(profile.get("user_id") or "")
                for profile in agent_profiles
                if profile.get("user_id")
            }
            active_agent_subscription_ids = {
                str(subscription.get("user_id") or "")
                for subscription in subs
                if str(subscription.get("status") or "").lower() in {"active", "trialing", "free_admin"}
            }
            now = datetime.now(timezone.utc)
            agent_last_activity_at = {}
            for offer in agent_lifecycle_offers:
                user_id = str(offer.get("user_id") or "")
                if not user_id:
                    continue
                activity_at = _parse_timestamp(offer.get("updated_at") or offer.get("created_at"))
                if activity_at and (
                    user_id not in agent_last_activity_at or activity_at > agent_last_activity_at[user_id]
                ):
                    agent_last_activity_at[user_id] = activity_at
            agent_offer_user_ids = set(agent_offer_counts)
            profile_by_user_id = {
                str(profile.get("user_id") or ""): profile
                for profile in agent_profiles
                if profile.get("user_id")
            }
            trial_ending_soon_queue = []
            for subscription in subs:
                if str(subscription.get("status") or "").lower() != "trialing":
                    continue
                trial_end = _parse_timestamp(subscription.get("trial_ends_at"))
                user_id = str(subscription.get("user_id") or "")
                profile = profile_by_user_id.get(user_id, {})
                email = str(profile.get("agent_email") or "").strip()
                if not trial_end or not email or not (now <= trial_end <= now + timedelta(days=14)):
                    continue
                trial_ending_soon_queue.append({
                    "agent_name": profile.get("agent_name") or "Agent",
                    "agent_email": email,
                    "trial_ends_at": subscription.get("trial_ends_at"),
                    "reason": "Review your trial before renewal",
                    "category": "trial",
                    "priority": 1,
                })
            trial_ending_soon_queue.sort(
                key=lambda item: _parse_timestamp(item.get("trial_ends_at")) or datetime.max.replace(tzinfo=timezone.utc)
            )
            activation_follow_up_queue = []
            for user_id, profile in profile_by_user_id.items():
                email = str(profile.get("agent_email") or "").strip()
                if not email:
                    continue
                if user_id in agent_offer_user_ids and user_id not in active_agent_subscription_ids:
                    # Preserve the activation signal: Offer created without active access.
                    subscription_status = str(next((item.get("status") for item in subs if str(item.get("user_id") or "") == user_id), "") or "").lower()
                    billing_attention = subscription_status in {"past_due", "canceled", "incomplete", "incomplete_expired"}
                    activation_follow_up_queue.append({
                        "agent_name": profile.get("agent_name") or "Agent",
                        "agent_email": email,
                        "reason": "Fix billing before the next offer" if billing_attention else "Review access before the next offer",
                        "category": "billing" if billing_attention else "access",
                        "priority": 1,
                    })
                elif user_id not in complete_agent_profile_ids:
                    activation_follow_up_queue.append({
                        "agent_name": profile.get("agent_name") or "Agent",
                        "agent_email": email,
                        "reason": "Complete profile to unlock faster repeat offers",
                        "priority": 2,
                    })
                elif (
                    user_id in active_agent_subscription_ids
                    and user_id in agent_offer_user_ids
                    and user_id in agent_last_activity_at
                    and (now - agent_last_activity_at[user_id]).days >= 30
                ):
                    inactive_days = max(0, (now - agent_last_activity_at[user_id]).days)
                    activation_follow_up_queue.append({
                        "agent_name": profile.get("agent_name") or "Agent",
                        "agent_email": email,
                        "reason": "Check in before the next client offer",
                        "category": "retention",
                        "priority": 3,
                        "inactive_days": inactive_days,
                    })
                elif user_id not in agent_offer_user_ids:
                    activation_follow_up_queue.append({
                        "agent_name": profile.get("agent_name") or "Agent",
                        "agent_email": email,
                        "reason": "Create a first saved offer",
                        "priority": 3,
                    })
            activation_follow_up_queue.sort(key=lambda item: (item["priority"], item["agent_name"].lower()))
            retention_follow_up_aged_count = len([
                item for item in activation_follow_up_queue
                if item.get("category") == "retention" and int(item.get("inactive_days") or 0) >= 60
            ])
            billing_portal_open_by_source = {}
            usage_near_limit_view_count = 0
            usage_exhausted_view_count = 0
            for item in events:
                if item.get("event_type") == "subscription_usage_near_limit_viewed":
                    usage_near_limit_view_count += 1
                elif item.get("event_type") == "subscription_usage_exhausted_viewed":
                    usage_exhausted_view_count += 1
                if item.get("event_type") != "billing_portal_opened":
                    continue
                metadata = item.get("metadata") or {}
                source = str(metadata.get("source") or "unknown").strip().lower()[:80] or "unknown"
                billing_portal_open_by_source[source] = billing_portal_open_by_source.get(source, 0) + 1
            activation_dashboard_view_count = len([
                item for item in events if item.get("event_type") == "agent_activation_dashboard_viewed"
            ])
            activation_action_count = len([
                item for item in events if item.get("event_type") == "agent_activation_action"
            ])
            # A dashboard view is recorded once per browser session and stage,
            # so raw views measure activity, not conversion. Use each valid
            # account id once for the action-rate denominator and numerator;
            # retain the raw totals separately for operational volume.
            activation_dashboard_viewer_ids = {
                str(item.get("user_id") or "").strip()
                for item in events
                if item.get("event_type") == "agent_activation_dashboard_viewed"
                and str(item.get("user_id") or "").strip()
            }
            activation_action_user_ids = {
                str(item.get("user_id") or "").strip()
                for item in events
                if item.get("event_type") == "agent_activation_action"
                and str(item.get("user_id") or "").strip()
            }
            activation_dashboard_viewer_count = len(activation_dashboard_viewer_ids)
            activation_action_user_count = len(activation_action_user_ids)
            activation_primary_action_count = 0
            activation_secondary_action_count = 0
            activation_actions_by_stage = {}
            activation_subscription_actions_by_billing = {}
            repeat_activation_reuse_selection_count = 0
            for item in events:
                if item.get("event_type") != "agent_activation_action":
                    continue
                metadata = item.get("metadata") or {}
                control = str(metadata.get("control") or "unknown").strip().lower()
                if control == "primary":
                    activation_primary_action_count += 1
                elif control == "secondary":
                    activation_secondary_action_count += 1
                stage = str(metadata.get("activationKey") or "unattributed").strip().lower()[:40] or "unattributed"
                activation_actions_by_stage[stage] = activation_actions_by_stage.get(stage, 0) + 1
                if (
                    stage == "repeat"
                    and str(metadata.get("action") or "").strip().lower() == "reuse_terms"
                ):
                    repeat_activation_reuse_selection_count += 1
                if str(metadata.get("action") or "").strip().lower() == "subscribe":
                    billing = str(metadata.get("billing") or "monthly").strip().lower()
                    billing = billing if billing in {"monthly", "annual"} else "monthly"
                    activation_subscription_actions_by_billing[billing] = (
                        activation_subscription_actions_by_billing.get(billing, 0) + 1
                    )
            # This is the durable conversion point for a repeat-offer flow:
            # the workspace has opened a new, terms-only start after clearing
            # client and property data. It stays aggregate-only in the admin
            # payload so operators can assess repeat usage without seeing an
            # individual agent's activity.
            repeat_offer_terms_reuse_start_count = len([
                item for item in events if item.get("event_type") == "terms_reuse_clicked"
            ])
            repeat_offer_terms_reuse_user_count = len({
                str(item.get("user_id") or "").strip()
                for item in events
                if item.get("event_type") == "terms_reuse_clicked"
                and str(item.get("user_id") or "").strip()
            })
            # Current packet-generation failures include a small client-side
            # category. Earlier releases did not, so distinguish missing legacy
            # telemetry from malformed future metadata. This remains aggregate
            # only: error text is never returned to the dashboard.
            packet_generation_failure_categories = {
                "session", "network", "timeout", "signature_provider", "validation", "service"
            }
            packet_generation_failure_counts = {key: 0 for key in sorted(packet_generation_failure_categories)}
            packet_generation_failure_counts["legacy"] = 0
            packet_generation_failure_counts["unclassified"] = 0
            for item in events:
                if item.get("event_type") != "subscription_packet_generation_failed":
                    continue
                metadata = item.get("metadata") or {}
                raw_category = str(metadata.get("errorCategory") or "").strip().lower()
                category = (
                    raw_category if raw_category in packet_generation_failure_categories
                    else "legacy" if not raw_category
                    else "unclassified"
                )
                packet_generation_failure_counts[category] += 1
            packet_generation_failure_count = sum(packet_generation_failure_counts.values())
            # A retry is an explicit agent decision after a failed packet
            # generation. Measure whether that same offer later generates,
            # without returning an offer id, user id, error body, or any other
            # identifying activity to the dashboard.
            packet_generation_retry_count = len([
                item for item in events
                if item.get("event_type") == "subscription_packet_generation_retry_clicked"
            ])
            packet_generation_retried_offer_ids = set()
            packet_generation_recovered_offer_ids = set()
            for item in sorted(events, key=lambda row: _parse_timestamp(row.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)):
                offer_id = str(item.get("offer_id") or "").strip()
                if not offer_id:
                    continue
                if item.get("event_type") == "subscription_packet_generation_retry_clicked":
                    packet_generation_retried_offer_ids.add(offer_id)
                elif (
                    item.get("event_type") == "subscription_packet_generated"
                    and offer_id in packet_generation_retried_offer_ids
                ):
                    packet_generation_recovered_offer_ids.add(offer_id)
            packet_generation_recovered_count = len(packet_generation_recovered_offer_ids)
            # The installed PWA is the low-cost mobile-app bridge. Keep this
            # aggregate-only so product decisions can use the real install
            # funnel without returning device details or user-level activity.
            pwa_install_event_counts = {
                "shown": 0,
                "native_available": 0,
                "cta_clicked": 0,
                "prompt_opened": 0,
                "accepted": 0,
                "dismissed": 0,
                "installed": 0,
                "instructions_opened": 0,
            }
            # Keep the attribution vocabulary intentionally small. This is
            # enough to improve the install surface without retaining raw
            # device or visitor data in the admin response.
            pwa_install_surfaces = {
                "seller_success",
                "buyer_review",
                "buyer_success",
                "account_dashboard",
            }
            pwa_install_shown_surface_counts = {
                surface: 0 for surface in sorted(pwa_install_surfaces)
            }
            pwa_install_accepted_surface_counts = {
                surface: 0 for surface in sorted(pwa_install_surfaces)
            }
            for item in events:
                event_type = str(item.get("event_type") or "").strip().lower()
                if not event_type.startswith("pwa_install_"):
                    continue
                event_key = event_type.removeprefix("pwa_install_")
                if event_key in pwa_install_event_counts:
                    pwa_install_event_counts[event_key] += 1
                if event_key == "shown":
                    surface = str((item.get("metadata") or {}).get("surface") or "").strip().lower()
                    if surface in pwa_install_surfaces:
                        pwa_install_shown_surface_counts[surface] += 1
                if event_key == "accepted":
                    surface = str((item.get("metadata") or {}).get("surface") or "").strip().lower()
                    if surface in pwa_install_surfaces:
                        pwa_install_accepted_surface_counts[surface] += 1
            # A public seller may use the installed app without an account.
            # Count only the aggregate shortcut event, never a device, email,
            # property, or browser identifier.
            pwa_seller_plan_shortcut_count = len([
                item for item in events
                if item.get("event_type") == "pwa_seller_plan_opened"
            ])
            pwa_buyer_offer_shortcut_count = len([
                item for item in events
                if item.get("event_type") == "pwa_buyer_offer_opened"
            ])
            # The seller's post-intake directory step is deliberately measured
            # as an aggregate bridge: operations can see whether seller demand
            # reaches provider discovery without receiving seller, property,
            # market-query, or contact details in reporting.
            fsbo_provider_directory_open_count = len([
                item for item in events
                if item.get("event_type") == "fsbo_provider_directory_opened"
            ])
            activation_follow_up_email_start_count = len([
                item for item in events if item.get("event_type") == "activation_follow_up_email_started"
            ])
            brokerage_activation_follow_up_email_start_count = len([
                item for item in events
                if item.get("event_type") == "activation_follow_up_email_started"
                and (item.get("metadata") or {}).get("surface") == "brokerage"
            ])
            # The client records a reached milestone once per browser session so
            # a returning agent can still be attributed. Conversion reporting,
            # however, must not turn those repeat sessions into additional
            # agents. Count the privacy-safe user IDs once per milestone.
            activation_milestone_users = {"profile": set(), "first_offer": set(), "subscription": set()}
            for item in events:
                if item.get("event_type") != "agent_activation_milestone_reached":
                    continue
                milestone = str((item.get("metadata") or {}).get("milestone") or "").strip().lower()
                user_id = str(item.get("user_id") or "").strip()
                if milestone in activation_milestone_users and user_id:
                    activation_milestone_users[milestone].add(user_id)
            activation_milestone_counts = {
                milestone: len(user_ids)
                for milestone, user_ids in activation_milestone_users.items()
            }
            subscription_checkout_start_count = len([
                item for item in events if item.get("event_type") == "subscription_checkout_started"
            ])
            subscription_checkout_return_count = len([
                item for item in events if item.get("event_type") == "subscription_checkout_returned"
            ])
            subscription_checkout_redirect_count = len([
                item for item in events if item.get("event_type") == "subscription_checkout_redirected"
            ])
            subscription_checkout_failure_count = len([
                item for item in events if item.get("event_type") == "subscription_checkout_failed"
            ])
            subscription_checkout_recovery_shown_count = len([
                item for item in events if item.get("event_type") == "subscription_checkout_recovery_shown"
            ])
            subscription_checkout_recovery_start_count = len([
                item for item in events
                if item.get("event_type") == "subscription_checkout_started"
                and str((item.get("metadata") or {}).get("source") or "").strip().lower() == "subscription_cancel_recovery"
            ])
            ondemand_first_offer_start_count = len([
                item for item in events
                if item.get("event_type") == "ondemand_first_offer_started"
                and (item.get("metadata") or {}).get("source") == "ondemand"
            ])
            ondemand_landing_view_count = len([
                item for item in events if item.get("event_type") == "ondemand_landing_viewed"
            ])
            ondemand_trial_entry_count = len([
                item for item in events if item.get("event_type") == "ondemand_trial_entry_selected"
            ])
            ondemand_terms_accepted_count = len([
                item for item in events if item.get("event_type") == "ondemand_trial_terms_accepted"
            ])
            homebuyer_landing_view_count = len([
                item for item in events if item.get("event_type") == "homebuyer_landing_viewed"
            ])
            homebuyer_landing_cta_count = len([
                item for item in events if item.get("event_type") == "homebuyer_landing_cta_selected"
            ])
            homebuyer_landing_offer_started_count = len([
                item for item in events if item.get("event_type") == "homebuyer_landing_offer_started"
            ])
            agent_landing_view_count = len([
                item for item in events if item.get("event_type") == "agent_landing_viewed"
            ])
            agent_landing_cta_count = len([
                item for item in events if item.get("event_type") == "agent_landing_cta_selected"
            ])
            investor_landing_view_count = len([
                item for item in events if item.get("event_type") == "investor_landing_viewed"
            ])
            investor_landing_cta_count = len([
                item for item in events if item.get("event_type") == "investor_landing_cta_selected"
            ])
            subscription_checkout_start_by_source = {}
            subscription_checkout_return_by_source = {}
            for item in events:
                event_type = item.get("event_type")
                if event_type not in {"subscription_checkout_started", "subscription_checkout_returned"}:
                    continue
                metadata = item.get("metadata") or {}
                source = str(metadata.get("source") or "homeofferflow").strip().lower()[:80] or "homeofferflow"
                target = (
                    subscription_checkout_start_by_source
                    if event_type == "subscription_checkout_started"
                    else subscription_checkout_return_by_source
                )
                target[source] = target.get(source, 0) + 1
            seller_review_request_count = len([
                item for item in events if item.get("event_type") == "seller_review_request_sent"
            ])
            seller_review_follow_up_count = len([
                item for item in events if item.get("event_type") == "seller_review_follow_up_started"
            ])
            seller_review_viewed_count = len([
                item for item in events if item.get("event_type") == "seller_review_viewed"
            ])
            seller_review_verified_count = len([
                item for item in events if item.get("event_type") == "seller_review_verified"
            ])
            seller_review_attestation_count = len([
                item for item in events if item.get("event_type") == "seller_review_attested"
            ])
            # Public seller-page events contain only an allowlisted event name
            # and package choice.  They let operations distinguish landing-page
            # traffic from intake friction without retaining visitor, property,
            # referrer, or campaign-detail data in the Admin response.
            seller_landing_event_types = {"fsbo_landing_viewed", "fsbo_landing_cta_selected"}
            seller_landing_events = [
                item for item in events if item.get("event_type") in seller_landing_event_types
            ]
            seller_landing_view_count = len([
                item for item in seller_landing_events if item.get("event_type") == "fsbo_landing_viewed"
            ])
            seller_landing_cta_count = len([
                item for item in seller_landing_events if item.get("event_type") == "fsbo_landing_cta_selected"
            ])
            seller_landing_package_cta_counts = {}
            for item in seller_landing_events:
                if item.get("event_type") != "fsbo_landing_cta_selected":
                    continue
                service_level = str((item.get("metadata") or {}).get("serviceLevel") or "").strip().lower()
                if service_level in {"free_intake", "seller_prep", "launch_kit", "flat_fee_mls", "offer_review", "contract_help", "premium_bundle"}:
                    seller_landing_package_cta_counts[service_level] = seller_landing_package_cta_counts.get(service_level, 0) + 1
            seller_landing_package_cta_counts = dict(sorted(
                seller_landing_package_cta_counts.items(), key=lambda item: (-item[1], item[0])
            ))
            seller_intake_event_types = {"fsbo_intake_opened", "fsbo_package_selected", "fsbo_required_fields_missing", "fsbo_request_submission_started", "fsbo_request_saved"}
            seller_intake_event_counts = {event_type: len([item for item in events if item.get("event_type") == event_type]) for event_type in seller_intake_event_types}
            # Seller package choices are an allowlisted product catalog. Surface
            # only aggregate submitted-request demand; do not expose seller,
            # property, campaign, or contact data just to measure revenue fit.
            seller_package_catalog = {
                "free_intake", "seller_prep", "launch_kit", "flat_fee_mls",
                "offer_review", "contract_help", "premium_bundle",
            }
            seller_package_request_counts = {}
            for lead in seller_leads:
                package_key = str(lead.get("service_level") or "").strip().lower()
                if package_key in seller_package_catalog:
                    seller_package_request_counts[package_key] = seller_package_request_counts.get(package_key, 0) + 1
            seller_package_request_counts = dict(sorted(
                seller_package_request_counts.items(), key=lambda item: (-item[1], item[0])
            ))
            buyer_signing_reminder_copied_count = len([
                item for item in events if item.get("event_type") == "buyer_signing_reminder_copied"
            ])
            priority_signing_sync_selected_count = len([
                item for item in events if item.get("event_type") == "priority_signing_sync_selected"
            ])
            brokerage_invite_total_count = len(brokerage_invites)
            brokerage_invite_accepted_count = len([
                invite for invite in brokerage_invites if str(invite.get("status") or "").lower() == "accepted"
            ])
            brokerage_invite_pending_count = len([
                invite for invite in brokerage_invites if str(invite.get("status") or "").lower() == "pending"
            ])
            brokerage_invite_aged_count = len([
                invite for invite in brokerage_invites
                if str(invite.get("status") or "").lower() == "pending"
                and (created_at := _parse_timestamp(invite.get("created_at")))
                and created_at <= now - timedelta(days=7)
            ])
            legal_acceptance_events = [
                item for item in events if item.get("event_type") == "legal_terms_accepted"
            ]
            legal_acceptance_count = len(legal_acceptance_events)
            # Keep this conversion cohort consistent with activation milestones:
            # the wizard may emit a fresh acceptance signal for a returning
            # session, but one agent must never become multiple denominator
            # entries. Anonymous acceptance events remain useful activity
            # signals above, but cannot be attributed to a first offer.
            legal_acceptance_user_ids = {
                str(item.get("user_id") or "").strip()
                for item in legal_acceptance_events
                if str(item.get("user_id") or "").strip()
            }
            legal_acceptance_to_first_offer_count = len(
                legal_acceptance_user_ids & activation_milestone_users["first_offer"]
            )
            metrics = {
                "offerCount": len(offers),
                "homebuyerOfferCount": len([o for o in offers if o.get("role") == "homebuyer"]),
                "agentOfferCount": len([o for o in offers if o.get("role") == "agent"]),
                "agentProfileCount": len(agent_profiles),
                "agentProfileCompleteCount": len([
                    profile for profile in agent_profiles if _agent_profile_complete(profile)
                ]),
                "agentProfileIncompleteCount": len(agent_profile_ids - complete_agent_profile_ids),
                "agentFirstOfferCount": len(agent_offer_counts),
                "agentWithoutOfferCount": len(agent_profile_ids - agent_offer_user_ids),
                "agentOfferWithoutActiveSubscriptionCount": len(agent_offer_user_ids - active_agent_subscription_ids),
                "activationFollowUpCount": len(activation_follow_up_queue),
                "retentionFollowUpCount": len([
                    item for item in activation_follow_up_queue if item.get("category") == "retention"
                ]),
                "retentionFollowUpAgedCount": retention_follow_up_aged_count,
                "trialEndingSoonCount": len(trial_ending_soon_queue),
                "trialEndingWithin3DaysCount": len([
                    item for item in trial_ending_soon_queue
                    if (trial_end := _parse_timestamp(item.get("trial_ends_at")))
                    and now <= trial_end <= now + timedelta(days=3)
                ]),
                "agentRepeatOfferCount": len([
                    user_id for user_id, count in agent_offer_counts.items() if count > 1
                ]),
                "agentRepeatOfferRate": round((
                    len([user_id for user_id, count in agent_offer_counts.items() if count > 1])
                    / len(agent_offer_counts)
                ) * 100) if agent_offer_counts else 0,
                "agentUpdatedDraftCount": agent_updated_draft_count,
                "investorOfferCount": len([o for o in offers if o.get("role") == "investor"]),
                "signedCount": len([o for o in offers if bucket(o.get("signwell_status") or o.get("status")) == "signed"]),
                "awaitingCount": len([o for o in offers if bucket(o.get("signwell_status") or o.get("status")) == "awaiting"]),
                "buyerSigningReminderCopiedCount": buyer_signing_reminder_copied_count,
                "prioritySigningSyncSelectedCount": priority_signing_sync_selected_count,
                "signwellWebhookVerificationConfigured": SIGNWELL_WEBHOOK_VERIFICATION_CONFIGURED,
                "offerVolume": total_volume,
                "subscriptionCount": len(subs),
                "brokerageCount": len(brokerages),
                "partnerLeadCount": len(partner_leads),
                "sandboxPartnerLeadCount": sandbox_partner_lead_count,
                "qualifiedPartnerLeadCount": len([lead for lead in partner_leads if lead.get("status") in {"qualified", "converted"}]),
                "sellerLeadCount": len(seller_leads),
                "sellerLandingViewCount": seller_landing_view_count,
                "sellerLandingCtaCount": seller_landing_cta_count,
                "sellerLandingCtaRate": round((seller_landing_cta_count / seller_landing_view_count) * 100, 1)
                if seller_landing_view_count else 0,
                "sellerLandingPackageCtaCounts": seller_landing_package_cta_counts,
                "sellerIntakeEventCounts": seller_intake_event_counts,
                "sellerPackageRequestCounts": seller_package_request_counts,
                "sellerCampaignLeadCount": len(tracked_seller_campaign_leads),
                "sellerCampaignMediumCounts": seller_campaign_medium_counts,
                "landingAudienceSelectionCount": sum(landing_audience_selection_counts.values()),
                "landingAudienceSelectionCounts": landing_audience_selection_counts,
                "qualifiedSellerLeadCount": len([lead for lead in seller_leads if lead.get("status") in {"qualified", "converted"}]),
                "sellerFollowUpEmailStartCount": seller_follow_up_email_start_count,
                "sellerFollowUpEmailStartRate": round((seller_follow_up_email_start_count / len(seller_leads)) * 100, 1)
                if seller_leads else 0,
                "sellerReviewRequestCount": seller_review_request_count,
                "sellerReviewFollowUpCount": seller_review_follow_up_count,
                "sellerReviewFollowUpRate": round((seller_review_follow_up_count / seller_review_request_count) * 100, 1)
                if seller_review_request_count else 0,
                "sellerReviewViewedCount": seller_review_viewed_count,
                "sellerReviewVerifiedCount": seller_review_verified_count,
                "sellerReviewAttestationCount": seller_review_attestation_count,
                "sellerReviewAttestationGapCount": max(0, seller_review_verified_count - seller_review_attestation_count),
                "sellerReviewAttestationGapRate": round(
                    (max(0, seller_review_verified_count - seller_review_attestation_count) / seller_review_verified_count) * 100, 1
                ) if seller_review_verified_count else 0,
                "sellerReviewViewRate": round((seller_review_viewed_count / seller_review_request_count) * 100, 1)
                if seller_review_request_count else 0,
                "sellerReviewVerificationRate": round((seller_review_verified_count / seller_review_viewed_count) * 100, 1)
                if seller_review_viewed_count else 0,
                "sellerReviewAttestationRate": round((seller_review_attestation_count / seller_review_verified_count) * 100, 1)
                if seller_review_verified_count else 0,
                "activePartnerPlacementCount": len([placement for placement in partner_placements if placement.get("is_active")]),
                "paidPartnerActivationQueueCount": len(paid_partner_activation_queue),
                "paidPartnerLeadCount": paid_partner_lead_count,
                "partnerOnboardingReadyCount": partner_onboarding_ready_count,
                "partnerOnboardingInProgressCount": partner_onboarding_in_progress_count,
                "partnerOnboardingCompletedCount": partner_onboarding_completed_count,
                "partnerOnboardingAccessMissingCount": partner_onboarding_access_missing_count,
                "partnerOnboardingCompletionRate": round(
                    (partner_onboarding_completed_count / paid_partner_lead_count) * 100, 1
                ) if paid_partner_lead_count else 0,
                "paidPartnerAgreementConfirmedCount": paid_partner_agreement_confirmed_count,
                "paidPartnerAgreementConfirmationRate": round(
                    (paid_partner_agreement_confirmed_count / paid_partner_lead_count) * 100, 1
                ) if paid_partner_lead_count else 0,
                "paidPartnerActivationQueueAgedCount": paid_partner_activation_queue_aged_count,
                "paidPartnerActivationReadinessCounts": paid_partner_activation_readiness_counts,
                "partnerActivationRate": round((len(active_partner_source_lead_ids) / paid_partner_lead_count) * 100)
                if paid_partner_lead_count else 0,
                "partnerActivationAvgDays": partner_activation_avg_days,
                "partnerFollowUpEmailStartCount": partner_follow_up_email_start_count,
                "partnerLandingViewCount": partner_landing_view_count,
                "partnerLandingCtaCount": partner_landing_cta_count,
                "partnerLandingCtaRate": round((partner_landing_cta_count / partner_landing_view_count) * 100, 1)
                if partner_landing_view_count else 0,
                "partnerLandingTierCtaCounts": partner_landing_tier_cta_counts,
                "partnerDirectoryApplicationStartCount": partner_directory_application_start_count,
                "partnerDirectoryEmptySearchCount": partner_directory_empty_search_count,
                "partnerDirectoryEmptySearchCategoryCounts": partner_directory_empty_search_category_counts,
                "partnerCheckoutEventCounts": partner_checkout_event_counts,
                "partnerCampaignCategoryCounts": partner_campaign_category_counts,
                "partnerCampaignTierCounts": partner_campaign_tier_counts,
                "partnerCampaignChannelCounts": partner_campaign_channel_counts,
                "partnerDirectoryImpressionCount": partner_directory_impression_count,
                "partnerDirectoryOutboundClickCount": partner_directory_outbound_click_count,
                "partnerDirectoryOutboundClickRate": round(
                    (partner_directory_outbound_click_count / partner_directory_impression_count) * 100, 1
                ) if partner_directory_impression_count else 0,
                "partnerDirectoryFsboSellerPlanImpressionCount": partner_directory_fsbo_seller_plan_impression_count,
                "partnerDirectoryFsboSellerPlanOutboundClickCount": partner_directory_fsbo_seller_plan_outbound_click_count,
                "partnerCheckoutStartCount": partner_checkout_event_counts["checkout_started"],
                "partnerCheckoutStripeOpenCount": partner_checkout_event_counts["stripe_opened"],
                "partnerCheckoutCancellationCount": partner_checkout_event_counts["cancelled"],
                "partnerCheckoutRecoveryAvailableCount": partner_checkout_event_counts["cancelled"],
                "partnerCheckoutRecoveryStripeOpenCount": partner_checkout_recovery_stripe_open_count,
                "partnerCheckoutRecoveryStripeOpenRate": round(
                    (partner_checkout_recovery_stripe_open_count / partner_checkout_event_counts["cancelled"]) * 100, 1
                ) if partner_checkout_event_counts["cancelled"] else 0,
                "partnerCheckoutCompletionCount": partner_checkout_event_counts["completed"],
                "partnerCheckoutFailureCount": partner_checkout_event_counts["failed"],
                "partnerCheckoutStripeOpenRate": round(
                    (partner_checkout_event_counts["stripe_opened"] / partner_checkout_event_counts["checkout_started"]) * 100, 1
                ) if partner_checkout_event_counts["checkout_started"] else 0,
                "partnerCheckoutCompletionRate": round(
                    (partner_checkout_event_counts["completed"] / partner_checkout_event_counts["stripe_opened"]) * 100, 1
                ) if partner_checkout_event_counts["stripe_opened"] else 0,
                "partnerOnboardingLinkCreatedCount": partner_onboarding_link_created_count,
                "partnerOnboardingEmailSentCount": partner_onboarding_email_sent_count,
                "partnerOnboardingSetupIssuedCount": partner_onboarding_setup_issued_count,
                "partnerCheckoutSetupRecoveryCount": partner_checkout_setup_recovery_count,
                "eventCount": len(events),
                "roadmapCount": len(roadmap),
                "roadmapBlockedCount": len([item for item in roadmap if item.get("status") == "blocked"]),
                "qaScenarioCount": len(qa_scenarios),
                "qaVerifiedCount": len([item for item in qa_scenarios if item.get("current_status") in {"passed", "staging_passed", "production"}]),
                "releaseCount": len(releases),
                "stripeWebhookEventCount": len(stripe_webhook_events),
                "stripeWebhookEventTypeCounts": stripe_webhook_event_type_counts,
                "stripeWebhookProcessedCount": len([
                    item for item in stripe_webhook_events if item.get("processing_state") == "processed"
                ]),
                "stripeWebhookAttentionCount": len([
                    item for item in stripe_webhook_events
                    if item.get("processing_state") == "failed"
                ]),
                "stripeWebhookRetryableCount": len([
                    item for item in stripe_webhook_events
                    if item.get("processing_state") in {"received", "failed"}
                ]),
                "stripeWebhookInvoiceFailureCount": stripe_webhook_event_type_counts.get("invoice.payment_failed", 0),
                "stripeWebhookRecoveryCount": stripe_webhook_event_type_counts.get("invoice.paid", 0) + stripe_webhook_event_type_counts.get("invoice.payment_succeeded", 0),
                "billingPortalOpenCount": len([
                    item for item in events if item.get("event_type") == "billing_portal_opened"
                ]),
                "subscriptionUsageNearLimitViewCount": usage_near_limit_view_count,
                "subscriptionUsageExhaustedViewCount": usage_exhausted_view_count,
                "subscriptionCheckoutStartCount": subscription_checkout_start_count,
                "subscriptionCheckoutRedirectCount": subscription_checkout_redirect_count,
                "subscriptionCheckoutReturnCount": subscription_checkout_return_count,
                "subscriptionCheckoutFailureCount": subscription_checkout_failure_count,
                "subscriptionCheckoutRecoveryShownCount": subscription_checkout_recovery_shown_count,
                "subscriptionCheckoutRecoveryStartCount": subscription_checkout_recovery_start_count,
                "subscriptionCheckoutReturnRate": round(
                    (subscription_checkout_return_count / subscription_checkout_start_count) * 100,
                    1,
                ) if subscription_checkout_start_count else 0,
                "subscriptionCheckoutStartBySource": subscription_checkout_start_by_source,
                "subscriptionCheckoutReturnBySource": subscription_checkout_return_by_source,
                "onDemandCheckoutStartCount": subscription_checkout_start_by_source.get("ondemand", 0),
                "onDemandLandingViewCount": ondemand_landing_view_count,
                "onDemandTrialEntryCount": ondemand_trial_entry_count,
                "onDemandTermsAcceptedCount": ondemand_terms_accepted_count,
                "onDemandTermsAcceptedRate": round((ondemand_terms_accepted_count / ondemand_landing_view_count) * 100, 1)
                if ondemand_landing_view_count else 0,
                "onDemandCheckoutReturnCount": subscription_checkout_return_by_source.get("ondemand", 0),
                "onDemandCheckoutReturnRate": round(
                    (subscription_checkout_return_by_source.get("ondemand", 0)
                    / subscription_checkout_start_by_source.get("ondemand", 0)) * 100,
                    1,
                ) if subscription_checkout_start_by_source.get("ondemand", 0) else 0,
                "onDemandFirstOfferStartCount": ondemand_first_offer_start_count,
                "onDemandFirstOfferStartRate": round(
                    (ondemand_first_offer_start_count
                    / subscription_checkout_return_by_source.get("ondemand", 0)) * 100,
                    1,
                ) if subscription_checkout_return_by_source.get("ondemand", 0) else 0,
                "homebuyerLandingViewCount": homebuyer_landing_view_count,
                "homebuyerLandingCtaCount": homebuyer_landing_cta_count,
                "homebuyerLandingCtaRate": round((homebuyer_landing_cta_count / homebuyer_landing_view_count) * 100, 1)
                if homebuyer_landing_view_count else 0,
                "homebuyerLandingOfferStartedCount": homebuyer_landing_offer_started_count,
                "homebuyerLandingOfferStartRate": round((homebuyer_landing_offer_started_count / homebuyer_landing_cta_count) * 100, 1)
                if homebuyer_landing_cta_count else 0,
                "agentLandingViewCount": agent_landing_view_count,
                "agentLandingCtaCount": agent_landing_cta_count,
                "agentLandingCtaRate": round((agent_landing_cta_count / agent_landing_view_count) * 100, 1)
                if agent_landing_view_count else 0,
                "investorLandingViewCount": investor_landing_view_count,
                "investorLandingCtaCount": investor_landing_cta_count,
                "investorLandingCtaRate": round((investor_landing_cta_count / investor_landing_view_count) * 100, 1)
                if investor_landing_view_count else 0,
                "brokerageInviteSentCount": len([
                    item for item in events if item.get("event_type") == "brokerage_invite_sent"
                ]),
                "brokerageInviteResendCount": len([
                    item for item in events
                    if item.get("event_type") == "brokerage_invite_sent"
                    and (item.get("metadata") or {}).get("isResend") is True
                ]),
                "brokerageInviteTotalCount": brokerage_invite_total_count,
                "brokerageInviteAcceptedCount": brokerage_invite_accepted_count,
                "brokerageInvitePendingCount": brokerage_invite_pending_count,
                "brokerageInviteAgedCount": brokerage_invite_aged_count,
                "brokerageInviteAcceptanceRate": round(
                    (brokerage_invite_accepted_count / brokerage_invite_total_count) * 100, 1
                ) if brokerage_invite_total_count else 0,
                "legalAcceptanceCount": legal_acceptance_count,
                "billingPortalOpenBySource": billing_portal_open_by_source,
                "usageNearLimitBillingPortalOpenCount": billing_portal_open_by_source.get("usage_near_limit", 0),
                "usageExhaustedBillingPortalOpenCount": billing_portal_open_by_source.get("usage_exhausted", 0),
                "usageNearLimitBillingPortalOpenRate": round(
                    (billing_portal_open_by_source.get("usage_near_limit", 0) / usage_near_limit_view_count) * 100, 1
                ) if usage_near_limit_view_count else 0,
                "usageExhaustedBillingPortalOpenRate": round(
                    (billing_portal_open_by_source.get("usage_exhausted", 0) / usage_exhausted_view_count) * 100, 1
                ) if usage_exhausted_view_count else 0,
                "activationDashboardViewCount": activation_dashboard_view_count,
                "activationDashboardViewerCount": activation_dashboard_viewer_count,
                "activationActionCount": activation_action_count,
                "activationActionUserCount": activation_action_user_count,
                "activationActionRate": round((activation_action_user_count / activation_dashboard_viewer_count) * 100)
                if activation_dashboard_viewer_count else 0,
                "activationPrimaryActionCount": activation_primary_action_count,
                "activationSecondaryActionCount": activation_secondary_action_count,
                "activationActionsByStage": activation_actions_by_stage,
                "activationSubscriptionActionsByBilling": activation_subscription_actions_by_billing,
                "repeatActivationReuseSelectionCount": repeat_activation_reuse_selection_count,
                "repeatOfferTermsReuseStartCount": repeat_offer_terms_reuse_start_count,
                "repeatOfferTermsReuseUserCount": repeat_offer_terms_reuse_user_count,
                "packetGenerationFailureCount": packet_generation_failure_count,
                "packetGenerationFailureCounts": packet_generation_failure_counts,
                "packetGenerationRetryCount": packet_generation_retry_count,
                "packetGenerationRecoveredCount": packet_generation_recovered_count,
                "packetGenerationRetryRecoveryRate": round(
                    (packet_generation_recovered_count / packet_generation_retry_count) * 100, 1
                ) if packet_generation_retry_count else 0,
                "pwaInstallEventCounts": pwa_install_event_counts,
                "pwaInstallShownSurfaceCounts": pwa_install_shown_surface_counts,
                "pwaInstallAcceptedSurfaceCounts": pwa_install_accepted_surface_counts,
                "pwaSellerPlanShortcutCount": pwa_seller_plan_shortcut_count,
                "pwaBuyerOfferShortcutCount": pwa_buyer_offer_shortcut_count,
                "fsboProviderDirectoryOpenCount": fsbo_provider_directory_open_count,
                "pwaInstallShownCount": pwa_install_event_counts["shown"],
                "pwaInstallNativeAvailableCount": pwa_install_event_counts["native_available"],
                "pwaInstallCtaClickCount": pwa_install_event_counts["cta_clicked"],
                "pwaInstallPromptOpenCount": pwa_install_event_counts["prompt_opened"],
                "pwaInstallInstructionsOpenCount": pwa_install_event_counts["instructions_opened"],
                "pwaInstallAcceptedCount": pwa_install_event_counts["accepted"],
                "pwaInstallDismissedCount": pwa_install_event_counts["dismissed"],
                "pwaInstalledCount": pwa_install_event_counts["installed"],
                "pwaInstallCtaClickRate": round(
                    (pwa_install_event_counts["cta_clicked"] / pwa_install_event_counts["shown"]) * 100, 1
                ) if pwa_install_event_counts["shown"] else 0,
                "pwaInstallNativeAvailableRate": round(
                    (pwa_install_event_counts["native_available"] / pwa_install_event_counts["shown"]) * 100, 1
                ) if pwa_install_event_counts["shown"] else 0,
                "pwaInstallPromptOpenRate": round(
                    (pwa_install_event_counts["prompt_opened"] / pwa_install_event_counts["cta_clicked"]) * 100, 1
                ) if pwa_install_event_counts["cta_clicked"] else 0,
                "pwaInstallAcceptedRate": round(
                    (pwa_install_event_counts["accepted"] / pwa_install_event_counts["prompt_opened"]) * 100, 1
                ) if pwa_install_event_counts["prompt_opened"] else 0,
                "pwaInstallGuidanceOpenRate": round(
                    (pwa_install_event_counts["instructions_opened"] / pwa_install_event_counts["shown"]) * 100, 1
                ) if pwa_install_event_counts["shown"] else 0,
                "pwaInstallCompletionRate": round(
                    (pwa_install_event_counts["installed"] / pwa_install_event_counts["prompt_opened"]) * 100, 1
                ) if pwa_install_event_counts["prompt_opened"] else 0,
                "activationFollowUpEmailStartCount": activation_follow_up_email_start_count,
                "brokerageActivationFollowUpEmailStartCount": brokerage_activation_follow_up_email_start_count,
                "activationMilestoneCounts": activation_milestone_counts,
                "activationFirstOfferRate": round((
                    activation_milestone_counts["first_offer"] / activation_milestone_counts["profile"]
                ) * 100, 1) if activation_milestone_counts["profile"] else 0,
                "activationSubscriptionRate": round((
                    activation_milestone_counts["subscription"] / activation_milestone_counts["first_offer"]
                ) * 100, 1) if activation_milestone_counts["first_offer"] else 0,
                "feedbackCount": len(feedback),
                "missingFormRequestCount": missing_form_request_count,
                "missingFormRequestCodeCounts": missing_form_request_code_counts,
                "missingFormRecentCodeCounts": missing_form_recent_code_counts,
                "missingFormTopCodes": list(missing_form_request_code_counts)[:5],
                "missingFormPriority": _missing_form_request_priority(feedback),
                "missingFormIntakeBriefCopyCount": missing_form_intake_brief_copy_count,
                # Generated AI outputs are useful context, but do not count as
                # human calibration evidence for the five-scenario release gate.
                "aiReviewOutputCount": len(ai_review_outputs),
                "aiReviewOutputModeCounts": ai_review_output_mode_counts,
                "aiCalibrationFeedbackCount": len(_ai_calibration_scenario_ids(feedback)),
                "aiCalibrationScenarioIds": _ai_calibration_scenario_ids(feedback),
                "aiCalibrationReviewStartCount": len([
                    item for item in events if item.get("event_type") == "ai_calibration_review_started"
                ]),
                "aiCalibrationPacketDownloadCount": len([
                    item for item in events if item.get("event_type") == "ai_calibration_reviewer_packet_downloaded"
                ]),
                "aiCalibrationReviewerInviteCopyCount": len([
                    item for item in events if item.get("event_type") == "ai_calibration_reviewer_invite_copied"
                ]),
                "aiCalibrationReviewerEmailStartCount": len([
                    item for item in events if item.get("event_type") == "ai_calibration_reviewer_email_started"
                ]),
                "aiCalibrationReviewCompletionCount": len([
                    item for item in events if item.get("event_type") == "ai_calibration_review_completed"
                ]),
            }
            metrics["legalAcceptanceUserCount"] = len(legal_acceptance_user_ids)
            metrics["legalAcceptanceToFirstOfferCount"] = legal_acceptance_to_first_offer_count
            metrics["legalAcceptanceToFirstOfferRate"] = round((
                legal_acceptance_to_first_offer_count / len(legal_acceptance_user_ids)
            ) * 100, 1) if legal_acceptance_user_ids else 0
            metrics["aiCalibrationReviewCompletionRate"] = round((
                metrics["aiCalibrationReviewCompletionCount"] / metrics["aiCalibrationReviewStartCount"]
            ) * 100, 1) if metrics["aiCalibrationReviewStartCount"] else 0
            ai_calibration_scenario_funnel = {
                scenario: {"starts": 0, "packet_downloads": 0, "completions": 0}
                for scenario in AI_CALIBRATION_SCENARIOS
            }
            for item in events:
                event_type = item.get("event_type")
                metadata = item.get("metadata") or {}
                if event_type == "ai_calibration_reviewer_packet_downloaded":
                    requested = metadata.get("missingScenarios") or metadata.get("missing_scenarios") or []
                    if isinstance(requested, list):
                        for scenario in requested:
                            scenario = str(scenario or "").upper()
                            if scenario in ai_calibration_scenario_funnel:
                                ai_calibration_scenario_funnel[scenario]["packet_downloads"] += 1
                    continue
                scenario = str(metadata.get("calibrationScenario") or metadata.get("calibration_scenario") or "").upper()
                if scenario not in ai_calibration_scenario_funnel:
                    continue
                if event_type == "ai_calibration_review_started":
                    ai_calibration_scenario_funnel[scenario]["starts"] += 1
                elif event_type == "ai_calibration_review_completed":
                    ai_calibration_scenario_funnel[scenario]["completions"] += 1
            metrics["aiCalibrationScenarioFunnel"] = ai_calibration_scenario_funnel
            ai_calibration_dispositions = {"keep": 0, "revise": 0, "remove": 0}
            ai_calibration_scenario_dispositions = {
                scenario: {"keep": 0, "revise": 0, "remove": 0}
                for scenario in AI_CALIBRATION_SCENARIOS
            }
            for item in feedback:
                if not _is_ai_calibration_evidence(item):
                    continue
                scenario = str(item.get("calibration_scenario") or "").upper()
                message = str(item.get("message") or "").lower()
                for disposition in ai_calibration_dispositions:
                    if f"reviewer disposition: {disposition}" in message:
                        ai_calibration_dispositions[disposition] += 1
                        if scenario in ai_calibration_scenario_dispositions:
                            ai_calibration_scenario_dispositions[scenario][disposition] += 1
                        break
            metrics["aiCalibrationDispositionCounts"] = ai_calibration_dispositions
            metrics["aiCalibrationScenarioDispositionCounts"] = ai_calibration_scenario_dispositions
            # Five anonymized, human-reviewed scenarios are the minimum evidence
            # threshold documented for any AI scoring/calibration expansion. Keep
            # this as an explicit dashboard signal so an operator cannot confuse
            # having a feedback feed with having enough calibration evidence.
            metrics["aiCalibrationTarget"] = 5
            metrics["aiCalibrationMissingScenarioIds"] = sorted(
                AI_CALIBRATION_SCENARIOS - set(metrics["aiCalibrationScenarioIds"])
            )
            metrics["aiCalibrationReady"] = (
                set(metrics["aiCalibrationScenarioIds"]) == AI_CALIBRATION_SCENARIOS
            )
            _json(self, 200, {
                "metrics": metrics,
                "offers": offers,
                "events": events,
                "subscriptions": subs,
                "brokerages": brokerages,
                "partnerLeads": partner_leads,
                "sellerLeads": seller_leads,
                "partnerPlacements": partner_placements,
                "paidPartnerActivationQueue": paid_partner_activation_queue[:50],
                "roadmap": roadmap,
                "qaScenarios": qa_scenarios,
                "qaRuns": qa_runs,
                "releases": releases,
                "stripeWebhookEvents": stripe_webhook_events,
                "showings": [],
                "feedback": feedback,
                "activationFollowUpQueue": activation_follow_up_queue[:50],
                "trialEndingSoonQueue": trial_ending_soon_queue[:50],
            })
        except Exception as e:
            # Keep the browser response concise, while preserving enough
            # server-only context to diagnose an authenticated scope failure.
            # This is especially important for private agreement drafts: an
            # empty list is valid, but a hidden 500 otherwise has no trace.
            failed_scope = locals().get("scope") or "default"
            print(f"Admin dashboard GET failed (scope={failed_scope}): {type(e).__name__}: {str(e)[:300]}")
            _json(self, 500, {"error": str(e)})

    def do_POST(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            _json(self, 500, {"error": "Supabase env vars missing"})
            return
        try:
            import asyncio
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            verify_token = str((query.get("verify_seller_review") or [""])[0]).strip()
            attest_session = str((query.get("attest_seller_review") or [""])[0]).strip()
            if verify_token or attest_session:
                length = int(self.headers.get("Content-Length", "0") or "0")
                if length <= 0 or length > MAX_BODY_BYTES:
                    _json(self, 400, {"error": "Invalid request size."})
                    return
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                if verify_token:
                    result = asyncio.run(_verify_seller_review(verify_token, data))
                else:
                    result = asyncio.run(_attest_seller_review(attest_session, data))
                _json(self, 200, result)
                return
            user = asyncio.run(_verified_user(self.headers.get("authorization", "")))
            if not user:
                _json(self, 401, {"error": "A valid signed-in session is required."})
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > MAX_SOURCE_UPLOAD_BODY_BYTES:
                _json(self, 400, {"error": "Invalid request size."})
                return
            raw_body = self.rfile.read(length)
            data = json.loads(raw_body.decode("utf-8"))
            if data.get("action") == "upload_platform_form_source":
                source = asyncio.run(platform_source._upload_source(user, raw_body))
                _json(self, 201, {"ok": True, "source": source})
                return
            if length > MAX_BODY_BYTES:
                _json(self, 400, {"error": "Invalid request size."})
                return
            if data.get("action") == "create_brokerage_invite":
                invite = asyncio.run(_create_brokerage_invite(user, data))
                _json(self, 201, {"ok": True, "invite": invite})
                return
            if data.get("action") == "revoke_brokerage_invite":
                invite = asyncio.run(_revoke_brokerage_invite(user, data))
                _json(self, 200, {"ok": True, "invite": invite})
                return
            if data.get("action") == "update_brokerage_branding":
                branding = asyncio.run(_update_brokerage_branding(user, data))
                _json(self, 200, {"ok": True, "branding": branding})
                return
            if data.get("action") == "update_brokerage_txr_authorization":
                authorization = asyncio.run(_update_brokerage_txr_authorization(user, data))
                _json(self, 200, {"ok": True, "authorization": authorization})
                return
            if data.get("action") == "update_brokerage_shared_defaults":
                defaults = asyncio.run(_update_brokerage_shared_defaults(user, data))
                _json(self, 200, {"ok": True, "defaults": defaults})
                return
            if data.get("action") == "apply_brokerage_shared_defaults":
                profile = asyncio.run(_apply_brokerage_shared_defaults(user))
                _json(self, 200, {"ok": True, "profile": profile})
                return
            if data.get("action") == "accept_brokerage_invite":
                membership = asyncio.run(_accept_brokerage_invite(user, data))
                _json(self, 200, {"ok": True, "membership": membership})
                return
            if data.get("action") == "set_brokerage_member_status":
                result = asyncio.run(_set_brokerage_member_status(user, data))
                _json(self, 200, {"ok": True, "membership": result})
                return
            if data.get("action") == "set_brokerage_member_team":
                result = asyncio.run(_set_brokerage_member_team(user, data))
                _json(self, 200, {"ok": True, "membership": result})
                return
            if data.get("action") == "create_seller_disclosure_draft":
                draft = asyncio.run(_create_seller_disclosure_draft(user, data))
                _json(self, 201, {"status": "ok", "draft": draft, "workflowActivated": False})
                return
            if data.get("action") == "update_seller_disclosure_draft":
                draft = asyncio.run(_update_seller_disclosure_draft(user, data))
                _json(self, 200, {"status": "ok", "draft": draft, "workflowActivated": False})
                return
            if data.get("action") == "create_seller_disclosure_review_link":
                link = asyncio.run(_create_seller_disclosure_review_link(user, data))
                _json(self, 201, {"status": "ok", "reviewLink": link, "workflowActivated": False})
                return
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
            if data.get("action") == "create_txr_1506_draft":
                draft = asyncio.run(_create_txr_1506_draft(user, data))
                _json(self, 201, {"status": "ok", "agreement": draft})
                return
            if data.get("action") == "send_txr_agreement_for_signature":
                result = asyncio.run(_send_txr_agreement_for_signature(user, data))
                _json(self, 200, {"status": "ok", "signwell": result})
                return
            if not asyncio.run(_is_platform_admin(user)):
                _json(self, 403, {"error": "Admin access is not enabled for this account."})
                return
            if data.get("action") == "create_platform_partner_placement":
                payload = _parse_partner_placement(data)
                row = asyncio.run(_create_platform_partner_placement(payload))
                _json(self, 200, {"ok": True, "partnerPlacement": row})
                return
            if data.get("action") == "send_partner_agreement_for_signature":
                result = asyncio.run(_send_partner_agreement_for_signature(data))
                _json(self, 201, {"ok": True, "partnerAgreement": result})
                return
            if data.get("action") == "create_partner_onboarding_link":
                link = asyncio.run(_create_partner_onboarding_link(data))
                _json(self, 201, {"ok": True, "onboarding": link})
                return
            if data.get("action") == "email_partner_onboarding_link":
                result = asyncio.run(_email_partner_onboarding_link(data))
                _json(self, 200, {"ok": True, "onboarding": result})
                return
            if data.get("action") == "update_seller_lead":
                lead_id, status = _parse_seller_lead_update(data)
                row = asyncio.run(_update_seller_lead(lead_id, status))
                _json(self, 200, {"ok": True, "sellerLead": row})
                return
            lead_id, status, onboarding_status = _parse_partner_lead_update(data)
            row = asyncio.run(_update_partner_lead(lead_id, status, onboarding_status))
            _json(self, 200, {"ok": True, "lead": row})
        except ValueError as exc:
            _json(self, 400, {"error": str(exc)[:300]})
        except PermissionError as exc:
            _json(self, 403, {"error": str(exc)[:300]})
        except json.JSONDecodeError:
            _json(self, 400, {"error": "Invalid JSON."})
        except Exception as exc:
            print("Admin partner lead update error:", str(exc))
            _json(self, 500, {"error": "Could not update the partner lead."})
