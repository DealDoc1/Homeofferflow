"""Actual listing API handlers/helpers with an isolated HTTP transport."""
import asyncio
from contextlib import ExitStack
from copy import deepcopy
from io import BytesIO
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx
from reportlab.pdfgen.canvas import Canvas

from tests.test_standalone_recipient_preview import MODULE as api
from tests.test_txr_1101 import sample_answers
from lib.txr_1101 import render_txr_1101 as ACTUAL_RENDER


REAL_CLIENT=httpx.AsyncClient
USER={'id':'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','email':'agent@example.test'}
SOURCE_ID='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
AGREEMENT_ID='cccccccc-cccc-4ccc-8ccc-cccccccccccc'


def payload(**answer_changes):
    answers=sample_answers(foreign_person='no',**answer_changes)
    return {'action':'create_txr_1101_draft','formCode':'TXR-1101',
            'formSourceId':SOURCE_ID,'clientNames':answers.pop('client_names'),'agreementData':answers}


def matches(row,params):
    for key,expr in params.items():
        if key in {'select','limit','order'}:continue
        value=row.get(key)
        actual=str(value).lower() if isinstance(value,bool) else str(value)
        if expr.startswith('eq.') and actual!=expr[3:]:return False
        if expr.startswith('in.(') and actual not in expr[4:-1].split(','):return False
        if expr=='is.true' and value is not True:return False
        if expr=='is.null' and value is not None:return False
    return True


class Store:
    def __init__(self):
        self.source={'id':SOURCE_ID,'brokerage_id':'source-host-only','form_code':'TXR-1101',
                     'source_revision':'06-15-26','status':'approved','authorization_attested':True,
                     'storage_bucket':'brokerage-form-sources','storage_path':'source-host/1101.pdf'}
        self.record=None;self.provider=None;self.requests=[];self.provider_creates=0;self.provider_sends=0
        self.profile={'agent_name':'QA Agent','license_number':'000001',
                      'brokerage_name':'Independent QA Realty','brokerage_license':'9000001'}
        self.office=None;self.empty_create=False;self.wrong_owner_create=False
        self.bad_provider_fields=False
        self.fail_inspect_once=False
        self.storage_bytes=b'%PDF-private-source-fixture'
        self.empty_update=False;self.race_update=False;self.normalize_timestamp=False

    def handle(self,request):
        self.requests.append(request)
        path=request.url.path;params=dict(request.url.params)
        if request.url.host=='fixture.supabase.test':
            if path=='/auth/v1/user':
                token=request.headers.get('authorization')
                if token=='Bearer qa-token':return httpx.Response(200,json=USER)
                if token=='Bearer other-token':return httpx.Response(200,json={**USER,'id':'other-owner'})
                return httpx.Response(401,json={})
            if path.startswith('/storage/v1/object/'):
                return httpx.Response(200,content=self.storage_bytes)
            if request.method=='GET':
                if path.endswith('/hof_brokerage_form_sources'):row=self.source
                elif path.endswith('/hof_standalone_agreements'):row=self.record
                elif path.endswith('/hof_agent_profiles'):return httpx.Response(200,json=[self.profile])
                elif path.endswith('/hof_profiles'):return httpx.Response(200,json=[{'brokerage_id':self.office['id']}] if self.office else [])
                elif path.endswith('/hof_brokerage_members'):return httpx.Response(200,json=[{'id':'active-member'}] if self.office else [])
                elif path.endswith('/hof_brokerages'):row=self.office
                else:raise AssertionError('Unexpected fixture read '+path)
                return httpx.Response(200,json=[deepcopy(row)] if row and matches(row,params) else [])
            if path.endswith('/hof_standalone_agreements'):
                body=json.loads(request.content)
                if request.method=='POST':
                    self.record={**body,'id':AGREEMENT_ID,'updated_at':'2026-10-17T13:00:00Z',
                                 'signwell_document_id':None}
                    if self.empty_create:return httpx.Response(201,json=[])
                    returned=deepcopy(self.record)
                    if self.wrong_owner_create:returned['agent_user_id']='another-owner'
                    return httpx.Response(201,json=[returned])
                if request.method=='PATCH':
                    if self.empty_update:return httpx.Response(200,json=[])
                    if self.race_update:
                        self.race_update=False;self.record['updated_at']='2026-10-17T14:00:00Z'
                    if not self.record or not matches(self.record,params):return httpx.Response(200,json=[])
                    self.record.update(body)
                    if self.normalize_timestamp:
                        self.record['updated_at']=self.record['updated_at'].replace('+00:00','Z')
                    return httpx.Response(200,json=[deepcopy(self.record)])
        if request.url.host=='www.signwell.com':
            if request.method=='POST' and path=='/api/v1/documents':
                self.provider_creates+=1
                self.provider={**json.loads(request.content),'id':'qa-provider','status':'draft'}
                if self.bad_provider_fields:self.provider['fields'][0].pop()
                return httpx.Response(201,json=deepcopy(self.provider))
            if request.method=='POST' and path=='/api/v1/documents/qa-provider/send':
                self.provider_sends+=1;self.provider['status']='sent'
                return httpx.Response(200,json=deepcopy(self.provider))
            if request.method=='GET' and path=='/api/v1/documents/qa-provider':
                if self.fail_inspect_once:
                    self.fail_inspect_once=False
                    return httpx.Response(503,json={'error':'fictional temporary inspection failure'})
                return httpx.Response(200,json=deepcopy(self.provider))
        raise AssertionError('No external request permitted: '+str(request.url))


class Txr1101ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stream=BytesIO();canvas=Canvas(stream,pagesize=(612,792))
        for page in range(10):
            canvas.drawString(36,740,'Fictional API transport fixture - page '+str(page+1));canvas.showPage()
        canvas.save();cls.rendered=stream.getvalue()

    def setUp(self):
        self.store=Store();self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(api,'SUPABASE_URL','https://fixture.supabase.test'))
        self.stack.enter_context(patch.object(api,'SUPABASE_SERVICE_ROLE_KEY','qa-service-only'))
        self.stack.enter_context(patch.object(api,'TXR_SIGNING_ENABLED',True))
        self.stack.enter_context(patch.object(api,'SIGNWELL_ENABLED',True))
        self.stack.enter_context(patch.object(api,'SIGNWELL_API_KEY','qa-provider-key'))
        self.stack.enter_context(patch.object(api,'SIGNWELL_TEST_MODE',True))
        transport=httpx.MockTransport(self.store.handle)
        self.stack.enter_context(patch.object(api.httpx,'AsyncClient',
            side_effect=lambda *a,**kw:REAL_CLIENT(*a,transport=transport,**kw)))
        # Source geometry is separately tested against the real private PDF.
        # This boundary spy isolates the API's trusted inputs and delivery flow.
        self.render=self.stack.enter_context(patch('lib.txr_1101.render_txr_1101',return_value=self.rendered))

    def post(self,body,token='qa-token'):
        raw=json.dumps(body).encode();result=[]
        handler=api.handler.__new__(api.handler)
        handler.path='/api/admin-dashboard'
        handler.headers={'authorization':'Bearer '+token,'Content-Length':str(len(raw))}
        handler.rfile=BytesIO(raw)
        with patch.object(api,'_json',side_effect=lambda h,status,value:result.append((status,value))):
            handler.do_POST()
        self.assertEqual(len(result),1)
        return result[0]

    def create(self,**changes):
        status,result=self.post(payload(**changes));self.assertEqual(status,201,result)
        return result['agreement']

    def get(self,path,token='qa-token'):
        result=[];handler=api.handler.__new__(api.handler)
        handler.path=path;handler.headers={'authorization':'Bearer '+token}
        with patch.object(api,'_json',side_effect=lambda h,status,value:result.append((status,value))):
            handler.do_GET()
        self.assertEqual(len(result),1)
        return result[0]

    def test_saved_listing_answers_can_be_reopened_without_delivery_bookkeeping(self):
        self.create(built_before_1978='yes',request_hoa_information='yes',hoa='yes')
        self.store.record['agreement_data']['client_emails']=['private@example.test']
        self.store.record['agreement_data']['broker_signer']={'name':'QA Broker'}
        status,result=self.get('/api/admin-dashboard?scope=txr1101_draft&agreement_id='+AGREEMENT_ID)
        self.assertEqual(status,200,result)
        row=result['agreement'];self.assertEqual(row['form_source_id'],SOURCE_ID)
        self.assertEqual(row['client_names'],payload()['clientNames'])
        self.assertNotIn('client_emails',row['agreement_data']);self.assertNotIn('broker_signer',row['agreement_data'])
        self.assertEqual(row['agreement_data']['built_before_1978'],'yes')
        self.assertEqual(row['agreement_data']['request_hoa_information'],'yes')
        self.assertIn('C',row['agreement_data']['addenda']);self.assertIn('G',row['agreement_data']['addenda'])

    def test_saved_listing_answer_read_cannot_open_another_owner_or_tracked_document(self):
        self.create();url='/api/admin-dashboard?scope=txr1101_draft&agreement_id='+AGREEMENT_ID
        self.assertEqual(self.get(url,token='other-token')[0],404)
        self.store.record['signwell_document_id']='provider-existing'
        self.assertEqual(self.get(url)[0],404)

    def test_saved_listing_answer_read_rejects_invalid_ids_and_missing_auth(self):
        self.assertEqual(self.get('/api/admin-dashboard?scope=txr1101_draft&agreement_id=bad')[0],400)
        self.assertEqual(self.get('/api/admin-dashboard?scope=txr1101_draft&agreement_id='+AGREEMENT_ID,token='bad')[0],401)

    def send_body(self):
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        contacts=[{key:r[key] for key in ('id','name','email')} for r in preview['recipients']]
        return {'action':'send_txr_agreement_for_signature','agreementId':AGREEMENT_ID,
                'confirmedRecipients':contacts}

    def update_body(self,**changes):
        return {**payload(**changes),'action':'update_txr_1101_draft','agreementId':AGREEMENT_ID,
                'updatedAt':self.store.record['updated_at']}

    def test_create_uses_verified_actor_and_shared_source_without_membership_or_send(self):
        result=self.create()
        self.assertEqual(result['agent_user_id'],USER['id'])
        self.assertEqual(result['brokerage_id'],'source-host-only')
        self.assertEqual(result['form_source_id'],SOURCE_ID)
        self.assertEqual(result['agreement_data']['signing_map_revision'],api.TXR_SIGNING_MAP_REVISIONS['TXR-1101'])
        self.assertFalse(any('/hof_brokerage_members' in r.url.path for r in self.store.requests))
        self.assertEqual(self.store.provider_creates,0);self.render.assert_not_called()

    def test_create_requires_auth_and_does_not_trust_browser_identity(self):
        body={**payload(),'agent_user_id':'intruder','brokerage_id':'intruder-office'}
        self.assertEqual(self.post(body,token='invalid')[0],401)
        self.assertIsNone(self.store.record)
        status,result=self.post(body);self.assertEqual(status,201,result)
        self.assertEqual(result['agreement']['agent_user_id'],USER['id'])
        self.assertEqual(result['agreement']['brokerage_id'],'source-host-only')

    def test_invalid_source_and_unapproved_revision_do_not_write_a_draft(self):
        for field,value in [('status','retired'),('authorization_attested',False),('form_code','TXR-1102')]:
            before=deepcopy(self.store.source);self.store.source[field]=value
            status,_=self.post(payload());self.assertEqual(status,400)
            self.assertIsNone(self.store.record);self.store.source=before

    def test_empty_or_wrong_owner_create_readback_cannot_claim_saved(self):
        for field in ('empty_create','wrong_owner_create'):
            setattr(self.store,field,True)
            status,result=self.post(payload());self.assertEqual(status,409)
            self.assertTrue(result['refreshRequired'])
            setattr(self.store,field,False)

    def test_long_unicode_payload_uses_only_the_listing_specific_size_allowance(self):
        body=payload(special_provisions='测试 '*900)
        self.assertGreater(len(json.dumps(body).encode()),api.MAX_BODY_BYTES)
        status,result=self.post(body);self.assertEqual(status,201,result)
        body['action']='not-a-listing-action'
        self.assertEqual(self.post(body)[0],400)

    def test_injected_party_fields_and_metadata_are_rejected(self):
        for values in [dict(agreementData={**payload()['agreementData'],'client_names':['Injected']}),
                       dict(agreementData={**payload()['agreementData'],'_hof_signature_delivery':{}})]:
            status,_=self.post({**payload(),**values});self.assertEqual(status,400)
        self.assertIsNone(self.store.record)

    def test_two_sellers_with_the_same_legal_name_keep_distinct_confirmed_recipients(self):
        self.create(client_names=['QA Same Name','QA Same Name'])
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        sellers=self.store.provider['recipients'][:2]
        self.assertEqual([r['id'] for r in sellers],['1','2'])
        self.assertEqual([r['name'] for r in sellers],['QA Same Name','QA Same Name'])
        self.assertNotEqual(sellers[0]['email'],sellers[1]['email'])

    def test_preview_uses_owned_row_and_current_source_with_private_storage_only(self):
        self.create();context={}
        result=asyncio.run(api._render_representation_draft_preview(USER,AGREEMENT_ID,fingerprint_context=context))
        self.assertEqual(result,self.rendered)
        self.assertEqual(self.render.call_args.args[1]['property_address'],payload()['agreementData']['property_address'])
        self.assertNotIn('signing_map_revision',self.render.call_args.args[1])
        self.assertNotIn('compensation',self.render.call_args.args[1])
        self.assertEqual(context['render_revision'],api.TXR_RENDER_REVISIONS['TXR-1101'])
        self.assertEqual(self.store.provider_creates,0)
        with self.assertRaises(PermissionError):
            asyncio.run(api._render_representation_draft_preview({**USER,'id':'other-owner'},AGREEMENT_ID))

    def test_source_revision_retirement_and_mismatched_saved_parties_fail_before_render(self):
        self.create()
        for change in ('revision','retired','parties'):
            record=deepcopy(self.store.record);source=deepcopy(self.store.source);self.render.reset_mock()
            if change=='revision':self.store.source['source_revision']='new-revision'
            elif change=='retired':self.store.source['status']='retired'
            else:self.store.record['agreement_data']['client_names']=['Altered party']
            with self.subTest(change=change),self.assertRaises(ValueError):
                asyncio.run(api._render_representation_draft_preview(USER,AGREEMENT_ID))
            self.render.assert_not_called();self.store.record=record;self.store.source=source

    def test_recipient_preview_reuses_seller_emails_with_separate_account_associate(self):
        self.create();result=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual([r['label'] for r in result['recipients']][:2],['Seller 1','Seller 2'])
        self.assertEqual([r['email'] for r in result['recipients']],
                         ['seller@example.com','seller2@example.com',USER['email']])
        self.assertEqual(result['recipients'][-1]['id'],'associate')
        self.assertFalse(result['recipients'][-1]['emailEditable'])

    def test_listing_contact_enrichment_uses_only_the_agents_active_office(self):
        self.store.office={'id':'own-office','is_active':True,'name':'QA Realty','license_number':'9000000',
            'office_address':'10 Example Lane','office_city':'Dallas','office_state':'TX','office_zip':'75201',
            'contact_phone':'214-555-0100','contact_email':'broker@example.test','contact_name':'QA Broker'}
        self.create();asyncio.run(api._render_representation_draft_preview(USER,AGREEMENT_ID))
        broker=self.render.call_args.args[2]
        self.assertEqual(broker['address'],'10 Example Lane')
        self.assertEqual(broker['city_state_zip'],'Dallas, TX 75201')
        self.assertEqual(broker['phone'],'214-555-0100')
        self.assertNotEqual(broker['id'],self.store.record['brokerage_id'])

    def test_actual_send_handler_creates_privately_verifies_and_sends_once_without_signing_order(self):
        self.create();body=self.send_body()
        status,result=self.post(body);self.assertEqual(status,200,result)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))
        self.assertFalse(self.store.provider['apply_signing_order'])
        self.assertTrue(self.store.provider['draft'])
        self.assertEqual({f['recipient_id'] for f in self.store.provider['fields'][0]},{'1','2','associate'})
        self.assertEqual(self.store.record['status'],'sent')
        self.assertEqual(self.store.provider['metadata']['render_revision'],api.TXR_RENDER_REVISIONS['TXR-1101'])
        self.assertEqual(self.post(body)[0],403)  # Refresh sent record, never send a duplicate.
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

    def test_wrong_owner_stale_map_unanswered_status_and_changed_recipients_never_contact_provider(self):
        for defect in ('owner','map','unanswered','recipient'):
            self.create();body=self.send_body()
            if defect=='owner':self.store.record['agent_user_id']='other-owner'
            elif defect=='map':self.store.record['agreement_data']['signing_map_revision']='old-map'
            elif defect=='unanswered':self.store.record['agreement_data']['foreign_person']='unanswered'
            else:body['confirmedRecipients'][0]['email']='changed@example.test'
            status,_=self.post(body)
            self.assertIn(status,(400,403),defect)
            self.assertEqual((self.store.provider_creates,self.store.provider_sends),(0,0))

    def test_provider_field_loss_cannot_send_an_invitation(self):
        self.create();body=self.send_body();self.store.bad_provider_fields=True
        status,_=self.post(body)
        self.assertNotEqual(status,200)
        self.assertEqual(self.store.provider_creates,1)
        self.assertEqual(self.store.provider_sends,0)

    def test_failed_provider_inspection_reuses_the_durable_document_and_sends_only_once(self):
        self.create();body=self.send_body();self.store.fail_inspect_once=True
        status,result=self.post(body)
        self.assertEqual(status,409,result)
        self.assertTrue(result['deliveryUnconfirmed'])
        self.assertEqual(self.store.record['signwell_document_id'],'qa-provider')
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,0))
        status,result=self.post(self.send_body())
        self.assertEqual(status,200,result)
        self.assertTrue(result['signwell']['recovered'])
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

    def test_independent_broker_plan_keeps_the_broker_recipient_and_not_the_agent(self):
        self.create(signer_plan='clients_and_broker');body=self.send_body()
        broker={'name':'QA Broker','email':'broker@example.test'}
        body['brokerSigner']=broker
        body['confirmedRecipients'][-1]={'id':'broker',**broker}
        status,result=self.post(body);self.assertEqual(status,200,result)
        self.assertEqual([r['id'] for r in self.store.provider['recipients']],['1','2','broker'])
        self.assertEqual(self.store.record['agreement_data']['broker_signer'],broker)
        self.assertFalse(any('/hof_brokerage_members' in r.url.path for r in self.store.requests))

    def test_edit_updates_the_same_unsent_draft_and_keeps_the_current_signing_revision(self):
        self.create();status,result=self.post(self.update_body(listing_price='650000'))
        self.assertEqual(status,200,result)
        self.assertEqual(result['agreement']['id'],AGREEMENT_ID)
        self.assertEqual(self.store.record['agreement_data']['listing_price'],'650000')
        self.assertEqual(self.store.record['agreement_data']['signing_map_revision'],
                         api.TXR_SIGNING_MAP_REVISIONS['TXR-1101'])
        self.assertEqual(sum(r.method=='POST' and r.url.path.endswith('/hof_standalone_agreements')
                             for r in self.store.requests),1)
        self.assertEqual(self.store.provider_creates,0)

    def test_edits_reject_other_owner_stale_versions_and_tracked_documents(self):
        self.create();body=self.update_body(listing_price='650000')
        self.assertEqual(self.post(body,token='other-token')[0],403)
        body['updatedAt']='old-version';self.assertEqual(self.post(body)[0],400)
        self.assertEqual(self.store.record['agreement_data']['listing_price'],'625000')
        self.store.record['signwell_document_id']='already-prepared'
        self.assertEqual(self.post(self.update_body())[0],403)

    def test_update_race_and_empty_success_cannot_overwrite_or_claim_saved(self):
        for setting in ('race_update','empty_update'):
            self.create();body=self.update_body(listing_price='650000')
            setattr(self.store,setting,True)
            status,result=self.post(body);self.assertEqual(status,409)
            self.assertTrue(result['refreshRequired'])
            self.assertEqual(self.store.record['agreement_data']['listing_price'],'625000')
            setattr(self.store,setting,False)

    def test_equivalent_database_timestamp_format_does_not_report_a_failed_save(self):
        self.create();self.store.normalize_timestamp=True
        status,result=self.post(self.update_body(listing_price='650000'))
        self.assertEqual(status,200,result)
        self.assertTrue(result['agreement']['updated_at'].endswith('Z'))
        self.assertEqual(self.post(self.update_body(listing_price='660000'))[0],200)

    @unittest.skipUnless(os.environ.get('HOF_TXR1101_SOURCE'),'Private exact-source integration QA is opt-in.')
    def test_actual_private_source_runs_through_api_preview_and_delivery_adapter_without_external_io(self):
        from pypdf import PdfReader
        source=Path(os.environ['HOF_TXR1101_SOURCE']).read_bytes()
        self.store.storage_bytes=source;self.render.side_effect=ACTUAL_RENDER
        self.create();preview=asyncio.run(api._render_representation_draft_preview(USER,AGREEMENT_ID))
        reader=PdfReader(BytesIO(preview))
        self.assertEqual(len(reader.pages),10)
        text='\n'.join(p.extract_text() or '' for p in reader.pages)
        self.assertIn('Independent QA Realty',text);self.assertIn('QA Agent',text)
        self.assertNotIn('Andrew Christian',text)
        self.store.storage_bytes=b'%PDF-wrong-source-same-catalog-revision'
        with self.assertRaises(ValueError):
            asyncio.run(api._render_representation_draft_preview(USER,AGREEMENT_ID))
        self.assertEqual(self.store.provider_creates,0)
        self.store.storage_bytes=source
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))


if __name__=='__main__':unittest.main()
