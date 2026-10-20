from copy import deepcopy
from io import BytesIO
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from pypdf import PdfReader
from lib import listing_package_signing_qa as qa
from tests.test_operator_purchase_signing_qa import MODULE, USER, response


class ListingPackageFixedQATests(unittest.TestCase):
    def test_rejects_wrong_source_and_unreviewed_layout(self):
        with self.assertRaises(ValueError): qa.build_packet(b'%PDF not the approved source')
        with self.assertRaises(ValueError): qa.build_payload(b'%PDF', [], '0'*40)
        with patch.object(qa, 'LAYOUT_SHA256', ''):
            with self.assertRaises(ValueError): qa.build_payload(b'%PDF', [], qa.REVIEWED_SOURCE_COMMIT)

    def test_fixed_roles_and_controls_do_not_infer_a_third_signer(self):
        self.assertEqual(qa._recipient('1'), 'qa_a')
        self.assertEqual(qa._recipient('associate'), 'qa_b')
        for role in ('2', 'broker', 'buyer', '', None):
            with self.subTest(role=role), self.assertRaises(ValueError): qa._recipient(role)
        groups, rules = qa.completion_controls()
        self.assertEqual(len(groups), 2); self.assertEqual(len(rules), 2)
        self.assertTrue(all(group['recipient_id']=='qa_a' for group in groups))
        self.assertEqual(len(qa.answers()['client_names']), 1)

    @unittest.skipUnless(os.environ.get('HOF_TXR1101_SOURCE'), 'private actual source provided for local QA')
    def test_actual_source_is_one_ordinary_transaction_using_real_composition(self):
        source=Path(os.environ['HOF_TXR1101_SOURCE']).read_bytes()
        packet, fields, manifest = qa.build_packet(source)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 12)
        self.assertEqual(len(fields[0]), 34); self.assertEqual(len(manifest), 1)
        self.assertEqual({field['recipient_id'] for field in fields[0]}, {'qa_a','qa_b'})
        self.assertEqual(sum(field['type']=='signature' for field in fields[0]), 4)
        self.assertFalse(any('buyer' in field['api_id'] or 'seller2' in field['api_id'] for field in fields[0]))
        self.assertTrue(all(field['page']==12 and field['height']==18 for field in fields[0] if field['type']=='text'))
        payload=qa.build_payload(packet, fields, qa.REVIEWED_SOURCE_COMMIT)
        self.assertIs(payload['test_mode'],True); self.assertIs(payload['draft'],True)
        self.assertIs(payload['apply_signing_order'],False); self.assertIs(payload['reminders'],False)
        self.assertEqual({r['email'] for r in payload['recipients']}, {'andrewchri@gmail.com','brewbqinfo@gmail.com'})
        changed=deepcopy(fields); changed[0][0]['x']+=1
        with self.assertRaises(ValueError): qa.build_payload(packet,changed,qa.REVIEWED_SOURCE_COMMIT)
        self.assertNotIn('broker@example.com', ''.join(page.extract_text() for page in PdfReader(BytesIO(packet)).pages))


class ListingPackageOperatorQATests(unittest.IsolatedAsyncioTestCase):
    async def test_owner_and_admin_required_before_source_access(self):
        with patch.object(MODULE, '_get', AsyncMock()) as get, \
             patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=False)), \
             patch.object(MODULE,'SIGNWELL_ENABLED',True),patch.object(MODULE,'SIGNWELL_API_KEY','fixture'):
            with self.assertRaises(PermissionError): await MODULE._listing_package_signing_qa(USER,send=True)
            get.assert_not_called()

    async def test_fixed_registered_source_download_stays_server_side(self):
        client=AsyncMock(); client.__aenter__.return_value=client
        client.get.return_value=response(200,{}); client.get.return_value.content=b'%PDF fictional fixture'
        source={'id':qa.SOURCE_ID,'source_revision':'06-15-26','source_sha256':qa.SOURCE_SHA256,
            'storage_bucket':'private-forms','storage_path':'fictional/source.pdf'}
        async def invoke(user, *,send,_spec):
            self.assertIs(send,True); self.assertIs(_spec.VERIFY_DRAFT,True)
            self.assertEqual(_spec.QA_RECIPIENTS,qa.QA_RECIPIENTS)
            return await _spec.build_packet()
        with patch.object(MODULE,'_purchase_signing_qa',invoke), \
             patch.object(MODULE,'_get',AsyncMock(return_value=[source])) as get, \
             patch.object(MODULE.httpx,'AsyncClient',return_value=client), \
             patch.object(qa,'build_packet',return_value=('packet','fields','manifest')) as build:
            result=await MODULE._listing_package_signing_qa(USER,send=True)
            self.assertEqual(result,('packet','fields','manifest'))
            self.assertIn('id=eq.'+qa.SOURCE_ID,get.call_args.args[0])
            self.assertIn('authorization_attested=is.true',get.call_args.args[0])
            build.assert_called_once_with(b'%PDF fictional fixture')
            self.assertIn('/storage/v1/object/private-forms/fictional/source.pdf',client.get.call_args.args[0])
            for key in ('id','source_revision','source_sha256'):
                wrong={**source,key:'wrong'}
                get.return_value=[wrong]; client.get.reset_mock();build.reset_mock()
                with self.subTest(key=key),self.assertRaises(ValueError): await MODULE._listing_package_signing_qa(USER,send=True)
                client.get.assert_not_called();build.assert_not_called()

    def test_route_accepts_only_fixed_action_and_remains_behind_admin_check(self):
        source=(Path(__file__).resolve().parents[1]/'api/admin-dashboard.py').read_text()
        start=source.index('if data.get("action") in {"send_listing_package_signing_test", "check_listing_package_signing_test"}')
        self.assertLess(source.index('if not asyncio.run(_is_platform_admin(user)):',source.index('def do_POST')),start)
        self.assertIn('if set(data) != {"action"}',source[start:start+500])
