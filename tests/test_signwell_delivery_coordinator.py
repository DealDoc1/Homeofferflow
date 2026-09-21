import asyncio
import copy
import unittest

from lib.signwell_delivery import (
    DeliveryMismatch, DeliveryPending, DeliveryUnsent, SendRejected,
    FINGERPRINT_KEY, deliver_verified_document,
)


class Store:
    def __init__(self):
        self.record = {'document_id': '', 'journal': None, 'version': 0, 'status': 'draft'}
        self.documents = {}
        self.calls = []
        self.sent_payloads = []
        self.now = 1000
        self.inspect_error = None
        self.send_error = None
        self.after_send = 'sent'
        self.send_result = 'normal'
        self.checkpoint_error = None
        self.checkpoint_false = False
        self.finish_error = None
        self.payload = {'draft': False, 'fields': [[{'page': 1, 'x': 10, 'y': 20}]],
                        'recipients': [{'id': '1', 'name': 'QA signer', 'email': 'qa@example.test'}],
                        'metadata': {'record_id': 'record'}, 'test_mode': True,
                        'apply_signing_order': False, 'embedded_signing': False,
                        'files': [{'file_base64': 'private-pdf-test-only'}]}
        self.context = {'owner_id': 'owner', 'record_id': 'record', 'source_revision': 'revision-1',
                        'inputs': {'price': '100'}}

    def operation(self):
        snapshot = copy.deepcopy(self.record)
        version = snapshot['version']

        async def create(payload):
            self.calls.append('create')
            doc_id = 'doc-' + str(len(self.documents) + 1)
            self.documents[doc_id] = {**copy.deepcopy(payload), 'id': doc_id, 'status': 'draft'}
            await asyncio.sleep(0)
            return {'id': doc_id}

        async def inspect(doc_id):
            self.calls.append('inspect:' + doc_id)
            if self.inspect_error:
                raise self.inspect_error
            await asyncio.sleep(0)
            return copy.deepcopy(self.documents[doc_id])

        async def checkpoint(doc_id, journal):
            nonlocal version
            self.calls.append('checkpoint:' + journal['phase'])
            if self.checkpoint_error:
                raise self.checkpoint_error
            if self.checkpoint_false or self.record['version'] != version:
                return False
            self.record.update(document_id=doc_id, journal=copy.deepcopy(journal), version=version+1)
            version += 1
            return True

        async def send(doc_id, payload):
            # Assert the checkpoint actually precedes the irreversible call.
            assert self.record['document_id'] == doc_id
            assert self.record['journal']['phase'] == 'sending'
            self.calls.append('send:' + doc_id)
            self.sent_payloads.append(copy.deepcopy(payload))
            self.documents[doc_id]['status'] = self.after_send
            if self.send_error:
                raise self.send_error
            if self.send_result != 'normal':
                return self.send_result
            return {'id': doc_id, 'status': self.after_send}

        async def finish(doc_id, document):
            self.calls.append('finish:' + doc_id)
            if self.finish_error:
                raise self.finish_error
            self.record['status'] = document['status']
            return True

        return deliver_verified_document(
            payload=self.payload, context=self.context, document_id=snapshot['document_id'],
            journal=snapshot['journal'], create=create, inspect=inspect, send=send,
            checkpoint=checkpoint, finish=finish,
            matches=lambda doc, fields, recipients: doc['fields'] == fields and doc['recipients'] == recipients,
            clock=lambda: self.now,
        )


class SignwellDeliveryCoordinatorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store = Store()

    async def test_private_create_is_saved_before_inspect_and_send(self):
        original = copy.deepcopy(self.store.payload)
        result = await self.store.operation()
        self.assertEqual(result['state'], 'sent')
        self.assertEqual(self.store.calls, ['create', 'checkpoint:prepared', 'inspect:doc-1',
                                           'checkpoint:sending', 'send:doc-1', 'finish:doc-1'])
        self.assertTrue(self.store.documents['doc-1']['draft'])
        self.assertEqual(self.store.payload, original)

    async def test_zero_row_claim_prevents_sending(self):
        self.store.checkpoint_false = True
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        self.assertFalse(any(call.startswith('send:') for call in self.store.calls))

    async def test_uncertain_checkpoint_prevents_sending(self):
        self.store.checkpoint_error = TimeoutError('database')
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        self.assertFalse(any(call.startswith('send:') for call in self.store.calls))

    async def test_inspection_failure_retains_id_and_retry_uses_same_document(self):
        self.store.inspect_error = TimeoutError('provider')
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        self.assertEqual(self.store.record['document_id'], 'doc-1')
        self.store.inspect_error = None
        await self.store.operation()
        self.assertEqual(self.store.calls.count('create'), 1)
        self.assertEqual(self.store.calls.count('send:doc-1'), 1)

    async def test_field_or_recipient_change_blocks_retry_without_deleting(self):
        for key in ('fields', 'recipients'):
            self.store = Store()
            self.store.inspect_error = TimeoutError()
            with self.assertRaises(DeliveryPending):
                await self.store.operation()
            self.store.inspect_error = None
            self.store.documents['doc-1'][key] = []
            with self.assertRaises(DeliveryMismatch):
                await self.store.operation()
            self.assertEqual(len(self.store.documents), 1)
            self.assertNotIn('send:doc-1', self.store.calls)

    async def test_send_timeout_recovers_confirmed_sent_or_completed_without_duplicate(self):
        for status, expected in (('sent', 'sent'), ('completed', 'signed')):
            self.store = Store()
            self.store.send_error = TimeoutError()
            self.store.after_send = status
            result = await self.store.operation()
            self.assertEqual(result['state'], expected)
            self.assertEqual(self.store.calls.count('create'), 1)
            self.assertEqual(self.store.calls.count('send:doc-1'), 1)

    async def test_uncertain_draft_waits_before_resuming_the_same_document(self):
        self.store.send_error = TimeoutError()
        self.store.after_send = 'draft'
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        self.assertEqual(self.store.calls.count('send:doc-1'), 1)
        self.store.now += 121
        self.store.send_error = None
        self.store.after_send = 'sent'
        await self.store.operation()
        self.assertEqual(self.store.calls.count('create'), 1)
        self.assertEqual(self.store.calls.count('send:doc-1'), 2)

    async def test_provider_rejection_and_confirmed_draft_allow_same_document_retry(self):
        self.store.send_error = SendRejected(402)
        self.store.after_send = 'draft'
        with self.assertRaises(DeliveryUnsent):
            await self.store.operation()
        self.assertEqual(self.store.record['journal']['phase'], 'prepared')
        self.store.send_error = None
        self.store.after_send = 'sent'
        await self.store.operation()
        self.assertEqual(self.store.calls.count('create'), 1)

    async def test_multisigner_retry_preserves_concurrent_invitations_and_recipient_identity(self):
        self.store.payload['recipients'].append(
            {'id': '2', 'name': 'QA co-buyer', 'email': 'cobuyer@example.test'})
        recipients = copy.deepcopy(self.store.payload['recipients'])
        self.store.send_error = SendRejected(402)
        self.store.after_send = 'draft'
        with self.assertRaises(DeliveryUnsent):
            await self.store.operation()
        self.store.send_error = None
        self.store.after_send = 'sent'
        await self.store.operation()
        # Refresh/replay after a confirmed send reconciles, not sends again.
        await self.store.operation()
        self.assertEqual(self.store.calls.count('create'), 1)
        self.assertEqual(len(self.store.sent_payloads), 2)
        for payload in [self.store.documents['doc-1'], *self.store.sent_payloads]:
            self.assertIs(payload['apply_signing_order'], False)
            self.assertEqual(payload['recipients'], recipients)

    async def test_changed_signing_order_cannot_silently_change_a_saved_request(self):
        self.store.inspect_error = TimeoutError()
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        self.store.inspect_error = None
        self.store.payload['apply_signing_order'] = True
        with self.assertRaises(DeliveryMismatch):
            await self.store.operation()
        self.assertEqual(self.store.calls.count('create'), 1)
        self.assertEqual(self.store.sent_payloads, [])

    async def test_unknown_state_after_send_never_claims_sent_or_unsent(self):
        self.store.send_error = SendRejected(500)
        self.store.after_send = 'future-state'
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        self.assertEqual(self.store.record['document_id'], 'doc-1')
        self.assertFalse(any(call.startswith('finish:') for call in self.store.calls))

    async def test_failed_final_write_is_recovered_without_another_send(self):
        self.store.finish_error = TimeoutError('database')
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        self.store.finish_error = None
        await self.store.operation()
        self.assertEqual(self.store.calls.count('send:doc-1'), 1)
        self.assertEqual(self.store.calls.count('create'), 1)

    async def test_concurrent_initial_attempts_allow_only_one_recipient_facing_send(self):
        results = await asyncio.gather(self.store.operation(), self.store.operation(), return_exceptions=True)
        self.assertEqual(sum(isinstance(result, dict) for result in results), 1)
        self.assertEqual(sum(call.startswith('send:') for call in self.store.calls), 1)
        # Two private creates can race; the losing unsent draft is not deleted.
        self.assertEqual(self.store.calls.count('create'), 2)

    async def test_concurrent_resumes_allow_only_one_send(self):
        self.store.inspect_error = TimeoutError()
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        self.store.inspect_error = None
        results = await asyncio.gather(self.store.operation(), self.store.operation(), return_exceptions=True)
        # The second request can observe the first's sent result and safely
        # reconcile it, or lose the conditional claim. Neither repeats send.
        self.assertTrue(any(isinstance(result, dict) for result in results))
        self.assertTrue(all(isinstance(result, (dict, DeliveryPending)) for result in results))
        self.assertEqual(self.store.calls.count('create'), 1)
        self.assertEqual(self.store.calls.count('send:doc-1'), 1)

    async def test_changed_inputs_owner_or_source_cannot_resume_previous_packet(self):
        for key in ('owner_id', 'record_id', 'source_revision', 'inputs'):
            self.store = Store()
            self.store.inspect_error = TimeoutError()
            with self.assertRaises(DeliveryPending):
                await self.store.operation()
            self.store.inspect_error = None
            self.store.context[key] = 'changed'
            with self.assertRaises(DeliveryMismatch):
                await self.store.operation()
            self.assertNotIn('send:doc-1', self.store.calls)

    async def test_provider_fingerprint_is_checked_not_just_the_saved_journal(self):
        self.store.inspect_error = TimeoutError()
        with self.assertRaises(DeliveryPending):
            await self.store.operation()
        self.store.inspect_error = None
        self.store.documents['doc-1']['metadata'][FINGERPRINT_KEY] = 'other-request'
        with self.assertRaises(DeliveryMismatch):
            await self.store.operation()
        self.assertNotIn('send:doc-1', self.store.calls)

    async def test_legacy_tracked_document_never_triggers_another_creation(self):
        self.store.record['document_id'] = 'legacy-doc'
        with self.assertRaises(DeliveryMismatch):
            await self.store.operation()
        self.assertEqual(self.store.calls, [])

    async def test_accepted_but_malformed_send_response_requires_document_verification(self):
        self.store.send_result = None
        await self.store.operation()
        self.assertEqual(self.store.calls.count('inspect:doc-1'), 2)
        self.assertEqual(self.store.calls.count('send:doc-1'), 1)


if __name__ == '__main__':
    unittest.main()
