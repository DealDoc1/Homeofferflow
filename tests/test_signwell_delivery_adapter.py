"""Run the real HTTP persistence adapter with stateful provider/row doubles."""
import asyncio
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('admin_delivery_adapter', ROOT / 'api/admin-dashboard.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DELIVERY = MODULE.signwell_delivery
USER = {'id': '11111111-1111-4111-8111-111111111111'}


class DeliveryFixture:
    def __init__(self, test, table):
        self.test = test
        self.table = table
        self.field = 'agreement_data' if table == 'hof_standalone_agreements' else 'response_data'
        self.row = {'id': '22222222-2222-4222-8222-222222222222', 'status': 'draft',
                    'updated_at': '2026-09-15T10:00:00+00:00', self.field: {'answer': 'yes'}}
        self.payload = {'draft': True, 'apply_signing_order': False, 'metadata': {'record': self.row['id']},
                        'recipients': [{'id': '1', 'email': 'signer@example.com', 'name': 'Signer'}],
                        'fields': [[{'api_id': 'signature', 'recipient_id': '1'}]]}
        self.context = {'owner': USER['id'], 'record': self.row['id'], 'source_revision': 'v1'}
        self.documents = {}
        self.creates = 0
        self.sends = 0
        self.failure = None
        self.reject_claim = False
        self.fail_final_write = False
        self.client = AsyncMock()
        self.client.get.side_effect = self.get
        self.client.post.side_effect = self.post
        self.client.patch.side_effect = self.persist

    def response(self, value, status=200):
        return SimpleNamespace(status_code=status, json=lambda: copy.deepcopy(value))

    async def get(self, url, **kwargs):
        return self.response(self.documents[url.rsplit('/', 1)[-1]])

    async def post(self, url, *, json, **kwargs):
        if not url.endswith('/send'):
            self.creates += 1
            doc_id = f'doc-{self.creates}'
            self.test.assertTrue(json['draft'])
            self.documents[doc_id] = {**copy.deepcopy(json), 'id': doc_id, 'status': 'draft'}
            await asyncio.sleep(0)
            return self.response({'id': doc_id}, 201)
        doc_id = url.split('/')[-2]
        self.sends += 1
        self.test.assertEqual(self.row['signwell_document_id'], doc_id)
        self.test.assertEqual(self.row[self.field][DELIVERY.JOURNAL_KEY]['phase'], 'sending')
        self.test.assertFalse(json['apply_signing_order'])
        if self.failure == 'rejected':
            return self.response({}, 402)
        if self.failure == 'timeout_draft':
            raise TimeoutError('provider response lost')
        self.documents[doc_id]['status'] = 'completed' if self.failure == 'timeout_completed' else 'sent'
        if self.failure == 'webhook_first':
            self.row.update(status='signed', signed_at='2026-09-15T11:00:00Z')
        if self.failure in {'timeout_sent', 'timeout_completed'}:
            raise TimeoutError('provider accepted, response lost')
        return self.response(self.documents[doc_id], 201)

    async def persist(self, url, *, json, headers):
        query = parse_qs(urlsplit(url).query)
        self.test.assertIn('/rest/v1/' + self.table, url)
        self.test.assertEqual(query['id'], ['eq.' + self.row['id']])
        self.test.assertEqual(query['agent_user_id'], ['eq.' + USER['id']])
        self.test.assertEqual(query['status'], ['in.(draft,failed)'])
        self.test.assertEqual(headers['Prefer'], 'return=representation')
        expected_id = 'eq.' + self.row['signwell_document_id'] if self.row.get('signwell_document_id') else 'is.null'
        if query['signwell_document_id'] != [expected_id] or self.row['status'] not in {'draft', 'failed'}:
            return self.response([])
        if self.field in json:
            if self.reject_claim or query.get('updated_at') != ['eq.' + self.row['updated_at']]:
                return self.response([])
        elif self.fail_final_write:
            raise TimeoutError('database response lost')
        self.row.update(copy.deepcopy(json))
        return self.response([self.row])

    async def lookup(self, query):
        self.test.assertIn('agent_user_id=eq.' + USER['id'], query)
        self.test.assertIn('signwell_document_id=eq.' + self.row['signwell_document_id'], query)
        return [copy.deepcopy(self.row)]

    async def deliver(self):
        return await MODULE._deliver_tracked_signwell_request(
            USER, self.table, copy.deepcopy(self.row), self.field,
            copy.deepcopy(self.row[self.field]), copy.deepcopy(self.payload), copy.deepcopy(self.context))


class SignwellDeliveryAdapterTests(unittest.TestCase):
    def run_case(self, scenario):
        for table in ('hof_standalone_agreements', 'hof_seller_disclosure_drafts'):
            with self.subTest(table=table):
                fixture = DeliveryFixture(self, table)
                with patch.object(MODULE.httpx, 'AsyncClient') as factory, \
                     patch.object(MODULE, '_get', AsyncMock(side_effect=fixture.lookup)):
                    factory.return_value.__aenter__.return_value = fixture.client
                    asyncio.run(scenario(fixture))
                    fixture.client.delete.assert_not_awaited()

    def test_zero_row_claim_cannot_send(self):
        async def scenario(f):
            f.reject_claim = True
            with self.assertRaises(DELIVERY.DeliveryPending): await f.deliver()
            self.assertEqual((f.creates, f.sends), (1, 0))
        self.run_case(scenario)

    def test_rejected_send_resumes_same_saved_document(self):
        async def scenario(f):
            f.failure = 'rejected'
            with self.assertRaises(DELIVERY.DeliveryUnsent): await f.deliver()
            doc_id = f.row['signwell_document_id']
            f.failure = None
            result = await f.deliver()
            self.assertEqual(result['document_id'], doc_id)
            self.assertTrue(result['recovered'])
            self.assertEqual((f.creates, f.sends), (1, 2))
        self.run_case(scenario)

    def test_timeout_after_acceptance_does_not_send_twice(self):
        async def scenario(f):
            f.failure = 'timeout_sent'
            result = await f.deliver()
            self.assertEqual(result['state'], 'sent')
            self.assertEqual((f.creates, f.sends), (1, 1))
        self.run_case(scenario)

    def test_timeout_after_completion_preserves_completed_state(self):
        async def scenario(f):
            f.failure = 'timeout_completed'
            result = await f.deliver()
            self.assertEqual(result['state'], 'signed')
            self.assertEqual(f.row['status'], 'signed')
            self.assertEqual((f.creates, f.sends), (1, 1))
        self.run_case(scenario)

    def test_uncertain_draft_requires_cooldown_before_same_id_retry(self):
        async def scenario(f):
            f.failure = 'timeout_draft'
            with self.assertRaises(DELIVERY.DeliveryPending): await f.deliver()
            with self.assertRaises(DELIVERY.DeliveryPending): await f.deliver()
            self.assertEqual((f.creates, f.sends), (1, 1))
            f.row[f.field][DELIVERY.JOURNAL_KEY]['started_at'] -= 121
            f.failure = None
            await f.deliver()
            self.assertEqual((f.creates, f.sends), (1, 2))
        self.run_case(scenario)

    def test_successful_send_survives_final_write_failure(self):
        async def scenario(f):
            f.fail_final_write = True
            with self.assertRaises(DELIVERY.DeliveryPending): await f.deliver()
            f.fail_final_write = False
            result = await f.deliver()
            self.assertTrue(result['recovered'])
            self.assertEqual((f.creates, f.sends), (1, 1))
        self.run_case(scenario)

    def test_newer_webhook_completion_is_not_regressed(self):
        async def scenario(f):
            f.failure = 'webhook_first'
            await f.deliver()
            self.assertEqual(f.row['status'], 'signed')
            self.assertEqual(f.row['signed_at'], '2026-09-15T11:00:00Z')
        self.run_case(scenario)

    def test_concurrent_clicks_make_only_one_recipient_facing_send(self):
        async def scenario(f):
            results = await asyncio.gather(f.deliver(), f.deliver(), return_exceptions=True)
            self.assertEqual(f.sends, 1)
            self.assertEqual(sum(isinstance(item, dict) for item in results), 1)
            self.assertTrue(any(isinstance(item, DELIVERY.DeliveryPending) for item in results))
        self.run_case(scenario)

    def test_changed_answers_do_not_send_saved_document(self):
        async def scenario(f):
            f.failure = 'rejected'
            with self.assertRaises(DELIVERY.DeliveryUnsent): await f.deliver()
            f.context['source_revision'] = 'v2'
            with self.assertRaises(DELIVERY.DeliveryMismatch): await f.deliver()
            self.assertEqual((f.creates, f.sends), (1, 1))
        self.run_case(scenario)
