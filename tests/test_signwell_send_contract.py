"""Exercise creation -> field verification -> supported send options offline."""
import asyncio
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from tests.test_txr_1507_renderer import blank_two_page_pdf


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('admin_send_contract', ROOT / 'api/admin-dashboard.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
RECORD_ID = '11111111-1111-4111-8111-111111111111'
USER = {'id': 'owner', 'email': 'agent@example.com'}


class SignwellSendContractTests(unittest.TestCase):
    def test_allowlist_excludes_create_only_and_unknown_options(self):
        source = {'draft': True, 'files': [], 'fields': [], 'recipients': [],
                  'with_signature_page': False, 'future_creation_setting': True,
                  'test_mode': False, 'apply_signing_order': True,
                  'embedded_signing': False, 'metadata': {'source': 'HomeOfferFlow'}}
        original = copy.deepcopy(source)
        self.assertEqual(MODULE._signwell_send_options(source), {
            'test_mode': False, 'apply_signing_order': True,
            'embedded_signing': False, 'metadata': {'source': 'HomeOfferFlow'},
        })
        self.assertEqual(source, original)

    def exercise_send(self, kind, changed_field=False, retry=False):
        created = {}
        calls = []
        client = AsyncMock()

        async def post(url, *, json, **kwargs):
            if url.endswith('/send'):
                calls.append('send')
                # Explicit contract validation: the original implementation
                # violated this allowlist by forwarding with_signature_page.
                self.assertFalse(set(json) & {'with_signature_page', 'draft', 'fields', 'files', 'recipients'})
                self.assertIs(json['apply_signing_order'], False)
                self.assertFalse(json['embedded_signing'])
                self.assertEqual(json['metadata'], created['metadata'])
                if retry and calls.count('send') == 1:
                    return SimpleNamespace(status_code=402, json=lambda: {})
                return SimpleNamespace(status_code=201, json=lambda: {'id': 'provider-id', 'status': 'sent'})
            calls.append('create')
            created.update(copy.deepcopy(json))
            self.assertTrue(json['draft'])
            self.assertFalse(json['with_signature_page'])
            self.assertIs(json['apply_signing_order'], False)
            return SimpleNamespace(status_code=201, json=lambda: {'id': 'provider-id'})

        async def get(url, **kwargs):
            if '/storage/' in url:
                return SimpleNamespace(status_code=200, content=b'%PDF-source')
            calls.append('inspect')
            document = copy.deepcopy(created)
            if changed_field:
                document['fields'][0][0]['y'] += 100
            return SimpleNamespace(status_code=200, json=lambda: document)

        client.post.side_effect = post
        client.get.side_effect = get
        async def checkpoint(url, *, json, headers):
            self.assertIn('id=eq.' + RECORD_ID, url)
            self.assertIn('agent_user_id=eq.owner', url)
            self.assertEqual(headers['Prefer'], 'return=representation')
            if 'agreement_data' in json or 'response_data' in json:
                self.assertIn('updated_at=eq.', url)
                calls.append('checkpoint')
            record.update(copy.deepcopy(json))
            return SimpleNamespace(status_code=200, json=lambda: [copy.deepcopy(record)])
        client.patch.side_effect = checkpoint
        recipients = [{'id': '1', 'name': 'Client One', 'email': 'client@example.com'},
                      {'id': 'associate', 'name': 'Agent One', 'email': 'agent@example.com'}]
        agreement = {'id': RECORD_ID, 'form_code': 'TXR-1507', 'status': 'failed',
                     'updated_at': '2026-09-15T13:00:00+00:00',
                     'form_source_id': 'source', 'source_revision': '06-15-26',
                     'client_names': ['Client One'], 'agreement_data': {
                         'signer_plan': 'clients_and_associate', 'service_level': 'full_services',
                         'intermediary': 'authorized', 'purchase_percentage': '3',
                         'signing_map_revision': MODULE.TXR_SIGNING_MAP_REVISIONS['TXR-1507']}}
        source = {'source_revision': '06-15-26', 'storage_bucket': 'private', 'storage_path': 'source.pdf'}
        disclosure = {'id': RECORD_ID, 'seller_names': ['Seller One'], 'buyer_names': ['Buyer One'],
                      'updated_at': '2026-09-15T13:00:00+00:00', 'status': 'draft', 'response_data': {}}
        record = agreement if kind == 'agreement' else disclosure
        async def lookup(query):
            return [copy.deepcopy(source if 'hof_brokerage_form_sources?' in query else record)]
        with patch.object(MODULE, 'TXR_SIGNING_ENABLED', True), \
             patch.object(MODULE, 'SIGNWELL_ENABLED', True), \
             patch.object(MODULE, 'SIGNWELL_API_KEY', 'test-only'), \
             patch.object(MODULE, '_get', AsyncMock(side_effect=lookup)), \
             patch.object(MODULE, '_patch', AsyncMock()) as persist, \
             patch.object(MODULE, '_standalone_signing_recipients', AsyncMock(return_value=recipients)), \
             patch.object(MODULE, '_render_owned_representation_agreement', AsyncMock(return_value=blank_two_page_pdf())), \
             patch.object(MODULE, '_render_seller_disclosure_draft_preview', AsyncMock(return_value=b'%PDF-rendered')), \
             patch.object(MODULE.httpx, 'AsyncClient') as factory:
            factory.return_value.__aenter__.return_value = client
            def operation():
                if kind == 'agreement':
                    return MODULE._send_txr_agreement_for_signature(USER, {
                        'agreementId': RECORD_ID, 'clientEmails': ['client@example.com'],
                        'confirmedRecipients': recipients,
                    })
                return MODULE._send_seller_disclosure_for_signature(USER, {
                    'draftId': RECORD_ID, 'signerEmails': ['seller@example.com', 'buyer@example.com'],
                })
            if retry:
                with self.assertRaises(MODULE.signwell_delivery.DeliveryUnsent):
                    asyncio.run(operation())
                self.assertEqual(record['signwell_document_id'], 'provider-id')
                result = asyncio.run(operation())
                self.assertTrue(result['ok'])
                self.assertTrue(result['recovered'])
                self.assertEqual(calls.count('create'), 1)
                self.assertEqual(calls.count('send'), 2)
                client.delete.assert_not_awaited()
                return
            if changed_field:
                with self.assertRaises(MODULE.signwell_delivery.DeliveryMismatch):
                    asyncio.run(operation())
                self.assertEqual(calls, ['create', 'checkpoint', 'inspect'])
                self.assertEqual(record['signwell_document_id'], 'provider-id')
                client.delete.assert_not_awaited()
            else:
                result = asyncio.run(operation())
                self.assertTrue(result['ok'])
                self.assertEqual(calls, ['create', 'checkpoint', 'inspect', 'checkpoint', 'send'])
                self.assertEqual(record['status'], 'sent')
                self.assertEqual(record['signwell_document_id'], 'provider-id')
                persist.assert_not_awaited()

    def test_agreement_sends_only_after_field_verification(self):
        self.exercise_send('agreement')

    def test_disclosure_uses_same_supported_send_contract(self):
        self.exercise_send('disclosure')

    def test_changed_field_blocks_both_send_paths(self):
        for kind in ('agreement', 'disclosure'):
            with self.subTest(kind=kind):
                self.exercise_send(kind, changed_field=True)

    def test_rejected_request_retries_existing_id_through_both_real_routes(self):
        for kind in ('agreement', 'disclosure'):
            with self.subTest(kind=kind):
                self.exercise_send(kind, retry=True)
