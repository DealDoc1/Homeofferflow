"""Fixed buyer QA recipe and protected source adapter; never sends requests."""
from copy import deepcopy
from io import BytesIO
import json
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from pypdf import PdfReader
from lib import buyer_representation_signing_qa as qa
from tests.test_operator_purchase_signing_qa import MODULE, USER, SCENARIO, response


def source_row(code):
    office = '57f5c952-80af-4ba9-9f7f-ad99dcbc31c5'
    return {'id': '3cc62446-1678-4559-bc2e-07eddd39741a', 'brokerage_id': office,
        'form_code': 'TXR-' + code[3:], 'source_revision': '06-15-26',
        'status': 'approved', 'authorization_attested': True,
        'source_sha256': qa.SOURCE_HASHES[code], 'storage_bucket': 'brokerage-form-sources',
        'storage_path': office + '/' + code + '.pdf'}


async def build_only(user, *, send, _spec):
    packet, fields, cases = await _spec.build_packet()
    return _spec.build_payload(packet, fields, _spec.REVIEWED_SOURCE_COMMIT)


class BuyerOperatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_owner_admin_check_precedes_any_source_or_profile_read(self):
        for user, is_admin in ((USER, False), ({'id': USER['id'], 'email': 'other@example.test'}, True)):
            with patch.object(MODULE, '_get', AsyncMock()) as get, \
                 patch.object(MODULE, '_agent_iabs_profile_record', AsyncMock()) as profile, \
                 patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=is_admin)), \
                 patch.object(MODULE, 'SIGNWELL_ENABLED', True), \
                 patch.object(MODULE, 'SIGNWELL_API_KEY', 'fixture'):
                with self.assertRaises(PermissionError):
                    await MODULE._buyer_package_signing_qa(user, send=True)
                get.assert_not_called(); profile.assert_not_called()

    async def test_recorded_attempt_is_not_recreated_or_sources_reloaded(self):
        notes = json.dumps({'qa_revision': qa.QA_REVISION, 'phase': 'started'})
        with patch.object(MODULE, '_get', AsyncMock(side_effect=[SCENARIO, [{'id': 'run', 'notes': notes}]])), \
             patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=True)), \
             patch.object(MODULE, 'SIGNWELL_ENABLED', True), \
             patch.object(MODULE, 'SIGNWELL_API_KEY', 'fixture'), \
             patch.object(MODULE.httpx, 'AsyncClient') as client, \
             patch.object(MODULE, '_agent_iabs_profile_record', AsyncMock()) as profile:
            result = await MODULE._buyer_package_signing_qa(USER, send=True)
            self.assertEqual(result['phase'], 'started')
            client.assert_not_called(); profile.assert_not_called()

    async def test_bad_catalog_metadata_refused_before_download(self):
        invalid = [{'id': 'bad'}, {'brokerage_id': 'bad'}, {'form_code': 'TXR-1501'},
            {'source_revision': 'old'}, {'status': 'pending_review'},
            {'authorization_attested': False}, {'source_sha256': 'bad'},
            {'storage_bucket': 'public'}, {'storage_path': 'other/form.pdf'},
            {'storage_path': source_row('TXR1507')['brokerage_id'] + '/../form.pdf'}]
        with patch.object(MODULE, '_purchase_signing_qa', build_only), \
             patch.object(MODULE, '_get', AsyncMock()) as get, \
             patch.object(MODULE.httpx, 'AsyncClient') as client:
            for change in invalid:
                get.return_value = [{**source_row('TXR1507'), **change}]
                with self.subTest(change=change), self.assertRaises(ValueError):
                    await MODULE._buyer_package_signing_qa(USER, send=True)
                client.assert_not_called()
            get.return_value = []
            with self.assertRaises(ValueError): await MODULE._buyer_package_signing_qa(USER, send=True)

    async def test_download_failure_and_hash_mismatch_do_not_read_iabs_or_send(self):
        client = AsyncMock(); client.__aenter__.return_value = client
        with patch.object(MODULE, '_purchase_signing_qa', build_only), \
             patch.object(MODULE, '_get', AsyncMock(return_value=[source_row('TXR1507')])), \
             patch.object(MODULE.httpx, 'AsyncClient', return_value=client), \
             patch.object(MODULE, '_agent_iabs_profile_record', AsyncMock()) as profile:
            for status in (404, 503, 200):
                reply = response(status, {}); reply.content = b'%PDF changed'
                client.get.return_value = reply
                with self.subTest(status=status), self.assertRaises(ValueError):
                    await MODULE._buyer_package_signing_qa(USER, send=True)
                profile.assert_not_called(); client.post.assert_not_called()
            client.get.side_effect = RuntimeError('PRIVATE_PROVIDER_VALUE')
            with self.assertRaises(ValueError) as error:
                await MODULE._buyer_package_signing_qa(USER, send=True)
            self.assertNotIn('PRIVATE_PROVIDER_VALUE', str(error.exception))

    def test_action_body_cannot_customize_test_and_is_admin_only(self):
        code = (Path(__file__).resolve().parents[1] / 'api/admin-dashboard.py').read_text()
        start = code.index('if data.get("action") in {"send_buyer_package_signing_test", "check_buyer_package_signing_test"}')
        self.assertLess(code.index('if not asyncio.run(_is_platform_admin(user)):', code.index('def do_POST')), start)
        self.assertIn('if set(data) != {"action"}', code[start:start + 500])


@unittest.skipUnless(os.environ.get('HOF_BUYER_QA_SOURCE_DIR'), 'Private sources not supplied')
class ActualBuyerProviderRecipeTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = qa.load_sources(Path(os.environ['HOF_BUYER_QA_SOURCE_DIR']), qa.IABS_SHA256)

    def test_pinned_recipe_uses_reviewed_sources_fields_and_fixed_test_settings(self):
        packet, fields, cases = qa.build_packet(self.sources)
        self.assertEqual(qa.layout_fingerprint(packet, fields), qa.LAYOUT_SHA256)
        payload = qa.build_payload(packet, fields, qa.REVIEWED_SOURCE_COMMIT)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 9)
        self.assertEqual(len(cases), 1); self.assertEqual(len(fields[0]), 15)
        self.assertEqual({f['recipient_id'] for f in fields[0]}, {'qa_a', 'qa_b'})
        self.assertTrue(all(f['page'] <= 8 for f in fields[0]))
        self.assertEqual(sum(f['type'] == 'signature' for f in fields[0]), 4)
        for key, expected in [('test_mode', True), ('draft', True),
                              ('apply_signing_order', False), ('reminders', False)]:
            self.assertIs(payload[key], expected)
        self.assertEqual(payload['recipients'], list(qa.QA_RECIPIENTS))
        self.assertEqual(payload['checkbox_groups'], [])
        self.assertEqual(payload['conditional_rules'], [])
        changed = deepcopy(fields); changed[0][0]['x'] += 1
        with self.assertRaises(ValueError): qa.build_payload(packet, changed, qa.REVIEWED_SOURCE_COMMIT)
        with self.assertRaises(ValueError): qa.build_payload(packet + b'changed', fields, qa.REVIEWED_SOURCE_COMMIT)
        with self.assertRaises(ValueError): qa.build_payload(packet, fields, '0' * 40)
        for key in self.sources:
            with self.subTest(key=key), self.assertRaises(ValueError):
                qa.build_packet({**self.sources, key: self.sources[key] + b'changed'})

    async def test_private_sources_and_version_checked_own_iabs_feed_shared_runner(self):
        async def get_rows(query):
            return [source_row('TXR' + query.split('form_code=eq.TXR-')[1][:4])]
        client = AsyncMock(); client.__aenter__.return_value = client
        async def download(url, **kwargs):
            self.assertIn('/storage/v1/object/brokerage-form-sources/', url)
            reply = response(200, {}); reply.content = self.sources[url.rsplit('/', 1)[1][:-4]]
            return reply
        client.get.side_effect = download
        profile = {'id': 'owned-iabs', 'updated_at': 'version-one'}
        with patch.object(MODULE, '_purchase_signing_qa', build_only), \
             patch.object(MODULE, '_get', get_rows), \
             patch.object(MODULE.httpx, 'AsyncClient', return_value=client), \
             patch.object(MODULE, '_agent_iabs_profile_record', AsyncMock(return_value=profile)), \
             patch.object(MODULE, '_agent_iabs_profile_pdf', AsyncMock(return_value=(self.sources['IABS'], profile))) as iabs:
            result = await MODULE._buyer_package_signing_qa(USER, send=True)
            self.assertEqual(result['metadata']['layout_sha256'], qa.LAYOUT_SHA256)
            iabs.assert_awaited_once_with(USER, expected_id='owned-iabs', expected_updated_at='version-one')
            client.post.assert_not_called()


if __name__ == '__main__':
    unittest.main()
