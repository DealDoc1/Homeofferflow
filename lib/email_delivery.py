"""Durable transactional email protocol; no provider or database secrets here.

The storage adapter owns authorization and atomic writes. Store an immutable
payload before sending: regenerated PDFs can differ in byte-level metadata,
and Resend rejects a reused idempotency key with a different request body.
Never fall back to an untracked send when the store is unavailable.
"""
import copy
import hashlib
import json
import math
import time


# Resend retains keys for 24 hours. Leave an hour for clock skew, transit,
# pauses, and a request in flight; do not renew this window on retries.
SAFE_RETRY_SECONDS = 23 * 60 * 60


class EmailDeliveryPending(RuntimeError):
    """Acceptance is unconfirmed; do not claim inbox delivery or send anew."""


class EmailDeliveryNeedsReview(EmailDeliveryPending):
    """The safe provider replay window elapsed without durable confirmation."""


def payload_fingerprint(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                         allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def delivery_key(purpose, trusted_identity):
    """Caller must derive identity from a verified checkout or owned record.

    The key intentionally contains no customer email, address, or raw checkout
    token. Different notification purposes for one order cannot collide.
    """
    if not isinstance(purpose, str) or not purpose.strip():
        raise ValueError('Email purpose is required.')
    if not isinstance(trusted_identity, str) or not trusted_identity.strip():
        raise ValueError('A verified email delivery identity is required.')
    return 'hof-email-v1-' + payload_fingerprint([purpose, trusted_identity])


def deliver_email_once(*, key, payload, reserve, begin_attempt, accept, send,
                       clock=time.time):
    """Callbacks use committed writes, never locks held across provider HTTP.

    reserve(key, payload, fingerprint): insert once, or read existing row. It
    must never replace an existing payload. Return an authoritative row.
    begin_attempt(row): atomically set first_attempt_at ONCE (epoch seconds),
    or return the previously stamped/accepted row after a concurrent update.
    accept(row, provider_id): return literal True only when acceptance is
    durably saved (or the same ID was already accepted). May discard payload
    after acceptance; retain key, fingerprint and provider ID as a tombstone.
    send(payload, key): send exactly these values; return {'id': provider_id}.

    Expected row fields: delivery_key, payload, payload_fingerprint, status
    ('pending' or 'accepted'), first_attempt_at, provider_id. This protocol is
    used by checkout only with its private storage adapter and schema.
    """
    if not isinstance(key, str) or not key.startswith('hof-email-v1-') or len(key) != 77:
        raise ValueError('Invalid email delivery key.')
    if not isinstance(payload, dict):
        raise ValueError('Email payload must be an object.')
    proposed = copy.deepcopy(payload)
    proposed_fingerprint = payload_fingerprint(proposed)

    def validate(row):
        if not isinstance(row, dict) or row.get('delivery_key') != key:
            raise EmailDeliveryPending('The saved email request could not be confirmed.')
        if row.get('status') == 'accepted':
            provider_id = row.get('provider_id')
            if not isinstance(provider_id, str) or not provider_id.strip():
                raise EmailDeliveryPending('The saved email acceptance needs a status check.')
            return {'id': provider_id, 'status': 'accepted', 'recovered': True}
        if row.get('status') != 'pending' or not isinstance(row.get('payload'), dict):
            raise EmailDeliveryPending('The saved email request needs a status check.')
        try:
            valid = payload_fingerprint(row['payload']) == row.get('payload_fingerprint')
        except (TypeError, ValueError):
            valid = False
        if not valid:
            raise EmailDeliveryPending('The saved email contents could not be confirmed.')
        return None

    try:
        row = reserve(key, proposed, proposed_fingerprint)
    except Exception as error:
        raise EmailDeliveryPending('The email request could not be saved. No new email was requested.') from error
    recovered = validate(row)
    if recovered:
        return recovered
    # A retry must use the first saved body, not today's regenerated PDF,
    # current template, changed signing status, or changed recipient list.
    frozen_fingerprint = row['payload_fingerprint']
    try:
        row = begin_attempt(copy.deepcopy(row))
    except Exception as error:
        raise EmailDeliveryPending('The email attempt could not be saved. No new email was requested.') from error
    recovered = validate(row)
    if recovered:
        return recovered
    if row['payload_fingerprint'] != frozen_fingerprint:
        raise EmailDeliveryPending('The saved email changed while it was being checked. No new email was requested.')
    try:
        started = row.get('first_attempt_at')
        if isinstance(started, bool) or started is None:
            raise ValueError('Invalid timestamp')
        age = float(clock()) - float(started)
        if not math.isfinite(age) or age < 0:
            raise ValueError('Invalid elapsed time')
    except (TypeError, ValueError, OverflowError) as error:
        raise EmailDeliveryPending('The saved email attempt needs a status check.') from error
    if age >= SAFE_RETRY_SECONDS:
        raise EmailDeliveryNeedsReview('Email acceptance is still unconfirmed. Check the original request before sending another email.')
    try:
        result = send(copy.deepcopy(row['payload']), key)
    except Exception as error:
        # A timeout can mean the provider accepted the email. The persisted
        # payload and first timestamp remain the only allowed retry identity.
        raise EmailDeliveryPending('Email acceptance is unconfirmed. The original request is saved for retry.') from error
    provider_id = result.get('id') if isinstance(result, dict) else None
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise EmailDeliveryPending('The email service did not confirm acceptance. The request is saved for retry.')
    try:
        confirmed = accept(copy.deepcopy(row), provider_id)
    except Exception as error:
        raise EmailDeliveryPending('Email acceptance could not be saved. Check the original request before sending another email.') from error
    if confirmed is not True:
        raise EmailDeliveryPending('Email acceptance could not be confirmed in the saved record.')
    return {'id': provider_id, 'status': 'accepted', 'recovered': False}
