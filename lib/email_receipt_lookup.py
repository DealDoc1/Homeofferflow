"""Exact provider lookup for private operator recovery; never sends an email."""
import uuid

from lib.email_delivery import (DELIVERY_KEY_RE, EmailDeliveryPending,
                                reconcile_verified_email_event)


def inspect_email_receipt(*, key, provider_id, read, accept, retrieve, apply=False):
    """retrieve must be an authenticated server-side GET, never browser data.

    No account search, payload replacement, new request, or timer reset exists.
    Returns operational status only, never the retrieved body or recipients.
    """
    if not isinstance(key, str) or not DELIVERY_KEY_RE.fullmatch(key):
        raise ValueError('A valid delivery key is required.')
    try:
        if str(uuid.UUID(provider_id)) != provider_id:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('A valid Resend email ID is required.') from None
    row = read(key)
    if not isinstance(row, dict) or row.get('delivery_key') != key:
        return {'status': 'not_found', 'updated': False}
    if row.get('status') == 'accepted':
        return {'status': 'already_accepted' if row.get('provider_id') == provider_id else 'mismatch',
                'updated': False}
    result = retrieve(provider_id)
    if not isinstance(result, dict) or result.get('id') != provider_id or result.get('object') != 'email':
        raise EmailDeliveryPending('The provider email could not be verified.')
    tags = result.get('tags')
    if not isinstance(tags, list) or any(not isinstance(tag, dict) or
            not isinstance(tag.get('name'), str) or not isinstance(tag.get('value'), str) for tag in tags):
        return {'status': 'unmatched', 'updated': False}
    tag_map = {tag['name']: tag['value'] for tag in tags}
    if len(tag_map) != len(tags) or tag_map.get('hof_delivery') != key:
        return {'status': 'unmatched', 'updated': False}
    outcome = result.get('last_event')
    allowed = {'sent', 'delivered', 'bounced', 'complained', 'suppressed', 'opened', 'clicked'}
    if outcome not in allowed:
        return {'status': 'unconfirmed', 'updated': False}
    # The authenticated GET is independent provider evidence, normalized to
    # the same receipt contract as signed webhooks. This is not a forged event
    # posted to the public endpoint and does not insert webhook telemetry.
    receipt = {'type': 'email.' + outcome, 'data': {'email_id': provider_id,
               'from': result.get('from'), 'to': result.get('to'), 'tags': tag_map}}
    matched = reconcile_verified_email_event(receipt, read=lambda candidate: row if candidate == key else None,
        accept=accept if apply else lambda *_: True)
    if not matched:
        return {'status': 'unmatched', 'updated': False}
    return {'status': 'accepted' if apply else 'matched', 'updated': bool(apply),
            'providerStatus': outcome,
            'needsAttention': outcome in {'bounced', 'complained', 'suppressed'}}
