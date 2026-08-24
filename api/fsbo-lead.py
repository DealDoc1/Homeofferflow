import os
import json
import re
import uuid
import hashlib
import secrets
import html
import base64
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from lib import partner_marketplace_agreement

SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_SERVICE_ROLE_KEY = (
    os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    or os.environ.get('SUPABASE_SERVICE_ROLE')
    or os.environ.get('SUPABASE_SERVICE_KEY')
    or ''
)
MAX_BODY_BYTES = 60_000
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
LEAD_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)
ONBOARDING_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{24,128}$")
STRIPE_CHECKOUT_SESSION_RE = re.compile(r"^cs_(?:test|live)_[A-Za-z0-9_]{8,250}$")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SELLER_PLAN_FROM_EMAIL = (
    os.environ.get("SELLER_PLAN_FROM_EMAIL")
    or os.environ.get("FEEDBACK_FROM_EMAIL")
    or os.environ.get("FROM_EMAIL")
    or "offers@homeofferflow.com"
)
SELLER_PLAN_REPLY_TO = (
    os.environ.get("SELLER_PLAN_REPLY_TO")
    or os.environ.get("SUPPORT_EMAIL")
    or "support@homeofferflow.com"
)
PARTNER_APPLICATION_FROM_EMAIL = (
    os.environ.get("PARTNER_APPLICATION_FROM_EMAIL")
    or SELLER_PLAN_FROM_EMAIL
)
PARTNER_APPLICATION_REPLY_TO = (
    os.environ.get("PARTNER_APPLICATION_REPLY_TO")
    or SELLER_PLAN_REPLY_TO
)
PARTNER_AGREEMENT_COPY_EMAIL = os.environ.get("PARTNER_AGREEMENT_COPY_EMAIL", "support@homeofferflow.com").strip().lower()
PARTNER_AGREEMENT_SIGNING_ENABLED = str(os.environ.get("HOF_PARTNER_AGREEMENT_SIGNING_ENABLED", "false")).lower() in {"1", "true", "yes", "on"}
PARTNER_AGREEMENT_SIGNWELL_TEST_MODE = str(os.environ.get("HOF_PARTNER_AGREEMENT_SIGNWELL_TEST_MODE", "false")).lower() in {"1", "true", "yes", "on"}
SIGNWELL_ENABLED = str(os.environ.get("SIGNWELL_ENABLED", "false")).lower() in {"1", "true", "yes", "on"}
SIGNWELL_API_KEY = os.environ.get("SIGNWELL_API_KEY", "")
ALLOWED_PARTNER_TYPES = {
    "title",
    "lender",
    "inspection",
    "surveyor",
    "home_warranty",
    "insurance",
    "roofing",
    "hvac",
    "plumbing",
    "electrical",
    "foundation_structural",
    "general_contractor",
    "pest_termite",
    "septic_well",
    "restoration",
    "photography_video",
    "staging",
    "repairs_handyman",
    "cleaning",
    "moving_storage",
    "lawn_pool",
    "security_smart_home",
    "other",
}
ALLOWED_MODELS = {"founding_pilot", "monthly_placement", "market_exclusive", "discuss"}
ALLOWED_BUDGETS = {"under_250", "250_499", "500_999", "1000_plus", "discuss"}
PARTNER_CHECKOUT_RECOVERY_SOURCE = "partner_cancel_recovery"
FSBO_PACKAGE_CATALOG = {
    "free_intake": ("Free Seller Intake", "$0"),
    "seller_prep": ("Seller Prep Plan", "$299"),
    "launch_kit": ("FSBO Launch Kit", "$499"),
    "flat_fee_mls": ("Flat-Fee MLS Listing", "from $1,299"),
    "offer_review": ("Seller Offer Review", "from $599"),
    "contract_help": ("Contract-to-Close Support", "from $1,999"),
    "premium_bundle": ("Premium FSBO Bundle", "from $2,999"),
}
FSBO_RECEIPT_NEXT_STEPS = {
    "free_intake": (
        "Confirm your property facts and target timeline.",
        "Gather recent photos, repair notes, and any prior listing information.",
        "Watch for a HomeOfferFlow follow-up about the path that fits your goals.",
    ),
    "seller_prep": (
        "List repairs, cleaning, staging, and photo-readiness needs.",
        "Gather recent utility, improvement, and property-condition records.",
        "Keep your target timing handy for scope and provider review.",
    ),
    "launch_kit": (
        "Collect your best property photos and key upgrades.",
        "Write down showing constraints and preferred launch timing.",
        "Keep comparable homes or pricing questions ready for the planning conversation.",
    ),
    "flat_fee_mls": (
        "Collect property facts, photos, and your preferred list timing.",
        "Flag HOA, occupancy, and disclosure questions for licensed-provider review.",
        "Wait for availability, scope, and final pricing confirmation before taking payment action.",
    ),
    "offer_review": (
        "Keep every buyer offer and addendum together.",
        "Note financing, concession, option-period, and closing-date differences.",
        "Wait for qualified professional review before choosing a contract path.",
    ),
    "contract_help": (
        "Organize your accepted contract, title contact, and lender contact.",
        "Write down upcoming deadlines and unanswered transaction questions.",
        "Use the appropriate licensed party for legal, brokerage, title, and amendment decisions.",
    ),
    "premium_bundle": (
        "Collect property facts, photos, and your target timeline.",
        "List prep, marketing, MLS, offer-review, and closing-support priorities.",
        "Wait for the confirmed scope and provider plan before any paid service begins.",
    ),
}
PUBLIC_PARTNER_FIELDS = "id,partner_type,partner_name,website_url,logo_url,market_area,placement_tier"
_DIRECTORY_LOOKUP_FIELDS = f"{PUBLIC_PARTNER_FIELDS},source_lead_id"
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
PARTNER_DIRECTORY_EVENT_TYPES = {"partner_directory_impression": "shown", "partner_directory_outbound_click": "clicked"}
PARTNER_DIRECTORY_TIERS = {"core", "featured", "premier", "exclusive_market"}
PARTNER_DIRECTORY_SURFACES = {"public_directory", "fsbo_seller_plan", "pwa_provider_directory"}
FSBO_LANDING_EVENT_TYPES = {
    "fsbo_landing_viewed": "viewed",
    "fsbo_landing_cta_selected": "selected",
    "fsbo_support_paths_expanded": "expanded",
    "fsbo_guide_viewed": "viewed",
    "fsbo_guide_cta_selected": "selected",
    "fsbo_provider_directory_opened": "opened",
    "fsbo_intake_opened": "opened",
    "fsbo_package_selected": "selected",
    "fsbo_goal_selected": "selected",
    "fsbo_required_fields_ready": "ready",
    "fsbo_required_fields_missing": "incomplete",
    "fsbo_request_submission_started": "started",
    "fsbo_request_saved": "saved",
    "fsbo_seller_plan_downloaded": "downloaded",
    "fsbo_seller_plan_copied": "copied",
    "pwa_seller_plan_opened": "opened",
}
FSBO_LANDING_CHANNELS = {
    "direct", "organic", "pwa_shortcut", "email", "social", "referral", "local_event", "print", "unspecified",
}
FSBO_RECEIPT_DELIVERY_STATUSES = {"sent", "failed", "not_configured", "missing_email"}
PARTNER_APPLICATION_RECEIPT_DELIVERY_STATUSES = {"sent", "failed", "not_configured", "missing_email"}
PARTNER_APPLICATION_NEXT_STEPS = {
    "founding_pilot": (
        "Review the selected category and market while your application is being evaluated.",
        "Use secure Stripe Checkout only when you are ready to review the final launch terms before payment.",
        "After payment, complete the secure business-profile onboarding; a public placement still waits for written-agreement review.",
    ),
    "monthly_placement": (
        "Review the selected category and market while your application is being evaluated.",
        "Use secure Stripe Checkout only when you are ready to review the final featured-placement terms before payment.",
        "After payment, complete the secure business-profile onboarding; a public placement still waits for written-agreement review.",
    ),
    "market_exclusive": (
        "Confirm the category and market are the exact placement you want considered.",
        "Use secure Stripe Checkout only when you are ready to review the final terms before payment; availability is confirmed separately.",
        "After payment, complete the secure business-profile onboarding; exclusivity and public placement still wait for written-agreement review.",
    ),
}
PARTNER_LANDING_EVENT_TYPES = {
    "partner_landing_viewed": "viewed",
    "partner_landing_cta_selected": "selected",
    "partner_application_opened": "application_opened",
    "partner_application_tier_selected": "tier_selected",
    "partner_application_essentials_opened": "essentials_opened",
    "partner_application_essentials_focused": "essentials_focused",
    "partner_guide_expanded": "guide_expanded",
    "partner_directory_application_selected": "application_selected",
    "partner_directory_pricing_selected": "pricing_selected",
    "partner_directory_empty_search": "unfilled_search",
}
PARTNER_LANDING_CHANNELS = {"direct", "organic", "pwa_shortcut", "email", "social", "referral", "other"}
PARTNER_ONBOARDING_EVENT_TYPES = {
    "partner_onboarding_opened": "opened",
    "partner_onboarding_completed": "completed",
}
ONDEMAND_LANDING_EVENT_TYPES = {
    "ondemand_landing_viewed": "viewed",
    "ondemand_trial_entry_selected": "entry_selected",
    "ondemand_magic_link_requested": "magic_link_requested",
    "ondemand_trial_terms_accepted": "terms_accepted",
}
ONDEMAND_LANDING_CHANNELS = {
    "direct", "email", "social", "referral", "local_event", "print",
    "organic", "pwa_shortcut", "organic_offer_workflow", "organic_listing_workflow", "organic_lease_workflow", "agent_workspace", "agent_form_library", "unspecified",
}
HOMEBUYER_LANDING_EVENT_TYPES = {
    "homebuyer_landing_viewed": "viewed",
    "homebuyer_landing_ready_list_opened": "ready_list_opened",
    "homebuyer_landing_cta_selected": "selected",
    "homebuyer_landing_offer_started": "started",
    "homebuyer_checkout_cancelled": "cancelled",
    "homebuyer_checkout_recovery_started": "recovery_started",
    "pwa_buyer_offer_opened": "opened",
}
HOMEBUYER_LANDING_CHANNELS = {
    "direct_outreach", "email", "social", "referral", "local_event", "print", "organic", "unspecified",
}
AGENT_LANDING_EVENT_TYPES = {
    "agent_landing_viewed": "viewed",
    "agent_landing_question_one_opened": "opened",
    "agent_landing_cta_selected": "selected",
    "agent_workflow_guide_viewed": "viewed",
    "agent_workflow_guide_cta_selected": "selected",
    "agent_resource_links_expanded": "resource_expanded",
}
AGENT_LANDING_CHANNELS = {
    "direct", "organic", "pwa_shortcut", "direct_outreach", "email", "social", "referral", "local_event", "print", "unspecified",
}
AGENT_LANDING_CTA_PATHS = {
    "client_draft", "seller_listing", "lease_listing", "relationship_drafts", "lease_representation", "listing_guide", "lease_guide", "form_library_guide",
}
INVESTOR_LANDING_EVENT_TYPES = {
    "investor_landing_viewed": "viewed",
    "investor_landing_cta_selected": "selected",
    "investor_offer_guide_viewed": "viewed",
    "investor_offer_guide_cta_selected": "selected",
}
INVESTOR_LANDING_CHANNELS = {
    "direct_outreach", "email", "social", "referral", "local_event", "print", "organic", "pwa_shortcut", "unspecified",
}


def _send(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    handler.send_header('Cache-Control', 'no-store')
    handler.end_headers()
    handler.wfile.write(body)


def _text(value, max_len=500):
    if value is None:
        return None
    value = ' '.join(str(value).strip().split())
    return value[:max_len] if value else None


def _campaign_text(value, max_len):
    """Normalize standard UTM values without retaining arbitrary URL content."""
    value = _text(value, max_len)
    if not value:
        return None
    value = re.sub(r"[^A-Za-z0-9._ -]", "", value)
    return _text(value, max_len)


def _seller_campaign_payload(data):
    campaign = {
        "utm_source": _campaign_text(data.get("utm_source"), 120),
        "utm_medium": _campaign_text(data.get("utm_medium"), 120),
        "utm_campaign": _campaign_text(data.get("utm_campaign"), 160),
        "utm_content": _campaign_text(data.get("utm_content"), 160),
    }
    campaign["source"] = "tracked_seller_landing" if any(campaign.values()) else "website_fsbo_intake"
    return campaign


def _recent_matching_fsbo_lead(email, property_address, service_level):
    """Return a same-package seller request from the last 24 hours, if any."""
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    params = {
        "seller_type": "eq.fsbo",
        "seller_email": f"ilike.{email}",
        "property_address": f"eq.{property_address}",
        "service_level": f"eq.{service_level}",
        "created_at": f"gte.{since}",
        "select": "id",
        "order": "created_at.desc",
        "limit": "1",
    }
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    with httpx.Client(timeout=12.0) as client:
        response = client.get(f"{SUPABASE_URL}/rest/v1/hof_seller_leads", params=params, headers=headers)
    if response.status_code >= 300:
        raise RuntimeError("Could not check the seller request status.")
    rows = response.json() if response.text else []
    return rows[0] if isinstance(rows, list) and rows else None


def _seller_plan_receipt_steps(payload):
    """Return controlled, useful next steps without putting seller data in content."""
    service_level = _text((payload or {}).get("service_level"), 80) or "free_intake"
    return FSBO_RECEIPT_NEXT_STEPS.get(service_level, FSBO_RECEIPT_NEXT_STEPS["free_intake"])


def _send_seller_plan_confirmation(payload):
    """Best-effort transactional receipt; a valid seller request is never discarded for email failure."""
    if not RESEND_API_KEY:
        return "not_configured"
    recipient = str((payload or {}).get("seller_email") or "").strip()
    if not EMAIL_RE.match(recipient):
        return "missing_email"

    address = str(payload.get("property_address") or "your property")
    package_name = str(payload.get("package_name") or "Seller plan")
    package_price = str(payload.get("package_price") or "")
    timeline = str(payload.get("timeline") or "not sure").replace("_", " ")
    next_steps = _seller_plan_receipt_steps(payload)
    plain_steps = "\n".join(f"{index}. {step}" for index, step in enumerate(next_steps, start=1))
    html_steps = "".join(f"<li>{html.escape(step)}</li>" for step in next_steps)
    plain_text = (
        "We received your HomeOfferFlow seller plan request.\n\n"
        f"Property: {address}\n"
        f"Selected plan: {package_name}{(' (' + package_price + ')') if package_price else ''}\n"
        f"Timeline: {timeline}\n\n"
        "Your next steps:\n"
        f"{plain_steps}\n\n"
        "A qualified human review is required to confirm scope, provider involvement, availability, and final pricing before any paid service begins. "
        "This receipt is not checkout, representation, a confirmed service order, or legal advice.\n\n"
        "Have a question or want to discuss the next step sooner? Reply directly to this email."
    )
    safe_address = html.escape(address)
    safe_package = html.escape(package_name)
    safe_price = html.escape(package_price)
    safe_timeline = html.escape(timeline)
    email_payload = {
        "from": f"HomeOfferFlow <{SELLER_PLAN_FROM_EMAIL}>",
        "to": [recipient],
        "reply_to": SELLER_PLAN_REPLY_TO,
        "subject": "Your HomeOfferFlow seller plan request",
        "text": plain_text,
        "html": (
            "<h2>We received your seller plan request</h2>"
            f"<p><strong>Property:</strong> {safe_address}<br>"
            f"<strong>Selected plan:</strong> {safe_package}{(' (' + safe_price + ')') if safe_price else ''}<br>"
            f"<strong>Timeline:</strong> {safe_timeline}</p>"
            "<h3>Your next steps</h3>"
            f"<ol>{html_steps}</ol>"
            "<p>A qualified human review is required to confirm scope, provider involvement, availability, and final pricing before any paid service begins.</p>"
            "<p>This receipt is not checkout, representation, a confirmed service order, or legal advice.</p>"
            "<p>Have a question or want to discuss the next step sooner? Reply directly to this email.</p>"
        ),
    }
    try:
        with httpx.Client(timeout=12.0) as client:
            response = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": "fsbo-seller-plan-" + hashlib.sha256(
                        f"{recipient.lower()}|{address}|{package_name}".encode("utf-8")
                    ).hexdigest(),
                },
                json=email_payload,
            )
        return "sent" if response.status_code < 300 else "failed"
    except Exception:
        return "failed"


def _record_seller_plan_receipt_event(payload, delivery_status):
    """Store delivery-provider acceptance only; never store seller or property data in telemetry."""
    status = _text(delivery_status, 80)
    if status not in FSBO_RECEIPT_DELIVERY_STATUSES:
        return
    service_level = _text((payload or {}).get("service_level"), 80) or "free_intake"
    if service_level not in FSBO_PACKAGE_CATALOG:
        service_level = "free_intake"
    _record_partner_checkout_event(
        "fsbo_seller_plan_receipt_" + status,
        status,
        "Privacy-safe seller plan receipt delivery status recorded.",
        {"surface": "seller_plan_receipt", "serviceLevel": service_level},
    )


def _partner_application_receipt_steps(payload):
    """Return controlled partner next steps without creating checkout or a placement."""
    tier = _text((payload or {}).get("preferred_model"), 80) or "founding_pilot"
    return PARTNER_APPLICATION_NEXT_STEPS.get(tier, PARTNER_APPLICATION_NEXT_STEPS["founding_pilot"])


def _send_partner_application_confirmation(payload):
    """Best-effort replyable application receipt; checkout remains a separate step."""
    if not RESEND_API_KEY:
        return "not_configured"
    recipient = str((payload or {}).get("contact_email") or "").strip()
    if not EMAIL_RE.match(recipient):
        return "missing_email"

    company = str(payload.get("company_name") or "your company")
    contact = str(payload.get("contact_name") or "there")
    market = str(payload.get("market_area") or "your market")
    tier_labels = {
        "founding_pilot": "Core Partner",
        "monthly_placement": "Featured Partner",
        "market_exclusive": "Premier Partner",
    }
    tier = tier_labels.get(str(payload.get("preferred_model") or ""), "Partner placement")
    next_steps = _partner_application_receipt_steps(payload)
    plain_steps = "\n".join(f"{index}. {step}" for index, step in enumerate(next_steps, start=1))
    html_steps = "".join(f"<li>{html.escape(step)}</li>" for step in next_steps)
    plain_text = (
        f"Hi {contact},\n\n"
        "We received your HomeOfferFlow partner application.\n\n"
        f"Company: {company}\nSelected tier: {tier}\nMarket: {market}\n\n"
        "What happens next:\n"
        f"{plain_steps}\n\n"
        "Your application is saved. Secure Stripe Checkout is a separate next step and shows the final terms before any payment. "
        "Submitting this application does not collect payment, activate advertising, reserve exclusivity, create a referral relationship, or create a service agreement. "
        "Any public placement remains subject to onboarding and written-agreement review.\n\n"
        "Have a question before checkout? Reply directly to this email."
    )
    safe_company = html.escape(company)
    safe_contact = html.escape(contact)
    safe_market = html.escape(market)
    safe_tier = html.escape(tier)
    try:
        with httpx.Client(timeout=12.0) as client:
            response = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": "partner-application-" + hashlib.sha256(
                        f"{recipient.lower()}|{company}|{tier}|{market}".encode("utf-8")
                    ).hexdigest(),
                },
                json={
                    "from": f"HomeOfferFlow <{PARTNER_APPLICATION_FROM_EMAIL}>",
                    "to": [recipient],
                    "reply_to": PARTNER_APPLICATION_REPLY_TO,
                    "subject": "Your HomeOfferFlow partner application",
                    "text": plain_text,
                    "html": (
                        f"<h2>Thanks, {safe_contact} — your partner application is saved</h2>"
                        f"<p><strong>Company:</strong> {safe_company}<br>"
                        f"<strong>Selected tier:</strong> {safe_tier}<br>"
                        f"<strong>Market:</strong> {safe_market}</p>"
                        "<h3>What happens next</h3>"
                        f"<ol>{html_steps}</ol>"
                        "<p>Secure Stripe Checkout is a separate next step and shows the final terms before any payment.</p>"
                        "<p>This application does not collect payment, activate advertising, reserve exclusivity, create a referral relationship, or create a service agreement. Any public placement remains subject to onboarding and written-agreement review.</p>"
                        "<p>Have a question before checkout? Reply directly to this email.</p>"
                    ),
                },
            )
        return "sent" if response.status_code < 300 else "failed"
    except Exception:
        return "failed"


def _record_partner_application_receipt_event(payload, delivery_status):
    """Record provider acceptance in aggregate without partner contact data."""
    status = _text(delivery_status, 80)
    if status not in PARTNER_APPLICATION_RECEIPT_DELIVERY_STATUSES:
        return
    tier = _text((payload or {}).get("preferred_model"), 80) or "founding_pilot"
    if tier not in ALLOWED_MODELS:
        tier = "founding_pilot"
    _record_partner_checkout_event(
        "partner_application_receipt_" + status,
        status,
        "Privacy-safe partner application receipt delivery status recorded.",
        {"surface": "partner_application_receipt", "tier": tier},
    )


def _money(value):
    try:
        if value is None or value == '':
            return None
        return float(str(value).replace('$', '').replace(',', ''))
    except Exception:
        return None


def _choice(value, allowed, default):
    value = _text(value, 80)
    return value if value in allowed else default


def _partner_category_list(value):
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValueError("Partner categories must be a list.")
    clean = []
    for item in value[:12]:
        category = _text(item, 80)
        if category in ALLOWED_PARTNER_TYPES and category not in clean:
            clean.append(category)
    return clean


def _build_partner_payload(data):
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


def _record_partner_checkout_event(event_type, status, message, metadata=None):
    """Store aggregate partner checkout telemetry without applicant data."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or not event_type:
        return
    payload = {
        "offer_id": None,
        "user_id": None,
        "event_type": _text(event_type, 120),
        "status": _text(status, 80) or None,
        "message": _text(message, 240),
        "metadata": metadata if isinstance(metadata, dict) else {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        with httpx.Client(timeout=12.0) as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/hof_offer_events",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 300:
            print(f"Partner checkout telemetry failed: {response.status_code}")
    except Exception as exc:
        print(f"Partner checkout telemetry failed: {str(exc)[:200]}")


def _record_partner_directory_event(data):
    """Persist aggregate directory traffic without retaining visitor data."""
    event_type = _text(data.get("event_type"), 80)
    partner_id = _text(data.get("partner_id"), 80)
    partner_type = _text(data.get("partner_type"), 80)
    placement_tier = _text(data.get("placement_tier"), 80)
    directory_surface = _text(data.get("directory_surface"), 80) or "public_directory"
    if event_type not in PARTNER_DIRECTORY_EVENT_TYPES:
        raise ValueError("Unsupported directory event.")
    try:
        partner_id = str(uuid.UUID(partner_id or ""))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("A valid partner placement is required.")
    if (
        partner_type not in ALLOWED_PARTNER_TYPES
        or placement_tier not in PARTNER_DIRECTORY_TIERS
        or directory_surface not in PARTNER_DIRECTORY_SURFACES
    ):
        raise ValueError("Unsupported partner placement metadata.")
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    query = urlencode({
        "id": f"eq.{partner_id}",
        "partner_type": f"eq.{partner_type}",
        "placement_tier": f"eq.{placement_tier}",
        "is_active": "eq.true",
        "select": "id",
        "limit": "1",
    })
    with httpx.Client(timeout=8.0) as client:
        response = client.get(f"{SUPABASE_URL}/rest/v1/hof_partner_placements?{query}", headers=headers)
    if response.status_code >= 300 or not response.json():
        raise ValueError("That partner placement is unavailable.")
    _record_partner_checkout_event(event_type, PARTNER_DIRECTORY_EVENT_TYPES[event_type], "Privacy-safe public partner directory engagement recorded.", {"partnerId": partner_id, "partnerType": partner_type, "placementTier": placement_tier, "directorySurface": directory_surface})


def _record_fsbo_landing_event(data):
    """Persist aggregate seller-landing engagement without visitor or property data."""
    event_type = _text(data.get("event_type"), 80)
    service_level = _text(data.get("service_level"), 80) or "free_intake"
    channel = _text(data.get("channel"), 80).lower() or "unspecified"
    if event_type not in FSBO_LANDING_EVENT_TYPES:
        raise ValueError("Unsupported seller landing event.")
    if service_level not in FSBO_PACKAGE_CATALOG:
        raise ValueError("Unsupported seller package.")
    if channel not in FSBO_LANDING_CHANNELS:
        raise ValueError("Unsupported seller landing channel.")
    _record_partner_checkout_event(
        event_type,
        FSBO_LANDING_EVENT_TYPES[event_type],
        "Privacy-safe public seller landing engagement recorded.",
        {
            "surface": (
                "pwa_seller_plan" if event_type == "pwa_seller_plan_opened"
                else "fsbo_provider_directory" if event_type == "fsbo_provider_directory_opened"
                else "fsbo_guide" if event_type.startswith("fsbo_guide_")
                else "seller_landing"
            ),
            "serviceLevel": service_level,
            "channel": channel,
        },
    )


def _record_partner_landing_event(data):
    """Persist aggregate partner-landing engagement without applicant details."""
    event_type = _text(data.get("event_type"), 80)
    tier = _text(data.get("tier"), 80) or "unspecified"
    category = _text(data.get("category"), 80) or "unspecified"
    channel = _text(data.get("channel"), 80) or "direct"
    if event_type not in PARTNER_LANDING_EVENT_TYPES:
        raise ValueError("Unsupported partner landing event.")
    if tier not in ALLOWED_MODELS | {"unspecified"}:
        raise ValueError("Unsupported partner tier.")
    if category not in ALLOWED_PARTNER_TYPES | {"unspecified"}:
        raise ValueError("Unsupported partner category.")
    if channel not in PARTNER_LANDING_CHANNELS:
        raise ValueError("Unsupported partner landing channel.")
    _record_partner_checkout_event(
        event_type,
        PARTNER_LANDING_EVENT_TYPES[event_type],
        "Privacy-safe public partner landing engagement recorded.",
        {
            "surface": "partner_directory" if event_type in {"partner_directory_application_selected", "partner_directory_pricing_selected"} else "partner_landing",
            "tier": tier,
            "category": category,
            "channel": channel,
        },
    )


def _record_partner_onboarding_event(event_type):
    """Persist aggregate setup progress without partner or visitor identity."""
    if event_type not in PARTNER_ONBOARDING_EVENT_TYPES:
        raise ValueError("Unsupported partner onboarding event.")
    _record_partner_checkout_event(
        event_type,
        PARTNER_ONBOARDING_EVENT_TYPES[event_type],
        "Privacy-safe paid-partner setup progress recorded.",
        {"surface": "partner_onboarding"},
    )


def _record_ondemand_landing_event(data):
    """Persist aggregate OnDemand trial funnel stages without agent details."""
    event_type = _text(data.get("event_type"), 80)
    channel = _text(data.get("channel"), 80) or "unspecified"
    if event_type not in ONDEMAND_LANDING_EVENT_TYPES:
        raise ValueError("Unsupported OnDemand landing event.")
    if channel not in ONDEMAND_LANDING_CHANNELS:
        raise ValueError("Unsupported OnDemand landing channel.")
    _record_partner_checkout_event(
        event_type,
        ONDEMAND_LANDING_EVENT_TYPES[event_type],
        "Privacy-safe OnDemand trial landing engagement recorded.",
        {"surface": "ondemand_landing", "plan": "agent", "billing": "monthly", "channel": channel},
    )


def _record_homebuyer_landing_event(data):
    """Persist aggregate buyer-landing stages without buyer or offer details."""
    event_type = _text(data.get("event_type"), 80)
    channel = _text(data.get("channel"), 80) or "unspecified"
    if event_type not in HOMEBUYER_LANDING_EVENT_TYPES:
        raise ValueError("Unsupported homebuyer landing event.")
    if channel not in HOMEBUYER_LANDING_CHANNELS:
        raise ValueError("Unsupported homebuyer landing channel.")
    metadata = {"surface": "homebuyer_landing", "price": "99", "channel": channel}
    if event_type.startswith("homebuyer_checkout_"):
        metadata["surface"] = "homebuyer_checkout"
    if event_type == "pwa_buyer_offer_opened":
        metadata["surface"] = "pwa_buyer_offer"
    _record_partner_checkout_event(
        event_type,
        HOMEBUYER_LANDING_EVENT_TYPES[event_type],
        "Privacy-safe public homebuyer landing engagement recorded.",
        metadata,
    )


def _record_agent_landing_event(data):
    """Persist aggregate agent-landing stages without identity or offer data."""
    event_type = _text(data.get("event_type"), 80)
    channel = _text(data.get("channel"), 80) or "unspecified"
    cta_path = _text(data.get("cta_path"), 80)
    if event_type not in AGENT_LANDING_EVENT_TYPES:
        raise ValueError("Unsupported agent landing event.")
    if channel not in AGENT_LANDING_CHANNELS:
        raise ValueError("Unsupported agent landing channel.")
    if event_type.endswith("_cta_selected"):
        if cta_path not in AGENT_LANDING_CTA_PATHS:
            raise ValueError("Unsupported agent landing CTA path.")
    elif cta_path:
        raise ValueError("CTA path is only allowed for agent CTA events.")
    metadata = {"surface": "agent_landing", "role": "agent", "channel": channel}
    if event_type.startswith("agent_workflow_guide_"):
        metadata["surface"] = "agent_workflow_guide"
    if cta_path:
        metadata["ctaPath"] = cta_path
    _record_partner_checkout_event(
        event_type,
        AGENT_LANDING_EVENT_TYPES[event_type],
        "Privacy-safe public agent landing engagement recorded.",
        metadata,
    )


def _record_investor_landing_event(data):
    """Persist aggregate investor-landing stages without identity or offer data."""
    event_type = _text(data.get("event_type"), 80)
    channel = _text(data.get("channel"), 80) or "unspecified"
    if event_type not in INVESTOR_LANDING_EVENT_TYPES:
        raise ValueError("Unsupported investor landing event.")
    if channel not in INVESTOR_LANDING_CHANNELS:
        raise ValueError("Unsupported investor landing channel.")
    _record_partner_checkout_event(
        event_type,
        INVESTOR_LANDING_EVENT_TYPES[event_type],
        "Privacy-safe public investor landing engagement recorded.",
        {
            "surface": "investor_offer_guide" if event_type.startswith("investor_offer_guide_") else "investor_landing",
            "role": "investor",
            "channel": channel,
        },
    )


def _partner_checkout_origin(headers):
    # Derive the return target from the deployed request host, not a caller-supplied URL.
    host = (headers.get("host") or "www.homeofferflow.com").split(",", 1)[0].strip()
    if not host or any(char in host for char in "/\\@"):
        host = "www.homeofferflow.com"
    proto = (headers.get("x-forwarded-proto") or "https").split(",", 1)[0].strip().lower()
    return f"{proto if proto in {'http', 'https'} else 'https'}://{host}"


def _get_partner_lead_for_checkout(lead_id):
    query = urlencode({
        "id": f"eq.{lead_id}",
        "select": "id,contact_email,partner_type,market_area,preferred_model,status,payment_status,stripe_checkout_session_id",
        "limit": "1",
    })
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    with httpx.Client(timeout=15) as client:
        response = client.get(f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{query}", headers=headers)
    if response.status_code >= 300:
        raise RuntimeError("Could not load the partner application.")
    rows = response.json() if response.text else []
    return rows[0] if isinstance(rows, list) and rows else None


def _open_stripe_checkout_url(session_id, stripe_secret_key):
    """Return the URL only while Stripe still considers this Checkout open."""
    if not session_id:
        return None
    with httpx.Client(timeout=15) as client:
        response = client.get(
            f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
            headers={"Authorization": f"Bearer {stripe_secret_key}"},
        )
    if response.status_code >= 300:
        return None
    session = response.json() if response.text else {}
    if session.get("status") != "open":
        return None
    return session.get("url") or None


def _claim_partner_checkout_session(lead_id, expected_session_id, resume_token, session_id):
    """Atomically retain one active Checkout session per unpaid application."""
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    query = {
        "id": f"eq.{lead_id}",
        "payment_status": "neq.paid",
        "stripe_checkout_session_id": (
            f"eq.{expected_session_id}" if expected_session_id else "is.null"
        ),
    }
    with httpx.Client(timeout=15) as client:
        response = client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{urlencode(query)}",
            headers=headers,
            json={
                "payment_status": "checkout_started",
                "checkout_resume_token": resume_token,
                "stripe_checkout_session_id": session_id,
            },
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not save the checkout state.")
    rows = response.json() if response.text else []
    return rows[0] if isinstance(rows, list) and rows else None


def _mark_partner_checkout_returned(lead_id, resume_token):
    if not LEAD_ID_RE.match(lead_id) or not LEAD_ID_RE.match(resume_token):
        raise ValueError("A valid checkout return is required.")
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    query = urlencode({
        "id": f"eq.{lead_id}",
        "checkout_resume_token": f"eq.{resume_token}",
        "payment_status": "eq.checkout_started",
    })
    with httpx.Client(timeout=15) as client:
        response = client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{query}",
            headers=headers,
            json={"checkout_returned_at": datetime.now(timezone.utc).isoformat()},
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not record the checkout return.")


def _onboarding_token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _secure_url(value, field):
    value = _text(value, 500)
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{field} must be a secure https URL.")
    return value


def _get_partner_onboarding(token):
    if not ONBOARDING_TOKEN_RE.match(token or ""):
        raise ValueError("This onboarding link is invalid.")
    query = urlencode({"onboarding_token_hash": f"eq.{_onboarding_token_hash(token)}", "select": "id,company_name,partner_type,market_area,preferred_model,payment_status,status,onboarding_token_expires_at,onboarding_website_url,onboarding_logo_url,onboarding_cta_label,onboarding_market_area", "limit": "1"})
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    with httpx.Client(timeout=12) as client:
        response = client.get(f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{query}", headers=headers)
    if response.status_code >= 300:
        raise RuntimeError("Could not load partner onboarding.")
    rows = response.json() if response.text else []
    lead = rows[0] if isinstance(rows, list) and rows else None
    if not lead or str(lead.get("payment_status") or "") != "paid" or str(lead.get("status") or "") in {"declined", "waitlist"}:
        raise LookupError("This onboarding link is unavailable.")
    try:
        expires_at = datetime.fromisoformat(str(lead["onboarding_token_expires_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        raise LookupError("This onboarding link has expired.")
    if expires_at <= datetime.now(timezone.utc):
        raise LookupError("This onboarding link has expired.")
    _record_partner_onboarding_event("partner_onboarding_opened")
    return lead


def _public_partner_onboarding(lead):
    return {key: lead.get(key) for key in ("company_name", "partner_type", "preferred_model", "onboarding_website_url", "onboarding_logo_url", "onboarding_cta_label", "onboarding_market_area", "market_area")}


def _dispatch_partner_agreement_after_onboarding(lead):
    """Send exactly one commercial agreement after paid onboarding completes.

    Onboarding is never rolled back if SignWell is temporarily unavailable: the
    paid partner remains in the existing admin queue for a retry.  A successful
    dispatch atomically records the provider document id so repeated form
    submissions cannot create duplicate commercial agreements.
    """
    if not PARTNER_AGREEMENT_SIGNING_ENABLED or not SIGNWELL_ENABLED or not SIGNWELL_API_KEY:
        return {"state": "not_enabled"}
    if str(lead.get("payment_status") or "").lower() != "paid":
        return {"state": "not_paid"}
    if str(lead.get("partner_agreement_status") or "not_started").lower() in {"sent", "signed"}:
        return {"state": "already_dispatched"}
    email = str(lead.get("contact_email") or "").strip()
    if not EMAIL_RE.match(email):
        return {"state": "invalid_email"}
    lead_id = str(lead.get("id") or "")
    if not LEAD_ID_RE.match(lead_id):
        return {"state": "invalid_lead"}
    pdf = partner_marketplace_agreement.render(lead)
    payload = {
        "test_mode": PARTNER_AGREEMENT_SIGNWELL_TEST_MODE,
        "draft": False,
        "reminders": True,
        "embedded_signing": False,
        "with_signature_page": True,
        "custom_requester_name": "HomeOfferFlow",
        "name": f"HomeOfferFlow Partner Marketplace Agreement — {lead_id[:8]}",
        "subject": "HomeOfferFlow Partner Marketplace Agreement for signature",
        "message": "Please review and sign the HomeOfferFlow Partner Marketplace Agreement. A completed PDF will be sent to you and HomeOfferFlow support. This agreement does not activate a public placement until HomeOfferFlow reviews the completed record.",
        "recipients": [{"id": "1", "name": str(lead.get("contact_name") or "Partner"), "email": email}],
        "copied_contacts": [{"name": "HomeOfferFlow Support", "email": PARTNER_AGREEMENT_COPY_EMAIL}],
        "files": [{"name": "HomeOfferFlow_Partner_Marketplace_Agreement.pdf", "file_base64": base64.b64encode(pdf).decode("ascii")}],
        "metadata": {"source": "HomeOfferFlow", "partner_lead_id": lead_id, "agreement_type": "partner_marketplace"},
    }
    with httpx.Client(timeout=45) as client:
        response = client.post("https://www.signwell.com/api/v1/documents", headers={"X-Api-Key": SIGNWELL_API_KEY, "Content-Type": "application/json"}, json=payload)
    if response.status_code not in {200, 201, 202}:
        raise RuntimeError(f"Partner agreement delivery could not start: HTTP {response.status_code}.")
    result = response.json()
    document_id = str(result.get("id") or result.get("document_id") or "").strip()
    if not document_id:
        raise RuntimeError("Partner agreement delivery did not return a document id.")
    now = datetime.now(timezone.utc).isoformat()
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
    query = urlencode({"id": f"eq.{lead_id}", "partner_agreement_status": "eq.not_started"})
    with httpx.Client(timeout=12) as client:
        saved = client.patch(f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{query}", headers=headers, json={"partner_agreement_status": "sent", "partner_agreement_signwell_document_id": document_id, "partner_agreement_sent_at": now, "updated_at": now})
    if saved.status_code >= 300:
        raise RuntimeError("Partner agreement was created but its delivery status could not be saved.")
    return {"state": "sent", "document_id": document_id}


def _complete_partner_onboarding(token, data):
    lead = _get_partner_onboarding(token)
    market = _text(data.get("market_area"), 300)
    if not market:
        raise ValueError("Primary market area is required.")
    now = datetime.now(timezone.utc).isoformat()
    payload = {"onboarding_website_url": _secure_url(data.get("website_url"), "Website"), "onboarding_logo_url": _secure_url(data.get("logo_url"), "Logo URL"), "onboarding_cta_label": _text(data.get("cta_label"), 80), "onboarding_market_area": market, "onboarding_status": "complete", "onboarding_completed_at": now, "onboarding_token_hash": None, "onboarding_token_expires_at": None, "updated_at": now}
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
    with httpx.Client(timeout=12) as client:
        response = client.patch(f"{SUPABASE_URL}/rest/v1/hof_partner_leads?id=eq.{lead['id']}&onboarding_token_hash=eq.{_onboarding_token_hash(token)}", headers=headers, json=payload)
    if response.status_code >= 300:
        raise RuntimeError("Could not save partner onboarding.")
    rows = response.json() if response.text else []
    if not isinstance(rows, list) or not rows:
        raise LookupError("This onboarding link is no longer available.")
    completed = rows[0]
    try:
        _dispatch_partner_agreement_after_onboarding(completed)
    except Exception as exc:
        # Do not make a paid partner repeat onboarding because a third-party
        # agreement delivery is temporarily unavailable. The admin lifecycle
        # queue exposes the unsent record for a controlled retry.
        print("partner agreement auto-dispatch failed", repr(exc))
    _record_partner_onboarding_event("partner_onboarding_completed")
    return _public_partner_onboarding(completed)


def _retrieve_partner_checkout_session(session_id):
    """Load one Stripe Checkout session after validating its opaque identifier."""
    if not STRIPE_CHECKOUT_SESSION_RE.match(session_id or ""):
        raise ValueError("A valid checkout confirmation is required.")
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("Partner checkout is not configured.")
    with httpx.Client(timeout=12) as client:
        response = client.get(
            f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
            headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"},
        )
    if response.status_code >= 300:
        raise LookupError("That checkout confirmation is unavailable.")
    session = response.json() if response.text else {}
    return session if isinstance(session, dict) else {}


def _get_paid_partner_for_checkout_recovery(lead_id, session_id):
    """Return a paid row only when it owns the completed Stripe session."""
    query = urlencode({
        "id": f"eq.{lead_id}",
        "stripe_checkout_session_id": f"eq.{session_id}",
        "payment_status": "eq.paid",
        "select": "id,status,onboarding_status",
        "limit": "1",
    })
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    with httpx.Client(timeout=12) as client:
        response = client.get(f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{query}", headers=headers)
    if response.status_code >= 300:
        raise RuntimeError("Could not confirm partner setup access.")
    rows = response.json() if response.text else []
    return rows[0] if isinstance(rows, list) and rows else None


def _recover_partner_onboarding_from_checkout(session_id):
    """Issue a fresh, single-use setup token for the exact paid Checkout return.

    Stripe and the saved server-side session id must agree before a token can be
    issued. The response deliberately contains no partner, contact, or billing
    data; the browser receives only the short-lived setup credential it needs.
    """
    session = _retrieve_partner_checkout_session(session_id)
    metadata = session.get("metadata") if isinstance(session.get("metadata"), dict) else {}
    lead_id = str(metadata.get("partner_lead_id") or "")
    if session.get("status") != "complete" or not LEAD_ID_RE.match(lead_id):
        raise LookupError("That checkout confirmation is unavailable.")
    lead = _get_paid_partner_for_checkout_recovery(lead_id, session_id)
    if not lead:
        # The signed webhook remains authoritative for recording payment. A
        # completed return can arrive before it has stored the paid row.
        return {"state": "processing"}
    if str(lead.get("status") or "") in {"declined", "waitlist"}:
        raise LookupError("Partner setup is unavailable.")
    if str(lead.get("onboarding_status") or "") == "complete":
        return {"state": "complete"}

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    query = urlencode({
        "id": f"eq.{lead_id}",
        "stripe_checkout_session_id": f"eq.{session_id}",
        "payment_status": "eq.paid",
        "onboarding_status": "neq.complete",
    })
    payload = {
        "onboarding_token_hash": _onboarding_token_hash(token),
        "onboarding_token_expires_at": expires_at,
        "onboarding_status": "ready",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with httpx.Client(timeout=12) as client:
        response = client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{query}",
            headers=headers,
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not prepare partner setup access.")
    rows = response.json() if response.text else []
    if not isinstance(rows, list) or not rows:
        return {"state": "processing"}
    _record_partner_checkout_event(
        "partner_checkout_setup_recovered",
        "ready",
        "Partner resumed secure setup from a completed checkout.",
        {"surface": "checkout_success_return"},
    )
    return {"state": "ready", "onboarding_token": token, "expires_at": expires_at}


def _create_partner_checkout(lead_id, headers, source=None):
    stripe_secret_key = STRIPE_SECRET_KEY
    if not stripe_secret_key:
        raise RuntimeError("Partner checkout is not configured.")
    if not LEAD_ID_RE.match(lead_id):
        raise ValueError("A valid partner application is required.")
    lead = _get_partner_lead_for_checkout(lead_id)
    if not lead:
        raise LookupError("Partner application was not found.")
    if lead.get("status") in {"declined", "waitlist"}:
        raise PermissionError("This application is not eligible for checkout.")
    if lead.get("payment_status") == "paid":
        raise PermissionError("This partner application has already been paid.")

    tier = lead.get("preferred_model") or ""
    telemetry = {"tier": tier}
    if source == PARTNER_CHECKOUT_RECOVERY_SOURCE:
        telemetry["source"] = PARTNER_CHECKOUT_RECOVERY_SOURCE
    existing_session_id = lead.get("stripe_checkout_session_id") or ""
    existing_url = _open_stripe_checkout_url(existing_session_id, stripe_secret_key)
    if existing_url:
        _record_partner_checkout_event(
            "founding_partner_stripe_checkout_opened",
            "opened",
            "Partner returned to an existing secure checkout.",
            telemetry,
        )
        return existing_url

    launch_price_id = os.environ.get(PRICE_ENV_BY_TIER.get(tier, ""), "")
    monthly_price_id = os.environ.get(MONTHLY_PRICE_ENV_BY_TIER.get(tier, ""), "")
    if not launch_price_id or not monthly_price_id:
        raise RuntimeError("This founding-partner tier is not configured for checkout.")
    if launch_price_id == monthly_price_id:
        raise RuntimeError("This founding-partner tier has the same launch and renewal price configured; checkout is disabled until billing is corrected.")

    origin = _partner_checkout_origin(headers)
    resume_token = str(uuid.uuid4())
    form = {
        "mode": "subscription",
        "customer_email": lead["contact_email"],
        "client_reference_id": lead_id,
        "line_items[0][price]": launch_price_id,
        "line_items[0][quantity]": "1",
        "line_items[1][price]": monthly_price_id,
        "line_items[1][quantity]": "1",
        "allow_promotion_codes": "true",
        "payment_method_collection": "always",
        "success_url": f"{origin}/?partner=1&partner_checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{origin}/?partner=1&partner_checkout=cancelled&partner_lead_id={lead_id}&partner_resume_token={resume_token}",
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
            headers={"Authorization": f"Bearer {stripe_secret_key}"},
        )
    result = response.json() if response.text else {}
    if response.status_code >= 400 or not result.get("url"):
        message = result.get("error", {}).get("message") if isinstance(result.get("error"), dict) else None
        raise RuntimeError(message or "Could not create Stripe Checkout.")
    claimed = _claim_partner_checkout_session(
        lead_id,
        existing_session_id,
        resume_token,
        result.get("id") or "",
    )
    if not claimed:
        # Another tab/device claimed the application first. Reuse that open
        # session rather than exposing the partner to parallel subscriptions.
        refreshed_lead = _get_partner_lead_for_checkout(lead_id)
        if refreshed_lead and refreshed_lead.get("payment_status") == "paid":
            raise PermissionError("This partner application has already been paid.")
        replacement_url = _open_stripe_checkout_url(
            (refreshed_lead or {}).get("stripe_checkout_session_id") or "",
            stripe_secret_key,
        )
        if replacement_url:
            _record_partner_checkout_event(
                "founding_partner_stripe_checkout_opened",
                "opened",
                "Partner resumed the active secure checkout.",
                telemetry,
            )
            return replacement_url
        raise RuntimeError("Secure checkout was refreshed. Please try again.")
    _record_partner_checkout_event(
        "founding_partner_stripe_checkout_opened",
        "opened",
        "Partner secure checkout opened.",
        telemetry,
    )
    return result["url"]


def _list_public_partner_placements(category=None, market=None):
    """Return public placement fields plus an approved public CTA, never lead data."""
    params = {
        # source_lead_id is used only in this server-side request to recover a
        # partner's approved onboarding CTA. It is stripped before the public
        # response, together with every contact and agreement field.
        "select": _DIRECTORY_LOOKUP_FIELDS,
        "is_active": "eq.true",
        "brokerage_id": "is.null",
        "order": "partner_name.asc",
        "limit": "100",
    }
    if category in ALLOWED_PARTNER_TYPES:
        params["partner_type"] = f"eq.{category}"
    if market:
        safe_market = re.sub(r"[^a-zA-Z0-9 ,.&/-]", "", market)[:100]
        if safe_market:
            params["market_area"] = f"ilike.*{safe_market}*"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    with httpx.Client(timeout=12.0) as client:
        response = client.get(
            f"{SUPABASE_URL}/rest/v1/hof_partner_placements?{urlencode(params)}",
            headers=headers,
        )
    if response.status_code >= 300:
        raise RuntimeError(f"Supabase directory read failed with status {response.status_code}.")
    rows = response.json() if response.text else []
    if not isinstance(rows, list):
        return []
    lead_ids = {
        str(row.get("source_lead_id") or "").strip()
        for row in rows
        if isinstance(row, dict) and LEAD_ID_RE.fullmatch(str(row.get("source_lead_id") or "").strip())
    }
    ctas = {}
    if lead_ids:
        lead_params = {
            "select": "id,onboarding_cta_label",
            "id": f"in.({','.join(sorted(lead_ids))})",
        }
        with httpx.Client(timeout=12.0) as client:
            lead_response = client.get(
                f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{urlencode(lead_params)}",
                headers=headers,
            )
        if lead_response.status_code < 300:
            for lead in lead_response.json() if lead_response.text else []:
                if not isinstance(lead, dict):
                    continue
                lead_id = str(lead.get("id") or "").strip()
                label = _text(lead.get("onboarding_cta_label"), 80)
                if LEAD_ID_RE.fullmatch(lead_id) and label:
                    ctas[lead_id] = label
    public_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_lead_id = str(row.pop("source_lead_id", "") or "").strip()
        if source_lead_id in ctas:
            row["cta_label"] = ctas[source_lead_id]
        public_rows.append(row)
    return public_rows


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _send(self, 204, {})

    def do_POST(self):
        try:
            if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
                return _send(self, 500, {'error': 'Supabase service role is not configured.'})
            length = int(self.headers.get('Content-Length', '0') or '0')
            if length <= 0 or length > MAX_BODY_BYTES:
                return _send(self, 400, {'error': 'Invalid request size.'})
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            if _text(data.get('request_type'), 80) == 'partner_directory_event':
                try:
                    _record_partner_directory_event(data)
                    return _send(self, 200, {'ok': True})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'fsbo_landing_event':
                try:
                    _record_fsbo_landing_event(data)
                    return _send(self, 200, {'ok': True})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'partner_landing_event':
                try:
                    _record_partner_landing_event(data)
                    return _send(self, 200, {'ok': True})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'ondemand_landing_event':
                try:
                    _record_ondemand_landing_event(data)
                    return _send(self, 200, {'ok': True})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'homebuyer_landing_event':
                try:
                    _record_homebuyer_landing_event(data)
                    return _send(self, 200, {'ok': True})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'agent_landing_event':
                try:
                    _record_agent_landing_event(data)
                    return _send(self, 200, {'ok': True})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'investor_landing_event':
                try:
                    _record_investor_landing_event(data)
                    return _send(self, 200, {'ok': True})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'founding_partner_checkout':
                lead_id = _text(data.get('partner_lead_id'), 80) or ''
                source = _text(data.get('checkout_source'), 80).lower()
                if source != PARTNER_CHECKOUT_RECOVERY_SOURCE:
                    source = None
                try:
                    return _send(self, 200, {'url': _create_partner_checkout(lead_id, self.headers, source)})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})
                except LookupError as exc:
                    return _send(self, 404, {'error': str(exc)})
                except PermissionError as exc:
                    return _send(self, 409, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'founding_partner_checkout_returned':
                try:
                    _mark_partner_checkout_returned(
                        _text(data.get('partner_lead_id'), 80) or '',
                        _text(data.get('partner_resume_token'), 80) or '',
                    )
                    _record_partner_checkout_event(
                        'founding_partner_checkout_cancelled',
                        'cancelled',
                        'Partner returned from secure checkout without completing payment.',
                    )
                    return _send(self, 200, {'ok': True})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'founding_partner_checkout_setup':
                try:
                    result = _recover_partner_onboarding_from_checkout(
                        _text(data.get('session_id'), 300) or ''
                    )
                    if result.get('state') == 'processing':
                        return _send(self, 202, {'ok': True, 'state': 'processing'})
                    if result.get('state') == 'complete':
                        return _send(self, 200, {'ok': True, 'state': 'complete'})
                    return _send(self, 200, {'ok': True, **result})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})
                except LookupError as exc:
                    return _send(self, 404, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'partner_onboarding_get':
                try:
                    return _send(self, 200, {'ok': True, 'partner': _public_partner_onboarding(_get_partner_onboarding(_text(data.get('onboarding_token'), 160) or ''))})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})
                except LookupError as exc:
                    return _send(self, 404, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'partner_onboarding_submit':
                try:
                    return _send(self, 200, {'ok': True, 'partner': _complete_partner_onboarding(_text(data.get('onboarding_token'), 160) or '', data)})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})
                except LookupError as exc:
                    return _send(self, 409, {'error': str(exc)})

            if _text(data.get('request_type'), 80) == 'founding_partner':
                # Quietly accept bots that fill the hidden field without polluting the CRM.
                if _text(data.get('company_website_confirm'), 250):
                    return _send(self, 200, {'ok': True})
                payload = _build_partner_payload(data)
                row = _insert_partner_lead(payload)
                application_receipt = _send_partner_application_confirmation(payload)
                _record_partner_application_receipt_event(payload, application_receipt)
                # Browser analytics cannot populate the private Admin
                # Dashboard for an unauthenticated applicant. Record only the
                # aggregate lifecycle and selected tier on the server.
                _record_partner_checkout_event(
                    'founding_partner_checkout_started',
                    'started',
                    'Partner checkout intent recorded after required details and consent.',
                    {'tier': payload['preferred_model']},
                )
                _record_partner_checkout_event(
                    'founding_partner_application_saved',
                    'saved',
                    'Partner application saved before secure checkout.',
                    {'tier': payload['preferred_model']},
                )
                return _send(self, 200, {
                    'ok': True,
                    'partner_lead_id': row.get('id'),
                    'partner_application_email': application_receipt,
                    'message': 'Partner interest received.',
                })

            # Quietly accept bots that fill the hidden seller field without
            # polluting the public FSBO follow-up queue.
            if _text(data.get('fsbo_website_confirm'), 250):
                return _send(self, 200, {'ok': True})

            property_address = _text(data.get('property_address') or data.get('address'), 500)
            seller_email = _text(data.get('seller_email') or data.get('email'), 250)
            if not property_address or not seller_email:
                return _send(self, 400, {'error': 'Property address and seller email are required.'})
            if not EMAIL_RE.match(seller_email):
                return _send(self, 400, {'error': 'Enter a valid seller email.'})

            partner_categories = _partner_category_list(data.get('partner_categories'))
            service_level = _text(data.get('service_level'), 80) or 'free_intake'
            if service_level not in FSBO_PACKAGE_CATALOG:
                return _send(self, 400, {'error': 'Choose a supported seller package.'})
            # Package labels and price guidance are commercial records, not
            # browser authority. Canonicalize them server-side for reliable
            # lead routing and honest follow-up.
            package_name, package_price = FSBO_PACKAGE_CATALOG[service_level]
            timeline = _text(data.get('timeline'), 80) or 'not_sure'
            campaign = _seller_campaign_payload(data)

            existing = _recent_matching_fsbo_lead(seller_email.lower(), property_address, service_level)
            if existing:
                return _send(self, 200, {"ok": True, "seller_lead_id": existing.get("id"), "duplicate": True})

            payload = {
                'seller_type': 'fsbo',
                'property_address': property_address,
                'property_city': _text(data.get('property_city'), 120),
                'property_county': _text(data.get('property_county'), 120),
                'property_state': _text(data.get('property_state'), 20) or 'TX',
                'property_zip': _text(data.get('property_zip'), 20),
                'seller_name': _text(data.get('seller_name') or data.get('name'), 250),
                'seller_email': seller_email.lower(),
                'seller_phone': _text(data.get('seller_phone') or data.get('phone'), 80),
                'asking_price': _money(data.get('asking_price')),
                'mortgage_balance': _money(data.get('mortgage_balance')),
                'desired_close_date': _text(data.get('desired_close_date'), 40),
                'service_level': service_level,
                'package_name': package_name,
                'package_price': package_price,
                'timeline': timeline,
                'partner_categories': partner_categories,
                **campaign,
                'notes': _text(data.get('notes'), 1500),
                # Public seller intake is never allowed to choose its CRM
                # state.  Qualification and any later activation happen only
                # through an authorized operations workflow.
                'status': 'new',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }

            headers = {
                'apikey': SUPABASE_SERVICE_ROLE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation',
            }
            url = f'{SUPABASE_URL}/rest/v1/hof_seller_leads'
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, headers=headers, json=payload)
            if resp.status_code >= 300:
                return _send(self, 500, {'error': 'Could not save seller lead.', 'detail': resp.text[:500]})
            row = resp.json()[0] if resp.text and resp.text.strip().startswith('[') else {}
            email_delivery = _send_seller_plan_confirmation(payload)
            _record_seller_plan_receipt_event(payload, email_delivery)
            return _send(self, 200, {
                'ok': True,
                'seller_lead_id': row.get('id'),
                'seller_plan_email': email_delivery,
            })
        except ValueError as exc:
            return _send(self, 400, {'error': str(exc)[:300]})
        except json.JSONDecodeError:
            return _send(self, 400, {'error': 'Invalid JSON.'})
        except Exception as exc:
            return _send(self, 500, {'error': str(exc)[:500]})

    def do_GET(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return _send(self, 500, {'error': 'Supabase service role is not configured.'})
        try:
            query = parse_qs(urlparse(self.path).query)
            if query.get('partner_directory', [''])[0] != '1':
                return _send(self, 404, {'error': 'Not found.'})
            category = _text(query.get('category', [''])[0], 80)
            market = _text(query.get('market', [''])[0], 100)
            rows = _list_public_partner_placements(category, market)
            return _send(self, 200, {'ok': True, 'partners': rows})
        except Exception as exc:
            return _send(self, 500, {'error': 'Could not load partner directory.', 'detail': str(exc)[:300]})
