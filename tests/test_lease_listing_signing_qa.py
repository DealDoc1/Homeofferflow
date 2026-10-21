"""Fixed fictional provider recipe; all preparation here stays offline."""
from copy import deepcopy
from io import BytesIO
import os
import json
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from pypdf import PdfReader
from lib import lease_listing_signing_qa as qa
from tests.test_operator_purchase_signing_qa import MODULE, USER, SCENARIO, response


def source_row(code='TXR-1102'):
    spec = {'revision': '01-05-26', 'sha256': qa.SOURCE_SHA256} if code == 'TXR-1102' else qa.SOURCES[code]
    return {'id': qa.SOURCE_ID if code == 'TXR-1102' else '1c03c861-8981-493b-a90d-0993adeb3ed1',
        'brokerage_id': 'qa-source-office', 'form_code': code,
        'source_revision': spec['revision'], 'source_sha256': spec['sha256'],
        'status': 'approved', 'authorization_attested': True,
        'storage_bucket': 'brokerage-form-sources', 'storage_path': 'qa-source-office/' + code + '.pdf'}


class FixedLeaseQATests(unittest.TestCase):
    def test_no_arbitrary_sources_or_roles(self):
        for sources in ({}, {'TXR-1102': b'%PDF'}, None):
            with self.subTest(sources=sources), self.assertRaises(ValueError): qa.build_packet(sources)
        for role in ('2', 'broker', 'tenant', '', None):
            with self.subTest(role=role), self.assertRaises(ValueError): qa._recipient(role)
        self.assertEqual(qa._recipient('1'), 'qa_a')
        self.assertEqual(qa._recipient('associate'), 'qa_b')

    def test_controls_require_landlord_facts_without_claiming_tenant_receipt(self):
        groups, rules = qa.completion_controls()
        self.assertEqual(len(groups), 4); self.assertEqual(len(rules), 2)
        self.assertTrue(all(g['recipient_id'] == 'qa_a' and g['exact_value'] == 1 for g in groups))
        self.assertEqual(len(qa.answers()['client_names']), 1)
        for rule in rules:
            self.assertEqual(rule['action_type'], 'require')
            self.assertIn('explanation', rule['action_field_ids'][0])

    def test_unreviewed_revision_and_layout_fail_closed(self):
        with self.assertRaises(ValueError): qa.build_payload(b'%PDF', [[]], '0' * 40)
        with patch.object(qa, 'LAYOUT_SHA256', ''):
            with self.assertRaises(ValueError): qa.build_payload(b'%PDF', [[]], qa.REVIEWED_SOURCE_COMMIT)


@unittest.skipUnless(os.environ.get('HOF_TXR1102_SOURCE') and os.environ.get('HOF_LEASE_DISCLOSURE_SOURCES'),
                     'private reviewed sources supplied for local QA')
class ActualLeaseQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = Path(os.environ['HOF_LEASE_DISCLOSURE_SOURCES'])
        cls.sources = {'TXR-1102': Path(os.environ['HOF_TXR1102_SOURCE']).read_bytes(),
            'TXR-2008': (folder / 'TXR-2008-2003-10-14.pdf').read_bytes(),
            'TXR-2015': (folder / 'TXR-2015-2025-09-01.pdf').read_bytes()}
        cls.packet, cls.fields, cls.cases = qa.build_packet(cls.sources)

    def test_one_ordinary_transaction_real_pages_and_lower_associate_row(self):
        self.assertEqual(len(PdfReader(BytesIO(self.packet)).pages), 14)
        self.assertEqual(len(self.cases), 1)
        self.assertEqual({f['recipient_id'] for f in self.fields[0]}, {'qa_a', 'qa_b'})
        signature = next(f for f in self.fields[0] if f['api_id'] == 'listing_C_lease2008_associate_signature')
        self.assertEqual(signature['page'], 13); self.assertEqual(signature['height'], 18)
        self.assertFalse(any('tenant' in f['api_id'].lower() or 'landlord2' in f['api_id'].lower()
                             for f in self.fields[0]))
        self.assertEqual(sum(f['type'] == 'signature' for f in self.fields[0]), 5)
        ids = {f['api_id']: f for f in self.fields[0]}
        groups, rules = qa.completion_controls()
        for group in groups:
            self.assertTrue(all(ids[key]['type'] == 'checkbox' for key in group['checkbox_ids']))
        for rule in rules:
            self.assertEqual(ids[rule['action_field_ids'][0]]['page'], 14)

    def test_review_pin_fixed_recipients_test_mode_parallel_no_reminders(self):
        payload = qa.build_payload(self.packet, self.fields, qa.REVIEWED_SOURCE_COMMIT)
        for key, value in [('test_mode', True), ('draft', True), ('apply_signing_order', False), ('reminders', False)]:
            self.assertIs(payload[key], value)
        self.assertEqual({r['email'] for r in payload['recipients']},
                         {'andrewchri@gmail.com', 'brewbqinfo@gmail.com'})
        self.assertIn('Tenant receipt/signature', payload['message'])
        changed = deepcopy(self.fields); changed[0][-1]['height'] += 1
        with self.assertRaises(ValueError): qa.build_payload(self.packet, changed, qa.REVIEWED_SOURCE_COMMIT)
        payload['fields'][0][0]['x'] += 1
        self.assertNotEqual(payload['fields'], self.fields)

    def test_each_altered_source_is_rejected(self):
        for code in self.sources:
            with self.subTest(code=code), self.assertRaises(ValueError):
                qa.build_packet({**self.sources, code: self.sources[code] + b'changed'})


class FixedLeaseOperatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_owner_admin_and_connection_checks_precede_source_reads(self):
        with patch.object(MODULE, '_get', AsyncMock()) as get, \
             patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=False)), \
             patch.object(MODULE, 'SIGNWELL_ENABLED', True), patch.object(MODULE, 'SIGNWELL_API_KEY', 'fixture'):
            with self.assertRaises(PermissionError): await MODULE._lease_listing_signing_qa(USER, send=True)
            get.assert_not_called()

    async def test_existing_reserved_attempt_does_not_reload_sources_or_send_again(self):
        notes = json.dumps({'qa_revision': qa.QA_REVISION, 'phase': 'started'})
        with patch.object(MODULE, '_get', AsyncMock(side_effect=[SCENARIO, [{'id': 'existing-run', 'notes': notes}]])) as get, \
             patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=True)), \
             patch.object(MODULE, 'SIGNWELL_ENABLED', True), patch.object(MODULE, 'SIGNWELL_API_KEY', 'fixture'), \
             patch.object(MODULE.httpx, 'AsyncClient') as client:
            result = await MODULE._lease_listing_signing_qa(USER, send=True)
            self.assertEqual(result['phase'], 'started')
            self.assertEqual(get.await_count, 2); client.assert_not_called()

    async def test_bad_source_metadata_fails_before_download(self):
        async def invoke(user, *, send, _spec): return await _spec.build_packet()
        invalid = [{'id': 'wrong'}, {'id': '1c03c861-8981-493b-a90d-0993adeb3ed1'},
            {'form_code': 'TXR-1101'}, {'source_revision': 'old'}, {'source_sha256': 'changed'},
            {'status': 'pending_review'}, {'authorization_attested': False},
            {'storage_bucket': 'public'}, {'storage_path': 'qa-source-office/../other.pdf'},
            {'storage_path': 'other/source.pdf'}, {'storage_path': 'qa-source-office//source.pdf'}]
        with patch.object(MODULE, '_purchase_signing_qa', invoke), \
             patch.object(MODULE, '_get', AsyncMock()) as get, \
             patch.object(MODULE.httpx, 'AsyncClient') as client:
            for change in invalid:
                get.return_value = [{**source_row(), **change}]
                with self.subTest(change=change), self.assertRaises(ValueError):
                    await MODULE._lease_listing_signing_qa(USER, send=True)
                client.assert_not_called()
            get.return_value = []
            with self.assertRaises(ValueError): await MODULE._lease_listing_signing_qa(USER, send=True)

    async def test_download_errors_and_content_mismatch_never_build_or_send(self):
        async def invoke(user, *, send, _spec): return await _spec.build_packet()
        client = AsyncMock(); client.__aenter__.return_value = client
        with patch.object(MODULE, '_purchase_signing_qa', invoke), \
             patch.object(MODULE, '_get', AsyncMock(return_value=[source_row()])), \
             patch.object(MODULE.httpx, 'AsyncClient', return_value=client), \
             patch.object(qa, 'build_packet') as build:
            for status in (404, 503, 200):
                reply = response(status, {}); reply.content = b'%PDF altered'
                client.get.return_value = reply
                with self.subTest(status=status), self.assertRaises(ValueError):
                    await MODULE._lease_listing_signing_qa(USER, send=True)
                build.assert_not_called(); client.post.assert_not_called()
            client.get.side_effect = RuntimeError('PRIVATE_KEY')
            with self.assertRaises(ValueError) as error: await MODULE._lease_listing_signing_qa(USER, send=True)
            self.assertNotIn('PRIVATE_KEY', str(error.exception))

    def test_route_is_admin_only_and_refuses_custom_input(self):
        code = (Path(__file__).resolve().parents[1] / 'api/admin-dashboard.py').read_text()
        start = code.index('if data.get("action") in {"send_lease_listing_signing_test", "check_lease_listing_signing_test"}')
        self.assertLess(code.index('if not asyncio.run(_is_platform_admin(user)):', code.index('def do_POST')), start)
        self.assertIn('if set(data) != {"action"}', code[start:start + 500])
        html = (Path(__file__).resolve().parents[1] / 'index.html').read_text()
        owner = html.index("${['andrewchri@gmail.com', 'andrew@ondemanddfw.com'].includes")
        self.assertGreater(html.index('<summary>Lease listing package test</summary>'), owner)
        control = html[html.index('<button id="adminLeaseListingSigningTestSend"'):]
        self.assertIn('disabled>', control[:control.index('</button>')])
        self.assertIn("runPurchaseSigningTest(false, this, 'lease-listing')", html)

    @unittest.skipUnless(os.environ.get('HOF_TXR1102_SOURCE') and os.environ.get('HOF_LEASE_DISCLOSURE_SOURCES'),
                         'private reviewed sources supplied for local QA')
    async def test_real_sources_load_privately_into_the_reviewed_specimen(self):
        folder = Path(os.environ['HOF_LEASE_DISCLOSURE_SOURCES'])
        sources = {'TXR-1102': Path(os.environ['HOF_TXR1102_SOURCE']).read_bytes(),
            'TXR-2008': (folder / 'TXR-2008-2003-10-14.pdf').read_bytes(),
            'TXR-2015': (folder / 'TXR-2015-2025-09-01.pdf').read_bytes()}
        async def invoke(user, *, send, _spec):
            packet, fields, cases = await _spec.build_packet()
            return _spec.build_payload(packet, fields, _spec.REVIEWED_SOURCE_COMMIT)
        async def get_rows(query):
            return [source_row(next(code for code in sources if 'form_code=eq.' + code in query))]
        async def download(url, **kwargs):
            self.assertIn('/storage/v1/object/brokerage-form-sources/qa-source-office/', url)
            reply = response(200, {}); reply.content = sources[url.rsplit('/', 1)[1].removesuffix('.pdf')]
            return reply
        client = AsyncMock(); client.__aenter__.return_value = client; client.get.side_effect = download
        with patch.object(MODULE, '_purchase_signing_qa', invoke), \
             patch.object(MODULE, '_get', get_rows), patch.object(MODULE.httpx, 'AsyncClient', return_value=client):
            payload = await MODULE._lease_listing_signing_qa(USER, send=True)
            self.assertEqual(payload['metadata']['layout_sha256'], qa.LAYOUT_SHA256)
            self.assertEqual(len(payload['fields'][0]), 44)
            self.assertEqual(client.get.await_count, 3); client.post.assert_not_called()
