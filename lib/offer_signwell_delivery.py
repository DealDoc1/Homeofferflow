"""Durable purchase-offer signing; caller supplies a verified owned record."""
import asyncio
import copy
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import quote

import httpx
from lib import signwell_delivery as delivery
from lib.signwell_request import document_matches_signing_request, send_options


def offer_answers(offer):
    return {key: value for key, value in offer.items()
            if key not in {delivery.JOURNAL_KEY, 'signwell', 'backend_saved',
                           '_subscription_user_id', '_paragraph4_source_pdf_bytes',
                           '_hofOfferId', 'checkout_customer_email',
                           'signwellStatus', 'signwellDocumentId', 'signwellLastStatusRefresh',
                           'signwellRecipientStatuses'}}


def stable_delivery_answers(offer, record):
    """Reuse the original identity for a tracked, otherwise unchanged packet.

    The caller must supply a server-read, authorized record. Keep the original
    fingerprint algorithm and its exact inputs: older journals and email keys
    may include the timestamps originally present at generation. Merely dropping
    timestamps globally would invalidate those existing receipts.

    Only explicitly known display bookkeeping may differ. Customer answers,
    uploaded contents and signing-source/render manifests remain significant.
    """
    current = offer_answers(offer)
    stored = record.get('offer_data') if isinstance(record, dict) else None
    if not isinstance(record, dict) or not record.get('signwell_document_id') or not isinstance(stored, dict):
        return current
    original = offer_answers(stored)
    bookkeeping = {'generatedAt', 'packetGeneratedAt', 'packetGenerationError',
                   'packetGenerationFailedAt', 'packetGenerationFailureCategory',
                   '_savedFromDashboard'}
    comparable = lambda answers: json.dumps(
        {key: value for key, value in answers.items() if key not in bookkeeping},
        sort_keys=True, separators=(',', ':'), allow_nan=False)
    if comparable(current) == comparable(original):
        return copy.deepcopy(original)
    return current


def deliver_offer_document(record, payload, offer, *, user_id, supabase_url, supabase_key, signwell_key):
    if not isinstance(record, dict) or not record.get('id') or record.get('user_id') != user_id:
        raise delivery.DeliveryMismatch('The saved offer could not be verified for this account. No invitation was requested.')
    current = copy.deepcopy(record)
    stored = current.get('offer_data') or {}
    journal = stored.get(delivery.JOURNAL_KEY)
    doc_id = str(current.get('signwell_document_id') or '')
    now = lambda: datetime.now(timezone.utc).isoformat()
    headers = {'apikey': supabase_key, 'Authorization': 'Bearer ' + supabase_key,
               'Content-Type': 'application/json', 'Prefer': 'return=representation'}
    provider_headers = {'X-Api-Key': signwell_key, 'Content-Type': 'application/json'}
    base = {'id': 'eq.' + str(record['id']), 'user_id': 'eq.' + user_id if user_id else 'is.null'}
    url = supabase_url.rstrip('/') + '/rest/v1/hof_offers'
    provider = 'https://www.signwell.com/api/v1/documents'
    identity_answers = stable_delivery_answers(offer, record)
    # A retry checkpoint must retain the same original inputs as its fingerprint,
    # not replace them with the newer browser timestamps we just disregarded.
    same_original_inputs = json.dumps(identity_answers, sort_keys=True, allow_nan=False) == json.dumps(
        offer_answers(stored), sort_keys=True, allow_nan=False)
    request_offer = stored if doc_id and same_original_inputs else offer
    prepared = {key: value for key, value in request_offer.items()
                if key not in {delivery.JOURNAL_KEY, '_subscription_user_id', '_paragraph4_source_pdf_bytes'}}

    def write(body, params):
        response = httpx.patch(url, params={**base, **params}, headers=headers, json=body, timeout=20)
        if response.status_code not in {200, 201}:
            raise RuntimeError('Offer status could not be saved.')
        rows = response.json()
        return rows if isinstance(rows, list) else []

    async def checkpoint(document_id, attempt):
        if not current.get('last_updated'):
            return False
        previous_id = current.get('signwell_document_id')
        rows = write({'status': 'Generated', 'signwell_document_id': document_id,
                      'last_updated': now(),
                      'offer_data': {**prepared, delivery.JOURNAL_KEY: attempt}},
                     {'last_updated': 'eq.' + str(current['last_updated']),
                      'status': 'in.(Generated,Generation Failed)',
                      'signwell_document_id': 'eq.' + previous_id if previous_id else 'is.null',
                      'select': 'id,user_id,status,last_updated,signwell_document_id,offer_data'})
        if len(rows) != 1 or rows[0].get('id') != record['id'] or rows[0].get('signwell_document_id') != document_id:
            return False
        current.update(rows[0])
        return True

    async def create(body):
        response = httpx.post(provider, headers=provider_headers, json=body, timeout=45)
        if response.status_code not in {200, 201, 202}:
            raise delivery.DeliveryUnsent('The signing service could not prepare your offer. No invitation was requested.')
        return response.json()

    async def inspect(document_id):
        response = httpx.get(provider + '/' + quote(document_id, safe=''), headers=provider_headers, timeout=45)
        if response.status_code != 200:
            raise RuntimeError('Signing status is temporarily unavailable.')
        return response.json()

    async def send(document_id, body):
        response = httpx.post(provider + '/' + quote(document_id, safe='') + '/send',
                              headers=provider_headers, json=send_options(body), timeout=45)
        if response.status_code not in {200, 201, 202}:
            raise delivery.SendRejected(response.status_code)
        return response.json()

    async def finish(document_id, document):
        state = delivery.document_state(document)
        status = {'sent': 'Sent for Signature', 'signed': 'Buyer Signed', 'void': 'Rejected'}[state]
        rows = write({'status': status, 'signwell_status': document.get('status') or status,
                      'last_updated': now()},
                     {'signwell_document_id': 'eq.' + document_id,
                      'status': 'in.(Generated,Generation Failed)', 'select': 'id,status,signwell_document_id'})
        if len(rows) == 1 and rows[0].get('id') == record['id']:
            return True
        response = httpx.get(url, params={**base, 'signwell_document_id': 'eq.' + document_id,
                             'select': 'id,status', 'limit': '1'}, headers=headers, timeout=20)
        latest = response.json() if response.status_code == 200 else []
        return bool(latest and str(latest[0].get('status') or '').lower() in
                    {'sent for signature', 'awaiting signature', 'buyer viewed', 'partially signed',
                     'partially buyer signed', 'buyer signed', 'signed', 'buyer signatures complete', 'rejected', 'expired'})

    source_bytes = offer.get('_paragraph4_source_pdf_bytes') or {}
    context = {'owner_id': user_id, 'offer_id': record['id'], 'offer': identity_answers,
               'paragraph4_sources': {key: hashlib.sha256(value).hexdigest() for key, value in source_bytes.items()}}
    return asyncio.run(delivery.deliver_verified_document(
        payload=payload, context=context, document_id=doc_id, journal=journal,
        create=create, inspect=inspect, send=send, checkpoint=checkpoint, finish=finish,
        matches=document_matches_signing_request))
