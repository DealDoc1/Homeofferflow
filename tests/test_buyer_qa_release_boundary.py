"""Keep this release a protected test capability, without customer activation."""
import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from lib import buyer_representation_signing_qa as buyer
from lib.signwell_qa_readback import required_flags_match
from tests.test_operator_purchase_signing_qa import DOCUMENT_ID, MODULE, SCENARIO, USER, response

ROOT = Path(__file__).resolve().parents[1]


class BuyerQAReleaseBoundaryTests(unittest.TestCase):
    def test_shared_composer_has_only_the_fixed_qa_consumer_in_product_code(self):
        consumers = []
        for folder in ('lib', 'api'):
            for path in (ROOT / folder).glob('*.py'):
                for node in ast.walk(ast.parse(path.read_text())):
                    if isinstance(node, ast.ImportFrom) and node.module == 'lib.representation_package':
                        consumers.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(consumers, ['lib/buyer_representation_signing_qa.py'])

    def test_operator_control_is_owner_scoped_and_disabled_until_status_check(self):
        html = (ROOT / 'index.html').read_text()
        owner = html.index("${['andrewchri@gmail.com', 'andrew@ondemanddfw.com'].includes")
        start = html.index('<summary>Buyer representation package test</summary>')
        self.assertGreater(start, owner)
        button = html[html.index('<button id="adminBuyerPackageSigningTestSend"'):]
        self.assertIn('disabled>', button[:button.index('</button>')])
        self.assertIn("runPurchaseSigningTest(false, this, 'buyer-package')", html)
        draft = html[html.index('<button id="adminBuyerDefaultMessageSigningTestSend"'):]
        self.assertIn('disabled>', draft[:draft.index('</button>')])
        self.assertIn("runPurchaseSigningTest(false, this, 'buyer-default-message')", html)

    def test_default_message_draft_preserves_the_reviewed_packet_and_only_changes_message_and_identity(self):
        packet, fields = b'%PDF-fictional', [[{'type': 'signature'}]]
        with patch.object(buyer, 'PACKET_SHA256', sha256(packet).hexdigest()), \
             patch.object(buyer, 'layout_fingerprint', return_value=buyer.LAYOUT_SHA256):
            original = buyer.build_payload(packet, fields, buyer.REVIEWED_SOURCE_COMMIT)
            draft = buyer.build_default_message_draft_payload(packet, fields, buyer.REVIEWED_SOURCE_COMMIT)
        self.assertIs(draft['draft'], True)
        self.assertIs(draft['test_mode'], True)
        self.assertNotIn('message', draft)
        self.assertTrue(draft['name'].startswith(buyer.DEFAULT_MESSAGE_DOCUMENT_PREFIX))
        self.assertEqual(draft['metadata']['qa_revision'], buyer.DEFAULT_MESSAGE_QA_REVISION)
        self.assertNotEqual(draft['metadata']['qa_revision'], original['metadata']['qa_revision'])
        self.assertEqual({**draft, 'message': original['message'], 'name': original['name'],
                          'metadata': {**draft['metadata'], 'qa_revision': buyer.QA_REVISION}}, original)

    def test_required_flags_match_exact_booleans_including_optional_fields(self):
        fields = [[{'api_id': 'a', 'required': True}, {'api_id': 'b', 'required': False}]]
        document = {'fields': deepcopy(fields)}
        self.assertTrue(required_flags_match(document, fields))
        for value in (None, 0, 1, '', 'true', False):
            document['fields'][0][0]['required'] = value
            self.assertFalse(required_flags_match(document, fields))
        document = {'fields': deepcopy(fields)}
        document['fields'][0][1]['required'] = True
        self.assertFalse(required_flags_match(document, fields))
        for rows in (None, {}, [{}], [[None]], [[{'api_id': 'a'}, {'api_id': 'a'}]]):
            self.assertFalse(required_flags_match({'fields': rows}, fields))


class BuyerQADraftOnlyTests(unittest.IsolatedAsyncioTestCase):
    async def test_draft_only_reserves_once_and_cannot_send_the_new_document(self):
        packet, fields = b'%PDF-fictional', [[{'type': 'signature'}]]
        spec = SimpleNamespace(
            QA_OPERATOR_EMAILS=buyer.QA_OPERATOR_EMAILS, QA_SCENARIO=buyer.QA_SCENARIO,
            QA_RECIPIENTS=buyer.QA_RECIPIENTS, QA_REVISION=buyer.DEFAULT_MESSAGE_QA_REVISION,
            REVIEWED_SOURCE_COMMIT=buyer.REVIEWED_SOURCE_COMMIT, LAYOUT_SHA256=buyer.LAYOUT_SHA256,
            VERIFY_DRAFT=True, DRAFT_ONLY=True, build_packet=lambda: (packet, fields, []),
            build_payload=buyer.build_default_message_draft_payload)
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.post.side_effect = [
            response(201, [{'id': 'draft-run'}]),
            response(201, {'id': DOCUMENT_ID, 'test_mode': True, 'status': 'draft'}),
        ]
        with patch.object(MODULE, 'SIGNWELL_ENABLED', True), \
             patch.object(MODULE, 'SIGNWELL_API_KEY', 'fictional-key'), \
             patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=True)), \
             patch.object(MODULE, '_get', AsyncMock(side_effect=[SCENARIO, []])) as get, \
             patch.object(MODULE, '_patch', AsyncMock()) as checkpoint, \
             patch.object(MODULE, '_verify_and_send_fixed_qa_draft', AsyncMock()) as send, \
             patch.object(MODULE.httpx, 'AsyncClient', return_value=client), \
             patch.object(buyer, 'PACKET_SHA256', sha256(packet).hexdigest()), \
             patch.object(buyer, 'layout_fingerprint', return_value=buyer.LAYOUT_SHA256):
            result = await MODULE._purchase_signing_qa(USER, send=True, _spec=spec)
            notes = checkpoint.await_args.args[2]['notes']
            get.side_effect = [SCENARIO, [{'id': 'draft-run', 'notes': notes}]]
            repeated = await MODULE._purchase_signing_qa(USER, send=True, _spec=spec)
            send.assert_not_awaited()
        self.assertEqual(result, repeated)
        self.assertEqual(result['phase'], 'draft_created')
        self.assertIn('No invitations were requested', result['message'])
        self.assertEqual(json.loads(notes)['qa_revision'], buyer.DEFAULT_MESSAGE_QA_REVISION)
        self.assertEqual(client.post.await_count, 2)
        self.assertIn('/rest/v1/hof_qa_runs', client.post.await_args_list[0].args[0])
        self.assertTrue(client.post.await_args_list[1].args[0].endswith('/api/v1/documents'))
        self.assertNotIn('message', client.post.await_args_list[1].kwargs['json'])
        client.get.assert_not_called()


class BuyerQAIabsHelperTests(unittest.IsolatedAsyncioTestCase):
    def row(self):
        return {'id': 'saved-iabs', 'user_id': USER['id'], 'document_type': 'iabs',
            'storage_bucket': 'agent-documents', 'storage_path': USER['id'] + '/iabs.pdf',
            'mime_type': 'application/pdf', 'byte_size': 8, 'updated_at': 'version-one'}

    async def test_record_checks_ownership_private_path_and_exact_version(self):
        with patch.object(MODULE, '_get', AsyncMock(return_value=[self.row()])) as get:
            self.assertEqual(await MODULE._agent_iabs_profile_record(USER), self.row())
            self.assertIn('user_id=eq.' + USER['id'], get.call_args.args[0])
            for change in ({'user_id': 'other'}, {'storage_path': 'other/iabs.pdf'},
                           {'storage_bucket': 'public'}, {'byte_size': True}):
                get.return_value = [{**self.row(), **change}]
                with self.subTest(change=change), self.assertRaises(ValueError):
                    await MODULE._agent_iabs_profile_record(USER)
            get.return_value = [self.row()]
            with self.assertRaises(ValueError):
                await MODULE._agent_iabs_profile_record(USER, expected_updated_at='stale')
            with self.assertRaises(ValueError):
                await MODULE._agent_iabs_profile_record(USER, expected_id='foreign')

    async def test_pdf_rechecks_version_after_download_and_rejects_changed_profile(self):
        client = AsyncMock(); client.__aenter__.return_value = client
        reply = response(200, {}); reply.content = b'%PDF1234'; client.get.return_value = reply
        with patch.object(MODULE.httpx, 'AsyncClient', return_value=client), \
             patch.object(MODULE, '_agent_iabs_profile_record', AsyncMock(side_effect=[self.row(), ValueError('changed')])) as record:
            with self.assertRaisesRegex(ValueError, 'changed'):
                await MODULE._agent_iabs_profile_pdf(USER, expected_id='saved-iabs', expected_updated_at='version-one')
            self.assertEqual(record.await_count, 2)
            self.assertIn('/agent-documents/' + USER['id'] + '/iabs.pdf', client.get.call_args.args[0])
            client.post.assert_not_called()


if __name__ == '__main__':
    unittest.main()
