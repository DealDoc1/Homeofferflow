"""Server-only fixed-price seller checkout requests.

This module is intentionally separate from the administrative dashboard. The
dashboard can request a link after access and scope checks, but customer and
payment data never belong in dashboard response construction or metrics.
"""

import os
import re
import uuid
import urllib.parse
from datetime import datetime, timezone

import httpx


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_SERVICE_KEY") or ""
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
PUBLIC_APP_ORIGIN = (os.environ.get("PUBLIC_APP_URL") or "https://www.homeofferflow.com").rstrip("/")
FROM_EMAIL = os.environ.get("SELLER_PLAN_FROM_EMAIL") or os.environ.get("FEEDBACK_FROM_EMAIL") or os.environ.get("FROM_EMAIL") or "offers@homeofferflow.com"
REPLY_TO = os.environ.get("SELLER_PLAN_REPLY_TO") or os.environ.get("SUPPORT_EMAIL") or "support@homeofferflow.com"
EMAIL_RE = re.compile(r"(?=.{3,254}$)[^@\s]+@[^@\s]+\.[^@\s]+$")
PACKAGES = {
    "seller_prep": {"name": "HomeOfferFlow Seller Prep Plan", "amount": 29900},
    "launch_kit": {"name": "HomeOfferFlow FSBO Launch Kit", "amount": 49900},
}


def _headers():
    return {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "Content-Type": "application/json"}


def _escape(value):
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


async def create_request(data):
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("Seller payment requests are not configured.")
    lead_id = str((data or {}).get("seller_lead_id") or "").strip()
    try:
        lead_id = str(uuid.UUID(lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("A valid seller lead ID is required.")
    if (data or {}).get("scope_confirmed") is not True:
        raise ValueError("Confirm the seller's scope and fixed price before sending payment.")
    async with httpx.AsyncClient(timeout=15) as client:
        lookup = await client.get(
            f"{SUPABASE_URL}/rest/v1/hof_seller_leads?id=eq.{urllib.parse.quote(lead_id)}&select=id,seller_email,service_level,status,seller_checkout_status,seller_checkout_session_id&limit=1",
            headers=_headers(),
        )
    if lookup.status_code >= 300 or not isinstance(lookup.json(), list) or not lookup.json():
        raise ValueError("Seller lead was not found.")
    lead = lookup.json()[0]
    if str(lead.get("status") or "").lower() != "qualified":
        raise PermissionError("Qualify the seller lead before sending a payment request.")
    package_key = str(lead.get("service_level") or "").strip().lower()
    package = PACKAGES.get(package_key)
    if not package:
        raise PermissionError("This seller package requires a confirmed quote instead of online checkout.")
    checkout_status = str(lead.get("seller_checkout_status") or "").lower()
    if checkout_status == "paid":
        raise PermissionError("This seller package has already been paid.")
    # Payment links are personal and a single fixed-price request is enough.
    # Do not make a second active Checkout session just because an admin
    # refreshes or double-clicks after the first request was saved.
    if checkout_status == "sent" or str(lead.get("seller_checkout_session_id") or "").startswith("cs_"):
        raise PermissionError("A secure payment request has already been sent for this seller.")
    email = str(lead.get("seller_email") or "").strip().lower()
    if not EMAIL_RE.fullmatch(email):
        raise ValueError("This seller lead has no valid email address.")
    form = {
        "mode": "payment", "customer_email": email,
        "success_url": f"{PUBLIC_APP_ORIGIN}/sellers?seller_payment=success",
        "cancel_url": f"{PUBLIC_APP_ORIGIN}/sellers?seller_payment=cancelled",
        "line_items[0][price_data][currency]": "usd",
        "line_items[0][price_data][unit_amount]": str(package["amount"]),
        "line_items[0][price_data][product_data][name]": package["name"],
        "line_items[0][quantity]": "1", "metadata[seller_lead_id]": lead_id,
        "metadata[seller_package]": package_key, "client_reference_id": lead_id,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            auth=(STRIPE_SECRET_KEY, ""),
            data=form,
            headers={"Idempotency-Key": "seller-checkout-" + lead_id},
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not create the seller payment request.")
    session = response.json()
    checkout_url, session_id = str(session.get("url") or "").strip(), str(session.get("id") or "").strip()
    if not checkout_url.startswith("https://") or not session_id.startswith("cs_"):
        raise RuntimeError("Could not create the seller payment request.")
    now = datetime.now(timezone.utc).isoformat()
    payload = {"seller_checkout_status": "sent", "seller_checkout_session_id": session_id, "seller_checkout_price_cents": package["amount"], "seller_checkout_requested_at": now, "updated_at": now}
    async with httpx.AsyncClient(timeout=12) as client:
        saved = await client.patch(f"{SUPABASE_URL}/rest/v1/hof_seller_leads?id=eq.{urllib.parse.quote(lead_id)}", headers={**_headers(), "Prefer": "return=representation"}, json=payload)
    if saved.status_code >= 300:
        raise RuntimeError("Seller payment link was created but could not be saved.")
    delivery = "not_configured"
    if RESEND_API_KEY:
        safe_name, safe_url = _escape(package["name"]), _escape(checkout_url)
        email_payload = {
            "from": f"HomeOfferFlow <{FROM_EMAIL}>", "to": [email], "reply_to": REPLY_TO,
            "subject": f"Complete payment for your {package['name']}",
            "tags": [{"name": "email_type", "value": "seller_checkout"}, {"name": "seller_package", "value": package_key}],
            "text": f"Your HomeOfferFlow scope has been confirmed. Complete secure payment for {package['name']}: {checkout_url}\n\nThis link is personal. Payment is for the confirmed package only and does not create legal or brokerage representation.",
            "html": ('<div style="font-family:Arial,sans-serif;line-height:1.5;color:#172033;">'
                     f"<h2>Your {safe_name} is ready</h2><p>Your HomeOfferFlow scope has been confirmed. Use this private link to complete secure payment.</p>"
                     f'<p><a href="{safe_url}" style="display:inline-block;padding:12px 18px;border-radius:8px;background:#123047;color:#ffffff;text-decoration:none;font-weight:700;">Complete secure payment</a></p>'
                     "<p style=\"font-size:13px;color:#5f6b7a;\">Payment is for the confirmed package only and does not create legal or brokerage representation. Please do not forward this link.</p></div>"),
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                sent = await client.post("https://api.resend.com/emails", headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json", "Idempotency-Key": "seller-checkout-" + session_id}, json=email_payload)
            delivery = "sent" if sent.status_code < 300 else "failed"
        except Exception:
            delivery = "failed"
    return {"sellerLeadId": lead_id, "package": package_key, "amountCents": package["amount"], "checkoutUrl": checkout_url, "delivery": delivery}


async def recover_request(data):
    """Return an already-sent active Checkout link without creating or emailing another one."""
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("Seller payment requests are not configured.")
    lead_id = str((data or {}).get("seller_lead_id") or "").strip()
    try:
        lead_id = str(uuid.UUID(lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("A valid seller lead ID is required.")
    if (data or {}).get("scope_confirmed") is not True:
        raise ValueError("Confirm the seller's scope and fixed price before retrieving payment.")
    async with httpx.AsyncClient(timeout=15) as client:
        lookup = await client.get(
            f"{SUPABASE_URL}/rest/v1/hof_seller_leads?id=eq.{urllib.parse.quote(lead_id)}&select=id,service_level,status,seller_checkout_status,seller_checkout_session_id&limit=1",
            headers=_headers(),
        )
    if lookup.status_code >= 300 or not isinstance(lookup.json(), list) or not lookup.json():
        raise ValueError("Seller lead was not found.")
    lead = lookup.json()[0]
    package_key = str(lead.get("service_level") or "").strip().lower()
    if str(lead.get("status") or "").lower() != "qualified" or package_key not in PACKAGES:
        raise PermissionError("This seller package is not ready for online payment.")
    session_id = str(lead.get("seller_checkout_session_id") or "").strip()
    if str(lead.get("seller_checkout_status") or "").lower() != "sent" or not session_id.startswith("cs_"):
        raise PermissionError("There is no active seller payment link to retrieve.")
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(f"https://api.stripe.com/v1/checkout/sessions/{urllib.parse.quote(session_id, safe='')}", auth=(STRIPE_SECRET_KEY, ""))
    if response.status_code >= 300:
        raise RuntimeError("Could not retrieve the seller payment link.")
    session = response.json()
    checkout_url = str(session.get("url") or "").strip()
    if str(session.get("id") or "") != session_id or not checkout_url.startswith("https://"):
        raise RuntimeError("The seller payment link is no longer available.")
    return {"sellerLeadId": lead_id, "package": package_key, "checkoutUrl": checkout_url, "delivery": "existing"}
