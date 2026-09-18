"""Private-draft -> durable checkpoint -> verified send, with bounded recovery.

Adapters own authorization, source validation and conditional database writes.
This coordinator never deletes a document and never re-creates a tracked one.
"""
import copy
import hashlib
import json
import math
import time
import uuid


JOURNAL_KEY = '_hof_signature_delivery'
FINGERPRINT_KEY = 'hof_request_fingerprint'
RETRY_COOLDOWN_SECONDS = 120


class DeliveryPending(RuntimeError):
    """A saved request needs verification; delivery must not be guessed."""


class DeliveryUnsent(RuntimeError):
    """The provider confirmed a rejected send remains an unsent draft."""


class DeliveryMismatch(ValueError):
    """The tracked document does not match the current reviewed request."""


class SendRejected(RuntimeError):
    def __init__(self, status_code):
        self.status_code = int(status_code)
        super().__init__(f'Provider send rejected ({self.status_code}).')


def request_fingerprint(payload, context):
    """Bind structured contents and identity; omit variable PDF timestamps."""
    metadata = {key: value for key, value in (payload.get('metadata') or {}).items()
                if key != FINGERPRINT_KEY}
    value = {'context': context, 'metadata': metadata,
             'fields': payload.get('fields'), 'recipients': payload.get('recipients'),
             'test_mode': payload.get('test_mode'),
             'apply_signing_order': payload.get('apply_signing_order'),
             'embedded_signing': payload.get('embedded_signing')}
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def document_state(document):
    if not isinstance(document, dict):
        return ''
    status = str(document.get('status') or document.get('document_status') or '').strip().lower()
    status = status.replace('-', '_').replace(' ', '_')
    if status in {'draft', 'created'} or (not status and document.get('draft') is True):
        return 'draft'
    if status in {'sent', 'shared', 'viewed', 'pending', 'in_progress', 'signed'}:
        return 'sent'
    if status in {'completed', 'complete'}:
        return 'signed'
    if status in {'declined', 'expired', 'cancelled', 'canceled'}:
        return 'void'
    return ''


async def deliver_verified_document(*, payload, context, document_id='', journal=None,
                                    create, inspect, send, checkpoint, finish, matches,
                                    clock=time.time):
    """Callbacks must not silently succeed on zero-row conditional writes.

    checkpoint(document_id, journal) returns literal True only after one
    owner/record/version-scoped row is confirmed persisted. finish returns
    literal True after reconciliation without regressing signed/void state.
    create is always called with draft=True; send never creates a document.
    """
    payload = copy.deepcopy(payload)
    payload['draft'] = True
    fingerprint = request_fingerprint(payload, context)
    payload.setdefault('metadata', {})[FINGERPRINT_KEY] = fingerprint
    journal = copy.deepcopy(journal or {})
    tracked = bool(document_id)

    async def save(phase):
        nonlocal journal
        next_journal = {'version': 1, 'document_id': document_id,
                        'fingerprint': fingerprint, 'phase': phase,
                        'attempt_id': str(uuid.uuid4()), 'started_at': clock(),
                        'recipients': copy.deepcopy(payload.get('recipients') or [])}
        try:
            confirmed = await checkpoint(document_id, next_journal)
        except Exception as error:
            raise DeliveryPending('We could not confirm the saved request. Refresh its status before trying again.') from error
        if confirmed is not True:
            raise DeliveryPending('Another update is already handling this request. Refresh its status before trying again.')
        journal = next_journal

    async def read_verified():
        try:
            document = await inspect(document_id)
        except Exception as error:
            raise DeliveryPending('We could not confirm delivery. The request is saved; check its signature status shortly.') from error
        if not isinstance(document, dict):
            raise DeliveryPending('The signing service did not return a document status. Check again shortly.')
        returned_id = str(document.get('id') or document.get('document_id') or document_id)
        metadata = document.get('metadata')
        if returned_id != document_id or not isinstance(metadata, dict) or metadata.get(FINGERPRINT_KEY) != fingerprint:
            raise DeliveryMismatch('This saved request does not match the reviewed document. No new invitation was requested. Prepare a new copy before sending.')
        if not document_state(document):
            raise DeliveryPending('The signing service did not confirm delivery. Check the saved request status shortly.')
        return document

    async def reconcile(document):
        try:
            confirmed = await finish(document_id, document)
        except Exception as error:
            raise DeliveryPending('The signing request is tracked, but its latest status could not be saved. Refresh signature status before trying again.') from error
        if confirmed is not True:
            raise DeliveryPending('The request changed while its status was being saved. Refresh signature status before trying again.')
        state = document_state(document)
        message = {'sent': 'Signature request sent.',
                   'signed': 'This document is already fully signed. No new invitation was sent.',
                   'void': 'This signing request has ended. No new invitation was sent.'}[state]
        return {'document_id': document_id, 'document': document,
                'state': state, 'message': message, 'recovered': tracked}

    if tracked:
        if journal.get('document_id') != document_id or journal.get('fingerprint') != fingerprint:
            raise DeliveryMismatch('This saved signing request needs a status check before it can be retried. No new invitation was requested.')
    else:
        result = await create(payload)
        document_id = str(result.get('id') or result.get('document_id') or '').strip() if isinstance(result, dict) else ''
        if not document_id:
            raise DeliveryPending('The signing service did not return a tracking number. No invitation was requested.')
        # Persist identity even if subsequent inspection fails. A failed save
        # leaves at most an unused private draft, never a recipient-facing send.
        await save('prepared')

    document = await read_verified()
    if document_state(document) != 'draft':
        return await reconcile(document)
    if not matches(document, payload.get('fields') or [], payload.get('recipients') or []):
        raise DeliveryMismatch('The saved signature fields or recipients do not match the reviewed document. Nothing new was sent. Prepare a new copy.')
    if journal.get('phase') == 'sending':
        try:
            age = clock() - float(journal.get('started_at'))
        except (TypeError, ValueError):
            age = float('nan')
        if not math.isfinite(age) or age < RETRY_COOLDOWN_SECONDS:
            raise DeliveryPending('The previous send is still being checked. Refresh signature status in a moment; do not create another copy.')

    await save('sending')
    try:
        sent = await send(document_id, payload)
    except Exception as error:
        # Never delete or re-create after an ambiguous send. The same ID is
        # the only authority for whether invitations may already exist.
        document = await read_verified()
        if document_state(document) != 'draft':
            return await reconcile(document)
        if isinstance(error, SendRejected) and 400 <= error.status_code < 500 and error.status_code not in {408, 409, 429}:
            await save('prepared')
            raise DeliveryUnsent('The signing service could not send this request. It remains an unsent draft; retry this saved request after the issue is resolved.') from error
        raise DeliveryPending('Delivery is still unconfirmed. The request is saved; refresh its signature status before retrying.') from error

    # An accepted HTTP response without a recognized sent state is not enough
    # to claim delivery. Verify the same document rather than repeat POST.
    if (not isinstance(sent, dict) or document_state(sent) not in {'sent', 'signed', 'void'}
            or str(sent.get('id') or sent.get('document_id') or document_id) != document_id):
        sent = await read_verified()
    if document_state(sent) == 'draft':
        raise DeliveryPending('The request is saved, but delivery has not been confirmed. Refresh signature status shortly.')
    return await reconcile(sent)
