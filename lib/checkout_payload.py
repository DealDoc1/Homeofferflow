"""Load immutable paid-checkout packets using service-only access.

Call only after verifying the Stripe event or the internal forwarding HMAC.
Browser subscription generation must never use a checkout payload reference.
"""
import hashlib
import hmac
import json
import re

import httpx

MAX_BYTES = 4 * 1024 * 1024
FAILURE = 'The saved checkout packet could not be verified. Delivery will be retried.'


def cleanup_expired_checkout_payload(event, *, supabase_url, service_key, client=None):
    """Remove only a verified expired/unpaid checkout's private staging copy.

    This function is not a public API. The webhook must authenticate the event
    and enforce live/test database isolation before invoking it. Do not call
    it from browser cancellation, a time-based sweep, or payment completion.
    """
    if event.get('type') != 'checkout.session.expired':
        return False
    session = (event.get('data') or {}).get('object') or {}
    metadata = session.get('metadata') or {}
    if (metadata.get('plan') != 'self' or session.get('mode') != 'payment'
            or session.get('status') != 'expired' or session.get('payment_status') != 'unpaid'
            or metadata.get('partner_lead_id') or metadata.get('seller_lead_id')
            or session.get('recovered_from')):
        return False
    # Recovery links clone the original checkout. Preserve its packet even
    # when the first session is expired; age alone is not safe cleanup proof.
    after_expiration = session.get('after_expiration')
    if after_expiration:
        if not isinstance(after_expiration, dict):
            return False
        recovery = after_expiration.get('recovery')
        if recovery and (not isinstance(recovery, dict) or recovery.get('enabled') is not False or recovery.get('url')):
            return False
    reference = metadata.get('offer_payload_id', '')
    fingerprint = metadata.get('offer_payload_sha256', '')
    session_id = session.get('id', '')
    if (not isinstance(reference, str) or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', reference)
            or not isinstance(fingerprint, str) or not re.fullmatch(r'[0-9a-f]{64}', fingerprint)
            or not isinstance(session_id, str) or not re.fullmatch(r'cs_[A-Za-z0-9_]+', session_id)):
        return False
    failure = 'Expired checkout cleanup could not be confirmed.'
    if not supabase_url or not service_key:
        raise ValueError(failure)
    try:
        response = (client or httpx).delete(
            supabase_url.rstrip('/') + '/rest/v1/hof_checkout_payloads', timeout=20,
            headers={'apikey': service_key, 'Authorization': 'Bearer ' + service_key, 'Prefer': 'return=minimal'},
            params={'id': 'eq.' + reference, 'payload_sha256': 'eq.' + fingerprint,
                    # An acknowledgement failure may leave this session unbound.
                    # Never delete a payload already bound to another session.
                    'or': f'(stripe_session_id.eq.{session_id},stripe_session_id.is.null)'})
        if response.status_code != 204:
            raise ValueError(failure)
        # Zero matching rows is also success: Stripe retries are idempotent.
        return True
    except Exception as error:
        raise ValueError(failure) from error


def load_checkout_payload(session, *, supabase_url, service_key, client=None):
    metadata = session.get('metadata') or {}
    reference = metadata.get('offer_payload_id', '')
    fingerprint = metadata.get('offer_payload_sha256', '')
    session_id = session.get('id', '')
    if (not isinstance(reference, str) or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', reference)
            or not isinstance(fingerprint, str) or not re.fullmatch(r'[0-9a-f]{64}', fingerprint)
            or not isinstance(session_id, str) or not re.fullmatch(r'cs_[A-Za-z0-9_]+', session_id)
            or metadata.get('plan') != 'self' or session.get('mode') != 'payment'
            or session.get('payment_status') not in {'paid', 'no_payment_required'}
            or not supabase_url or not service_key):
        raise ValueError(FAILURE)
    try:
        response = (client or httpx).get(
            supabase_url.rstrip('/') + '/rest/v1/hof_checkout_payloads', timeout=20,
            headers={'apikey': service_key, 'Authorization': 'Bearer ' + service_key},
            params={'id': 'eq.' + reference, 'stripe_session_id': 'eq.' + session_id,
                    'payload_sha256': 'eq.' + fingerprint,
                    'select': 'id,payload_text,payload_sha256,stripe_session_id', 'limit': '1'})
        if response.status_code != 200:
            raise ValueError(FAILURE)
        rows = response.json()
        if not isinstance(rows, list) or len(rows) != 1:
            raise ValueError(FAILURE)
        row = rows[0]
        if row['id'] != reference or row['stripe_session_id'] != session_id or row['payload_sha256'] != fingerprint:
            raise ValueError(FAILURE)
        raw = row['payload_text'].encode('utf8')
        if len(raw) > MAX_BYTES or not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), fingerprint):
            raise ValueError(FAILURE)
        offer = json.loads(raw)
        email = session.get('customer_email') or (session.get('customer_details') or {}).get('email', '')
        if (not isinstance(offer, dict) or offer.get('_plan') != 'self'
                or not email or offer.get('_paymentEmail', '').casefold() != email.strip().casefold()):
            raise ValueError(FAILURE)
        return offer
    except Exception as error:
        # Provider bodies and packet contents are private, including on failure.
        raise ValueError(FAILURE) from error
