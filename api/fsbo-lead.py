import os
import json
import re
import uuid
import hashlib
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

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
FSBO_PACKAGE_CATALOG = {
    "free_intake": ("Free Seller Intake", "$0"),
    "seller_prep": ("Seller Prep Plan", "$299"),
    "launch_kit": ("FSBO Launch Kit", "$499"),
    "flat_fee_mls": ("Flat-Fee MLS Listing", "from $1,299"),
    "offer_review": ("Seller Offer Review", "from $599"),
    "contract_help": ("Contract-to-Close Support", "from $1,999"),
    "premium_bundle": ("Premium FSBO Bundle", "from $2,999"),
}
PUBLIC_PARTNER_FIELDS = "id,partner_type,partner_name,website_url,logo_url,market_area,placement_tier"
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
        "select": "id,contact_email,partner_type,market_area,preferred_model,status,payment_status",
        "limit": "1",
    })
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
    with httpx.Client(timeout=15) as client:
        response = client.get(f"{SUPABASE_URL}/rest/v1/hof_partner_leads?{query}", headers=headers)
    if response.status_code >= 300:
        raise RuntimeError("Could not load the partner application.")
    rows = response.json() if response.text else []
    return rows[0] if isinstance(rows, list) and rows else None


def _mark_partner_checkout_started(lead_id, resume_token):
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    with httpx.Client(timeout=15) as client:
        response = client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?id=eq.{lead_id}",
            headers=headers,
            json={"payment_status": "checkout_started", "checkout_resume_token": resume_token},
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not save the checkout state.")


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
    return lead


def _public_partner_onboarding(lead):
    return {key: lead.get(key) for key in ("company_name", "partner_type", "preferred_model", "onboarding_website_url", "onboarding_logo_url", "onboarding_cta_label", "onboarding_market_area", "market_area")}


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
    return _public_partner_onboarding(rows[0])


def _create_partner_checkout(lead_id, headers):
    stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
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
    launch_price_id = os.environ.get(PRICE_ENV_BY_TIER.get(tier, ""), "")
    monthly_price_id = os.environ.get(MONTHLY_PRICE_ENV_BY_TIER.get(tier, ""), "")
    if not launch_price_id or not monthly_price_id:
        raise RuntimeError("This founding-partner tier is not configured for checkout.")

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
    _mark_partner_checkout_started(lead_id, resume_token)
    return result["url"]


def _list_public_partner_placements(category=None, market=None):
    """Return only public, platform-wide placement fields for the directory."""
    params = {
        "select": PUBLIC_PARTNER_FIELDS,
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
    return rows if isinstance(rows, list) else []


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

            if _text(data.get('request_type'), 80) == 'founding_partner_checkout':
                lead_id = _text(data.get('partner_lead_id'), 80) or ''
                try:
                    return _send(self, 200, {'url': _create_partner_checkout(lead_id, self.headers)})
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
                    return _send(self, 200, {'ok': True})
                except ValueError as exc:
                    return _send(self, 400, {'error': str(exc)})

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
                return _send(self, 200, {
                    'ok': True,
                    'partner_lead_id': row.get('id'),
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
                'status': _text(data.get('status'), 80) or 'new',
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
            return _send(self, 200, {'ok': True, 'seller_lead_id': row.get('id')})
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
