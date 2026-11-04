"""Keep this release a protected test capability, without customer activation."""
import ast
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from lib.signwell_qa_readback import required_flags_match
from tests.test_operator_purchase_signing_qa import MODULE, USER, response

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
