"""Server-owned packet allowance protocol; no browser-supplied month/quantity."""
import hashlib
import re
import uuid

import httpx
from lib.email_delivery import payload_fingerprint
from lib.offer_signwell_delivery import offer_answers


def packet_answers_hash(offer):
    """Identify the customer's reviewed answers, not UI/provider bookkeeping.

    Source/renderer fixes do not consume another unit for unchanged answers.
    Uploaded document contents remain in the identity; server-internal source
    hashes and rendering revisions are instead verified by the signing layer.
    """
    transient = {'generatedAt', 'packetGeneratedAt', 'packetGenerationError',
                 'packetGenerationFailedAt', 'packetGenerationFailureCategory'}
    return payload_fingerprint({key: value for key, value in offer_answers(offer).items()
                                if not key.startswith('_') and key not in transient})


class PacketGenerationPending(RuntimeError):
    pass


class PacketAllowanceUnavailable(PacketGenerationPending):
    pass


class PacketGenerationBusy(PacketGenerationPending):
    pass


class PacketGenerationStore:
    def __init__(self, *, supabase_url, service_key, client=None):
        if not supabase_url or not service_key:
            raise PacketGenerationPending('Packet usage tracking is unavailable.')
        self.url = supabase_url.rstrip('/') + '/rest/v1/rpc/'
        self.headers = {'apikey': service_key, 'Authorization': 'Bearer ' + service_key,
                        'Content-Type': 'application/json'}
        self.client = client or httpx

    def _call(self, name, payload):
        try:
            response = self.client.post(self.url + name, headers=self.headers, json=payload, timeout=20)
            if response.status_code != 200:
                raise ValueError('Unconfirmed database operation')
            return response.json()
        except Exception as error:
            raise PacketGenerationPending('Packet usage could not be confirmed. Check My Offers before trying again.') from error

    def claim(self, user_id, offer_id, answers_hash, attempt_token):
        return self._call('hof_claim_packet_generation', {'p_user': user_id, 'p_offer': offer_id,
                          'p_answers_hash': answers_hash, 'p_attempt': attempt_token})

    def complete(self, row):
        return self._call('hof_complete_packet_generation', {'p_user': row['user_id'],
                          'p_key': row['generation_key'], 'p_attempt': row['attempt_token']})

    def release(self, row):
        return self._call('hof_release_unrendered_packet', {'p_user': row['user_id'],
                          'p_key': row['generation_key'], 'p_attempt': row['attempt_token']})


def render_packet_with_usage(*, user_id, offer_id, answers_hash, render, store):
    """Reserve -> render -> record one unit, all before outbound delivery.

    The caller must authenticate the user and hash the actual reviewed answers.
    Source and render revisions belong to delivery verification, not allowance:
    correcting a renderer must not charge again for unchanged customer answers.
    This routine has no email/signing call.
    The database transaction ends before rendering or any provider HTTP call.
    """
    try:
        user_id, offer_id = str(uuid.UUID(user_id)), str(uuid.UUID(offer_id))
    except (ValueError, TypeError, AttributeError):
        raise ValueError('A verified account and saved offer are required.') from None
    if not isinstance(answers_hash, str) or not re.fullmatch('[0-9a-f]{64}', answers_hash):
        raise ValueError('The reviewed packet identity is required.')
    token = str(uuid.uuid4())
    expected_key = 'hof-packet-v1-' + hashlib.sha256(
        f'{user_id}:{offer_id}:{answers_hash}'.encode()).hexdigest()
    row = store.claim(user_id, offer_id, answers_hash, token)

    def validate(candidate, completed=False):
        expected = {'user_id': user_id, 'offer_id': offer_id,
                    'answers_hash': answers_hash, 'generation_key': expected_key}
        if not isinstance(candidate, dict) or any(candidate.get(k) != v for k,v in expected.items()):
            raise PacketGenerationPending('The packet reservation could not be verified.')
        if not re.fullmatch(r'[0-9]{4}-(0[1-9]|1[0-2])', str(candidate.get('billing_month', ''))):
            raise PacketGenerationPending('The packet billing period could not be verified.')
        if completed:
            if candidate.get('outcome') != 'completed' or candidate.get('status') != 'completed' or not candidate.get('usage_event_id'):
                raise PacketGenerationPending('Packet completion could not be confirmed.')
            try:
                uuid.UUID(candidate['usage_event_id'])
            except (ValueError, TypeError, AttributeError):
                raise PacketGenerationPending('The packet usage receipt could not be verified.') from None
        elif candidate.get('status') != 'reserved' or candidate.get('attempt_token') != token:
            raise PacketGenerationPending('The packet reservation is no longer current.')

    outcome = row.get('outcome') if isinstance(row, dict) else None
    if outcome in {'no_subscription', 'inactive', 'limit_reached'}:
        raise PacketAllowanceUnavailable('Your packet allowance is unavailable. Check your account before starting another packet.')
    if outcome == 'busy':
        raise PacketGenerationBusy('This packet is already being prepared. Check My Offers before trying again.')
    if outcome == 'legacy_packet':
        raise PacketGenerationPending('This offer already has packet history. Open My Offers to check its existing documents and signing status before generating it again.')
    if outcome not in {'reserved', 'completed'}:
        raise PacketGenerationPending('The saved offer could not be reserved for generation.')
    recovered = outcome == 'completed'
    validate(row, completed=recovered)
    try:
        pdf = render()
        if not isinstance(pdf, bytes) or not pdf.startswith(b'%PDF-'):
            raise ValueError('The packet could not be rendered.')
    except Exception:
        if not recovered and store.release(row) is not True:
            raise PacketGenerationPending('Packet preparation stopped. Its allowance reservation needs a status check.') from None
        raise
    if not recovered:
        completed = store.complete(row)
        validate(completed, completed=True)
        if completed.get('billing_month') != row['billing_month']:
            raise PacketGenerationPending('The saved packet billing period changed unexpectedly.')
    return {'pdf_bytes': pdf, 'usage': {'status': 'recorded', 'generationKey': expected_key,
             'billingMonth': row['billing_month'], 'recovered': recovered}}
