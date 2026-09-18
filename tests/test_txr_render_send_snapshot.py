"""Real render -> field map -> delivery adapter, with no network or source files."""
import asyncio
import base64
import copy
from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

from pypdf import PdfReader, PdfWriter
from scripts.run_private_txr_draft_qa import _data
from tests.test_txr_signing_request_path import MODULE


USER = {'id': '11111111-1111-4111-8111-111111111111', 'email': 'agent@example.test'}
RECORD_ID = '22222222-2222-4222-8222-222222222222'


class RenderSendFixture:
    def __init__(self, test, code='TXR-1501', role='associate', count=2, long=False):
        self.test = test
        data = copy.deepcopy(_data()[code.replace('-', '')])
        data.update(data.pop('compensation'))
        names = data.pop('client_names')[:count]
        data.update(signer_plan='clients_and_' + role,
                    signing_map_revision=MODULE.TXR_SIGNING_MAP_REVISIONS[code])
        if long:
            data['market_area'] = 'Long market description ' * 30
        self.row = {'id': RECORD_ID, 'agent_user_id': USER['id'], 'brokerage_id': 'library-host',
                    'status': 'draft', 'updated_at': '2026-09-18T10:00:00Z',
                    'form_code': code, 'form_source_id': 'source', 'source_revision': 'QA-v1',
                    'client_names': names, 'agreement_data': data}
        self.broker = {'id': 'office', 'name': 'QA Brokerage', 'contact_name': 'QA Broker',
                       'contact_email': 'broker@example.test', 'license_number': '0000000'}
        self.profile = {'agent_name': 'QA Associate', 'license_number': '0000000'}
        self.source = {'id': 'source', 'source_revision': 'QA-v1',
                       'storage_bucket': 'private', 'storage_path': 'qa.pdf'}
        writer = PdfWriter()
        for _ in range(6 if code == 'TXR-1501' else 2):
            writer.add_blank_page(width=612, height=792)
        stream = BytesIO()
        writer.write(stream)
        self.source_bytes = stream.getvalue()
        self.source_status = 200
        self.document = None
        self.queries = []
        self.downloads = 0
        self.sends = 0
        self.edit_during_download = False
        self.edit_identity_during_download = False
        self.independent = False
        self.hide_record = False
        self.client = AsyncMock()
        self.client.get.side_effect = self.get
        self.client.post.side_effect = self.post
        self.client.patch.side_effect = self.persist
        self.emails = ['one@example.test', 'two@example.test'][:count]
        self.recipients = MODULE._txr_signwell_recipients(
            self.row, self.emails, self.broker,
            {'email': USER['email'], 'name': self.profile['agent_name']})

    @staticmethod
    def response(body, status=200):
        return SimpleNamespace(status_code=status, json=lambda: copy.deepcopy(body))

    async def lookup(self, path):
        self.queries.append(path)
        if path.startswith('hof_standalone_agreements?'):
            self.test.assertIn('agent_user_id=eq.' + USER['id'], path)
            self.test.assertIn('id=eq.' + RECORD_ID, path)
            self.test.assertIn('status=in.(draft,failed)', path)
            return [] if self.hide_record else [copy.deepcopy(self.row)]
        if path.startswith('hof_brokerage_form_sources?'):
            self.test.assertIn('status=eq.approved&authorization_attested=is.true', path)
            self.test.assertIn('form_code=eq.' + self.row['form_code'], path)
            return [copy.deepcopy(self.source)]
        if path.startswith('hof_brokerages?'):
            self.test.assertIn('id=eq.office', path)
            self.test.assertNotIn('library-host', path)
            return [copy.deepcopy(self.broker)]
        if path.startswith('hof_agent_profiles?'):
            self.test.assertIn('user_id=eq.' + USER['id'], path)
            return [copy.deepcopy(self.profile)]
        if path.startswith('hof_profiles?'):
            self.test.assertIn('id=eq.' + USER['id'], path)
            return [] if self.independent else [{'brokerage_id': 'office'}]
        if path.startswith('hof_brokerage_members?'):
            self.test.assertIn('user_id=eq.' + USER['id'], path)
            self.test.assertIn('brokerage_id=eq.office', path)
            self.test.assertIn('status=eq.active', path)
            return [{'id': 'membership'}]
        raise AssertionError('Unexpected lookup: ' + path)

    async def get(self, url, **kwargs):
        if '/storage/v1/object/private/qa.pdf' in url:
            self.downloads += 1
            if self.edit_during_download:
                self.row['updated_at'] = '2026-09-18T10:01:00Z'
                self.row['client_names'] = ['Changed in another tab']
            if self.edit_identity_during_download:
                self.profile['agent_name'] = 'Changed Associate'
                self.broker['name'] = 'Changed Brokerage'
            return SimpleNamespace(status_code=self.source_status, content=self.source_bytes)
        self.test.assertTrue(url.endswith('/documents/provider-id'))
        return self.response(self.document)

    async def post(self, url, *, json, **kwargs):
        if url.endswith('/documents'):
            self.test.assertIsNone(self.document)
            self.test.assertIs(json['draft'], True)
            self.document = {**copy.deepcopy(json), 'id': 'provider-id', 'status': 'draft'}
            return self.response({'id': 'provider-id'}, 201)
        self.test.assertTrue(url.endswith('/documents/provider-id/send'))
        self.test.assertEqual(self.row['agreement_data'][MODULE.signwell_delivery.JOURNAL_KEY]['phase'], 'sending')
        self.test.assertFalse(json['apply_signing_order'])
        self.sends += 1
        self.document['status'] = 'sent'
        return self.response(self.document, 201)

    async def persist(self, url, *, json, **kwargs):
        query = parse_qs(urlsplit(url).query)
        self.test.assertEqual(query['agent_user_id'], ['eq.' + USER['id']])
        self.test.assertEqual(query['id'], ['eq.' + RECORD_ID])
        if 'agreement_data' in json:
            if query['updated_at'] != ['eq.' + self.row['updated_at']]:
                return self.response([])
        self.row.update(copy.deepcopy(json))
        return self.response([self.row])

    def run(self):
        with patch.object(MODULE, 'TXR_SIGNING_ENABLED', True), \
             patch.object(MODULE, 'SIGNWELL_ENABLED', True), \
             patch.object(MODULE, 'SIGNWELL_API_KEY', 'offline-test'), \
             patch.object(MODULE, '_get', AsyncMock(side_effect=self.lookup)), \
             patch.object(MODULE, '_get_optional', AsyncMock(return_value=[self.profile])), \
             patch.object(MODULE.httpx, 'AsyncClient') as factory:
            factory.return_value.__aenter__.return_value = self.client
            return asyncio.run(MODULE._send_txr_agreement_for_signature(USER, {
                'agreementId': RECORD_ID, 'clientEmails': self.emails,
                'confirmedRecipients': self.recipients,
            }))


class TxrRenderSendSnapshotTests(unittest.TestCase):
    def test_real_render_and_delivery_use_one_source_and_one_owned_draft(self):
        for code in ('TXR-1501', 'TXR-1507'):
            for role in ('associate', 'broker'):
                for count in (1, 2):
                    with self.subTest(code=code, role=role, count=count):
                        f = RenderSendFixture(self, code, role, count)
                        result = f.run()
                        self.assertTrue(result['ok'])
                        self.assertEqual(f.downloads, 1)
                        self.assertEqual(sum(q.startswith('hof_standalone_agreements?') for q in f.queries), 1)
                        self.assertEqual(sum(q.startswith('hof_brokerage_form_sources?') for q in f.queries), 1)
                        self.assertEqual(sum(q.startswith('hof_agent_profiles?') for q in f.queries), 1)
                        self.assertEqual(sum(q.startswith('hof_brokerages?') for q in f.queries), 1)
                        self.assertEqual(f.sends, 1)
                        self.assertEqual(f.document['recipients'], f.recipients)
                        pdf = PdfReader(BytesIO(base64.b64decode(f.document['files'][0]['file_base64'])))
                        text = '\n'.join(p.extract_text() for p in pdf.pages)
                        self.assertIn('Draft Client One', text)
                        self.assertIn('QA Brokerage', text)
                        self.assertEqual(len(pdf.pages), 6 if code == 'TXR-1501' else 2)
                        for field in f.document['fields'][0]:
                            self.assertLessEqual(field['page'], len(pdf.pages))
                        f.client.delete.assert_not_awaited()

    def test_independent_agent_renders_and_sends_own_identity_without_seat(self):
        for code in ('TXR-1501', 'TXR-1507'):
            f = RenderSendFixture(self, code)
            f.independent = True
            f.profile.update(brokerage_name='Independent Profile Office', brokerage_license='7654321')
            self.assertTrue(f.run()['ok'])
            text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(
                base64.b64decode(f.document['files'][0]['file_base64']))).pages)
            self.assertIn('Independent Profile Office', text)
            self.assertIn('7654321', text)
            self.assertNotIn('QA Brokerage', text)
            self.assertFalse(any(q.startswith(('hof_brokerages?', 'hof_brokerage_members?')) for q in f.queries))
            self.assertEqual(f.document['recipients'][-1]['email'], USER['email'])

    def test_render_and_recipient_use_same_identity_snapshot(self):
        f = RenderSendFixture(self)
        f.edit_identity_during_download = True
        self.assertTrue(f.run()['ok'])
        text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(
            base64.b64decode(f.document['files'][0]['file_base64']))).pages)
        self.assertIn('QA Associate', text)
        self.assertIn('QA Brokerage', text)
        self.assertNotIn('Changed Associate', text)
        self.assertNotIn('Changed Brokerage', text)
        self.assertEqual(f.document['recipients'][-1]['name'], 'QA Associate')

    def test_long_form_added_pages_reach_the_actual_delivery_payload(self):
        for role in ('associate', 'broker'):
            for count in (1, 2):
                with self.subTest(role=role, count=count):
                    f = RenderSendFixture(self, role=role, count=count, long=True)
                    f.run()
                    raw = base64.b64decode(f.document['files'][0]['file_base64'])
                    pages = PdfReader(BytesIO(raw)).pages
                    self.assertGreater(len(pages), 6)
                    expected = {r['id'] for r in f.recipients}
                    for number in range(7, len(pages) + 1):
                        fields = [field for field in f.document['fields'][0] if field['page'] == number]
                        self.assertEqual({field['recipient_id'] for field in fields}, expected)
                        self.assertTrue(all(field['required'] and field['type'] == 'initials' for field in fields))

    def test_another_tab_edit_cannot_send_the_old_or_mixed_copy(self):
        f = RenderSendFixture(self)
        f.edit_during_download = True
        with self.assertRaises(MODULE.signwell_delivery.DeliveryPending):
            f.run()
        self.assertEqual(f.sends, 0)
        self.assertEqual(f.row['client_names'], ['Changed in another tab'])
        self.assertNotIn('signwell_document_id', f.row)
        # At most a private unsent provider draft is created; no invitation.
        self.assertEqual(f.document['status'], 'draft')
        text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(
            base64.b64decode(f.document['files'][0]['file_base64']))).pages)
        self.assertIn('Draft Client One', text)
        self.assertNotIn('Changed in another tab', text)

    def test_changed_source_revision_stops_before_download_or_provider_creation(self):
        f = RenderSendFixture(self)
        f.source['source_revision'] = 'QA-v2'
        with self.assertRaisesRegex(ValueError, 'revision'):
            f.run()
        self.assertEqual(f.downloads, 0)
        self.assertIsNone(f.document)

    def test_unavailable_or_invalid_source_never_reaches_provider(self):
        for status, content in ((403, b''), (200, b'not a PDF')):
            with self.subTest(status=status):
                f = RenderSendFixture(self)
                f.source_status, f.source_bytes = status, content
                with self.assertRaisesRegex(RuntimeError, 'source could not be loaded'):
                    f.run()
                self.assertIsNone(f.document)

    def test_missing_owned_draft_has_no_download_or_provider_side_effect(self):
        f = RenderSendFixture(self)
        f.hide_record = True
        with self.assertRaises(PermissionError):
            f.run()
        self.assertEqual(f.downloads, 0)
        self.assertIsNone(f.document)


if __name__ == '__main__':
    unittest.main()
