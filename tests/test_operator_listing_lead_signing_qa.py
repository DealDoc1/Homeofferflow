from copy import deepcopy
import json
from unittest.mock import AsyncMock, patch
import unittest
import httpx
from lib import listing_lead_signing_qa as qa
from tests.test_operator_purchase_signing_qa import MODULE, USER, SCENARIO, DOCUMENT_ID, response


class OperatorListingLeadSigningQATests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet,cls.fields,cls.cases=qa.build_packet()
        cls.payload=qa.build_payload(cls.packet,cls.fields,qa.REVIEWED_SOURCE_COMMIT)

    def setUp(self):
        self.client=AsyncMock();self.client.__aenter__.return_value=self.client
        self.provider={**deepcopy(self.payload),'id':DOCUMENT_ID,'status':'draft'}
        self.provider.pop('files')
        self.client.get.return_value=response(200,self.provider)
        self.client.post.side_effect=[response(201,[{'id':'run'}]),
            response(201,{'id':DOCUMENT_ID,'test_mode':True,'status':'draft'}),
            response(201,{'id':DOCUMENT_ID,'test_mode':True,'status':'Sent'})]
        patches=[patch.object(MODULE,'SIGNWELL_ENABLED',True),
            patch.object(MODULE,'SIGNWELL_API_KEY','PRIVATE_KEY'),
            patch.object(MODULE,'_is_platform_admin',AsyncMock(return_value=True)),
            patch.object(MODULE,'_get',AsyncMock(side_effect=[SCENARIO,[]])),
            patch.object(MODULE,'_patch',AsyncMock()),
            patch.object(MODULE.httpx,'AsyncClient',return_value=self.client),
            patch.object(qa,'build_packet',return_value=(self.packet,self.fields,self.cases))]
        for item in patches:item.start();self.addCleanup(item.stop)

    async def test_reserved_draft_is_persisted_verified_then_sent_once(self):
        events=[]
        async def record(*args):events.append(json.loads(args[2]['notes'])['phase'])
        async def inspect(*args,**kwargs):events.append('inspect');return response(200,self.provider)
        MODULE._patch.side_effect=record;self.client.get.side_effect=inspect
        result=await MODULE._listing_lead_signing_qa(USER,send=True)
        self.assertEqual(result['phase'],'created');self.assertEqual(result['document_id'],DOCUMENT_ID)
        self.assertEqual(events,['draft_unverified','inspect','send_started','created'])
        calls=self.client.post.call_args_list
        self.assertIn('/hof_qa_runs',calls[0].args[0]);self.assertTrue(calls[1].kwargs['json']['draft'])
        reserved=json.loads(calls[0].kwargs['json']['notes'])
        self.assertEqual(reserved['layout_sha256'],qa.LAYOUT_SHA256)
        self.assertEqual(len(reserved['completion_controls_sha256']),64)
        self.assertTrue(calls[1].kwargs['json']['test_mode'])
        self.assertTrue(calls[2].args[0].endswith(DOCUMENT_ID+'/send/'))
        self.assertFalse(calls[2].kwargs['json']['apply_signing_order'])
        self.assertNotIn('fields',calls[2].kwargs['json'])
        self.assertNotIn('PRIVATE_KEY',str(result)+str(MODULE._patch.call_args_list))

    async def test_dropped_rules_changed_fields_or_foreign_identity_never_send(self):
        mutations=[lambda d:d.pop('checkbox_groups'),lambda d:d.pop('conditional_rules'),
            lambda d:d['checkbox_groups'][0].update(exact_value=2),
            lambda d:next(field for field in d['fields'][0] if field['type']=='text').pop('validation_regex'),
            lambda d:d['fields'][0][0].update(x=999),
            lambda d:d['recipients'][0].update(email='other@example.test'),
            lambda d:d['metadata'].update(layout_sha256='unknown'),
            lambda d:d.update(apply_signing_order=True),lambda d:d.update(test_mode=False),
            lambda d:d['fields'][0][-1].update(recipient_id='other')]
        for change in mutations:
            with self.subTest(change=change):
                document=deepcopy(self.provider);change(document)
                self.client.get.return_value=response(200,document)
                self.client.post.reset_mock();self.client.post.side_effect=[response(201,[{'id':'run'}]),response(201,{'id':DOCUMENT_ID,'test_mode':True})]
                MODULE._get.side_effect=[SCENARIO,[]]
                result=await MODULE._listing_lead_signing_qa(USER,send=True)
                self.assertEqual(result['phase'],'draft_unverified')
                self.assertEqual(self.client.post.await_count,2);self.assertIn('without invitations',result['message'])

    async def test_failed_draft_checkpoint_never_inspects_or_sends(self):
        MODULE._patch.side_effect=[RuntimeError('PRIVATE_KEY SECRET_LINK'),None]
        result=await MODULE._listing_lead_signing_qa(USER,send=True)
        self.assertEqual(result['phase'],'unconfirmed');self.assertEqual(result['document_id'],DOCUMENT_ID)
        self.client.get.assert_not_called();self.assertEqual(self.client.post.await_count,2)
        self.assertNotIn('PRIVATE_KEY',str(result)+str(MODULE._patch.call_args_list))

    async def test_send_timeout_keeps_exact_document_and_never_retries(self):
        self.client.post.side_effect=[response(201,[{'id':'run'}]),
            response(201,{'id':DOCUMENT_ID,'test_mode':True}),httpx.ReadTimeout('PRIVATE_KEY SECRET_LINK')]
        result=await MODULE._listing_lead_signing_qa(USER,send=True)
        self.assertEqual(result['phase'],'unconfirmed');self.assertEqual(result['document_id'],DOCUMENT_ID)
        self.assertEqual(self.client.post.await_count,3)
        notes=json.loads(MODULE._patch.call_args.args[2]['notes'])
        self.assertIs(notes['controls_verified'],True);self.assertEqual(notes['error_type'],'ReadTimeout')
        self.assertNotIn('SECRET_LINK',str(result)+str(notes))

    async def test_recorded_attempt_and_status_check_never_create_or_send(self):
        run={'id':'run','notes':json.dumps({'qa_revision':qa.QA_REVISION,'phase':'draft_unverified',
            'document_id':DOCUMENT_ID,'test_mode':True})}
        for send in (True,False):
            MODULE._get.side_effect=[SCENARIO,[run]]
            result=await MODULE._listing_lead_signing_qa(USER,send=send)
            self.assertEqual(result['document_id'],DOCUMENT_ID)
        self.client.post.assert_not_called();MODULE._patch.assert_not_called();qa.build_packet.assert_not_called()

    async def test_owner_and_platform_admin_are_both_required(self):
        with self.assertRaises(PermissionError):await MODULE._listing_lead_signing_qa({**USER,'email':'another-admin@example.test'},send=True)
        MODULE._is_platform_admin.return_value=False
        with self.assertRaises(PermissionError):await MODULE._listing_lead_signing_qa(USER,send=True)
        MODULE._get.assert_not_called();self.client.post.assert_not_called()

    async def test_status_with_foreign_layout_never_reports_completion(self):
        MODULE._get.side_effect=[SCENARIO,[{'id':'run','notes':json.dumps({
            'qa_revision':qa.QA_REVISION,'phase':'created','document_id':DOCUMENT_ID,'test_mode':True})}]]
        self.provider['status']='Completed';self.provider['metadata']['layout_sha256']='different'
        result=await MODULE._listing_lead_signing_qa(USER)
        self.assertIn('did not match',result['message']);self.assertNotEqual(result['provider_status'],'completed')
        self.client.post.assert_not_called();MODULE._patch.assert_not_called()

    async def test_non_draft_spec_is_rejected_before_reservation(self):
        with patch.object(qa,'build_payload',return_value={**self.payload,'draft':False}):
            with self.assertRaises(ValueError):await MODULE._listing_lead_signing_qa(USER,send=True)
        self.client.post.assert_not_called()

    def test_route_accepts_only_the_fixed_action_after_admin_check(self):
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/'api/admin-dashboard.py').read_text()
        start=source.index('if data.get("action") in {"send_listing_lead_signing_test", "check_listing_lead_signing_test"}')
        self.assertLess(source.index('if not asyncio.run(_is_platform_admin(user)):',source.index('def do_POST')),start)
        self.assertIn('if set(data) != {"action"}',source[start:start+500])
