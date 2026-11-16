"""Actual listing API handlers/helpers with an isolated HTTP transport."""
from contextlib import ExitStack
from copy import deepcopy
from io import BytesIO
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx
from pypdf import PdfReader, PdfWriter

from lib.txr_1101 import render_txr_1101
from tests.test_standalone_recipient_preview import MODULE as api
from tests.test_txr_1101 import sample_answers


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
        self.source_pdf=b'%PDF-fixture'
        self.iabs_pdf=None
        self.record=None;self.requests=[];self.empty_create=False;self.wrong_owner_create=False
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
            if request.method=='GET':
                if path.endswith('/hof_brokerage_form_sources'):row=self.source
                elif path.endswith('/hof_standalone_agreements'):row=self.record
                elif path.endswith('/hof_agent_profiles'):
                    row={'user_id':USER['id'],'agent_name':'QA Associate','brokerage_name':'QA Realty'}
                elif path.endswith(('/hof_profiles','/hof_agent_profile_aliases')):
                    row=None
                elif path.endswith('/hof_agent_documents'):
                    row={'user_id':USER['id'],'document_type':'iabs','storage_bucket':'agent-documents',
                         'storage_path':USER['id']+'/iabs.pdf','mime_type':'application/pdf'} if self.iabs_pdf else None
                elif path=='/storage/v1/object/brokerage-form-sources/source-host/1101.pdf':
                    return httpx.Response(200,content=self.source_pdf)
                elif path=='/storage/v1/object/agent-documents/'+USER['id']+'/iabs.pdf':
                    return httpx.Response(200,content=self.iabs_pdf)
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
        raise AssertionError('No external request permitted: '+str(request.url))


class Txr1101ApiTests(unittest.TestCase):

    def setUp(self):
        self.store=Store();self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(api,'SUPABASE_URL','https://fixture.supabase.test'))
        self.stack.enter_context(patch.object(api,'SUPABASE_SERVICE_ROLE_KEY','qa-service-only'))
        transport=httpx.MockTransport(self.store.handle)
        self.stack.enter_context(patch.object(api.httpx,'AsyncClient',
            side_effect=lambda *a,**kw:REAL_CLIENT(*a,transport=transport,**kw)))
        # Source geometry is separately tested against the real private PDF.
        # This boundary spy isolates the API's trusted inputs and delivery flow.
        self.render=self.stack.enter_context(patch('lib.txr_1101.render_txr_1101'))

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

    def preview(self,token='qa-token'):
        handler=api.handler.__new__(api.handler)
        handler.path='/api/admin-dashboard?preview_agreement='+AGREEMENT_ID
        handler.headers={'authorization':'Bearer '+token}
        handler.wfile=BytesIO()
        with patch.object(handler,'send_response') as status, patch.object(handler,'send_header') as headers, \
                patch.object(handler,'end_headers'):
            handler.do_GET()
        return status.call_args.args[0],dict(call.args for call in headers.call_args_list),handler.wfile.getvalue()

    def test_listing_pdf_preview_is_private_and_only_reads_for_the_verified_owner(self):
        self.create()
        writer=PdfWriter()
        for _ in range(10):
            writer.add_blank_page(width=612,height=792)
        pdf=BytesIO()
        writer.write(pdf)
        self.render.return_value=pdf.getvalue()
        self.store.requests.clear()
        status,headers,body=self.preview()
        self.assertEqual(status,200)
        self.assertEqual(headers['Content-Type'],'application/pdf')
        self.assertEqual(headers['Cache-Control'],'private, no-store')
        self.assertEqual(len(PdfReader(BytesIO(body)).pages),10)
        self.assertEqual(self.render.call_args.args[1]['listing_price'],'625000')
        self.assertTrue(all(request.method=='GET' for request in self.store.requests))
        self.store.requests.clear()
        self.assertEqual(self.preview(token='other-token')[0],403)
        self.assertFalse(any('/storage/' in request.url.path for request in self.store.requests))

    @unittest.skipUnless(os.environ.get('HOF_TXR1101_SOURCE'),'Private exact-source QA is opt-in.')
    def test_listing_preview_combines_exact_source_saved_iabs_and_lead_disclosure(self):
        self.store.source_pdf=Path(os.environ['HOF_TXR1101_SOURCE']).read_bytes()
        self.render.side_effect=render_txr_1101
        writer=PdfWriter()
        writer.add_blank_page(width=612,height=792)
        iabs=BytesIO()
        writer.write(iabs)
        self.store.iabs_pdf=iabs.getvalue()
        self.create(client_names=['QA Single Seller'],built_before_1978='yes')
        status,_,body=self.preview()
        self.assertEqual(status,200)
        pages=PdfReader(BytesIO(body)).pages
        self.assertGreaterEqual(len(pages),12)
        self.assertIn('QA Single Seller',pages[0].extract_text())
        self.assertTrue(any('LEAD-BASED PAINT' in page.extract_text().upper() for page in pages[10:]))
        self.assertTrue(any(request.url.path.endswith('/'+USER['id']+'/iabs.pdf')
                            for request in self.store.requests))

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
        self.render.assert_not_called()

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


    def test_edit_updates_the_same_unsent_draft_and_keeps_the_current_signing_revision(self):
        self.create();status,result=self.post(self.update_body(listing_price='650000'))
        self.assertEqual(status,200,result)
        self.assertEqual(result['agreement']['id'],AGREEMENT_ID)
        self.assertEqual(self.store.record['agreement_data']['listing_price'],'650000')
        self.assertEqual(self.store.record['agreement_data']['signing_map_revision'],
                         api.TXR_SIGNING_MAP_REVISIONS['TXR-1101'])
        self.assertEqual(sum(r.method=='POST' and r.url.path.endswith('/hof_standalone_agreements')
                             for r in self.store.requests),1)
        self.render.assert_not_called()

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

if __name__=='__main__':unittest.main()
