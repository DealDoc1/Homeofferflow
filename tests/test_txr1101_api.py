"""Actual listing API handlers/helpers with an isolated HTTP transport."""
import asyncio
from contextlib import ExitStack
from copy import deepcopy
import base64
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
SHARED_PROFILE_ID='dddddddd-dddd-4ddd-8ddd-dddddddddddd'
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
        self.alias=None;self.shared_profile=None;self.alias_wrong_row=False
        self.iabs=None;self.iabs_bytes=None;self.iabs_wrong_row=False
        self.iabs_error=404
        self.disclosure=None
        self.bad_completion_controls=False
        self.bad_provider_fields=False
        self.fail_inspect_once=False
        self.storage_bytes=b'%PDF-private-source-fixture'
        self.related_sources=[];self.related_files={}
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
                if path in self.related_files:
                    status,content=self.related_files[path]
                    return httpx.Response(status,content=content)
                if '/agent-documents/' in path:
                    return httpx.Response(200,content=self.iabs_bytes) if self.iabs_bytes else httpx.Response(self.iabs_error,content=b'')
                return httpx.Response(200,content=self.storage_bytes)
            if request.method=='GET':
                if path.endswith('/hof_brokerage_form_sources'):
                    return httpx.Response(200,json=[deepcopy(row) for row in [self.source,*self.related_sources] if matches(row,params)])
                elif path.endswith('/hof_standalone_agreements'):row=self.record
                elif path.endswith('/hof_agent_profile_aliases'):
                    row=self.alias
                    return httpx.Response(200,json=[deepcopy(row)] if row and (self.alias_wrong_row or matches(row,params)) else [])
                elif path.endswith('/hof_agent_documents'):
                    row=self.iabs
                    return httpx.Response(200,json=[deepcopy(row)] if row and (self.iabs_wrong_row or matches(row,params)) else [])
                elif path.endswith('/hof_agent_profiles'):
                    profile=self.profile if params.get('user_id')=='eq.'+USER['id'] else self.shared_profile if params.get('user_id')=='eq.'+SHARED_PROFILE_ID else None
                    return httpx.Response(200,json=[deepcopy(profile)] if profile else [])
                elif path.endswith('/hof_profiles'):return httpx.Response(200,json=[{'brokerage_id':self.office['id']}] if self.office and params.get('id')=='eq.'+USER['id'] else [])
                elif path.endswith('/hof_brokerage_members'):return httpx.Response(200,json=[{'id':'active-member'}] if self.office else [])
                elif path.endswith('/hof_brokerages'):row=self.office
                elif path.endswith('/hof_seller_disclosure_drafts'):row=self.disclosure
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
                if self.bad_completion_controls:self.provider.pop('checkbox_groups',None)
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
    def test_private_api_bundle_keeps_the_reviewed_lead_source_and_fonts(self):
        root=Path(__file__).resolve().parents[1]
        config=json.loads((root/'vercel.json').read_text())
        included=config['functions']['api/admin-dashboard.py']['includeFiles']
        self.assertEqual(included,'{lead_based_paint_56-0.pdf,lib/fonts/**}')
        from hashlib import sha256
        from lib.listing_lead_disclosure import SOURCE_SHA256
        self.assertEqual(sha256((root/'lead_based_paint_56-0.pdf').read_bytes()).hexdigest(),SOURCE_SHA256)

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

    def test_independent_office_context_has_no_seat_requirement_or_source_host_data(self):
        status,result=self.get('/api/admin-dashboard?scope=txr1101_context')
        self.assertEqual(status,200,result)
        self.assertEqual(result['brokerage']['name'],'Independent QA Realty')
        self.assertEqual(result['noticeContacts'],dict.fromkeys(['address','city_state_zip','phone','email','email_2'],''))
        self.assertNotIn('profile',result);self.assertNotIn('brokerage_id',result)
        self.assertFalse(any('hof_brokerage_members' in r.url.path or 'hof_brokerage_form_sources' in r.url.path for r in self.store.requests))

    def test_linked_office_context_supplies_only_the_current_agents_own_saved_business_defaults(self):
        self.store.office={'id':'active-office','name':'OnDemand Realty','license_number':'',
            'office_address':'10 Fictional Plaza','office_city':'Dallas','office_state':'TX','office_zip':'75201',
            'contact_phone':'214-555-0100','contact_email':'notices@example.test','is_active':True,
            'billing_secret':'must not escape'}
        status,result=self.get('/api/admin-dashboard?scope=txr1101_context')
        self.assertEqual(status,200,result)
        self.assertEqual(result['brokerage'],{'name':'OnDemand Realty','license_number':'9010832'})
        self.assertEqual(result['noticeContacts']['city_state_zip'],'Dallas, TX 75201')
        self.assertEqual(result['noticeContacts']['email'],'notices@example.test')
        self.assertNotIn('billing_secret',json.dumps(result))
        status,other=self.get('/api/admin-dashboard?scope=txr1101_context',token='other-token')
        self.assertEqual(status,200,other);self.assertEqual(other['brokerage']['name'],'')
        self.assertEqual(other['noticeContacts']['address'],'')
        self.assertEqual(self.get('/api/admin-dashboard?scope=txr1101_context',token='bad')[0],401)

    def test_listing_disclosure_choices_exclude_existing_purchase_and_listing_requests(self):
        from tests.test_listing_seller_disclosure import disclosure
        for binding,count in (({},1),({'signature_offer_id':'purchase-request'},0),
                              ({'signature_packet_id':'listing-request'},0)):
            with self.subTest(binding=binding):
                self.store.disclosure=disclosure(agent_user_id=USER['id'],seller_review_attested=True,**binding)
                status,result=self.get('/api/admin-dashboard?scope=txr1101_context')
                self.assertEqual(status,200,result)
                self.assertEqual(len(result['sellerDisclosures']),count)
                request=next(r for r in reversed(self.store.requests) if r.url.path.endswith('/hof_seller_disclosure_drafts'))
                self.assertEqual(request.url.params['signature_packet_id'],'is.null')
                self.assertEqual(request.url.params['signature_offer_id'],'is.null')

    def test_notice_snapshot_is_saved_and_reopened_but_never_changes_the_signing_recipient(self):
        contacts={'address':'42 Fictional Road','city_state_zip':'Plano, TX 75024',
                  'phone':'214-555-0123','email':'notices@example.test','email_2':''}
        self.create(broker_notice_contacts=contacts)
        status,result=self.get('/api/admin-dashboard?scope=txr1101_draft&agreement_id='+AGREEMENT_ID)
        self.assertEqual(status,200,result);self.assertEqual(result['agreement']['agreement_data']['broker_notice_contacts'],contacts)
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        self.assertNotIn('notices@example.test',[r['email'] for r in self.store.provider['recipients']])
        args=self.render.call_args.args
        self.assertEqual(args[2]['address'],'42 Fictional Road')
        self.assertEqual(args[2]['name'],'Independent QA Realty')
        self.assertEqual(args[3]['agent_name'],'QA Agent')

    def test_listing_uses_approved_shared_profile_without_transferring_actor_ownership(self):
        self.store.alias={'login_user_id':USER['id'],'canonical_user_id':SHARED_PROFILE_ID}
        self.store.shared_profile={**self.store.profile,'agent_name':'Shared QA Agent',
            'brokerage_name':'Shared QA Realty','license_number':'000002'}
        body={**payload(),'canonical_user_id':'untrusted-client-selector'}
        status,result=self.post(body);self.assertEqual(status,201,result)
        self.assertEqual(self.store.record['agent_user_id'],USER['id'])
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        self.assertEqual(self.render.call_args.args[3]['agent_name'],'Shared QA Agent')
        self.assertEqual(self.render.call_args.args[2]['name'],'Shared QA Realty')
        account_reads=[r for r in self.store.requests if r.url.path.endswith('/hof_profiles')]
        self.assertTrue(account_reads)
        self.assertTrue(all(r.url.params.get('id')=='eq.'+USER['id'] for r in account_reads))
        status,other=self.get('/api/admin-dashboard?scope=txr1101_context',token='other-token')
        self.assertEqual(status,200,other);self.assertEqual(other['brokerage']['name'],'')

    def test_shared_profile_never_supplies_the_canonical_owners_organization_membership(self):
        self.store.alias={'login_user_id':USER['id'],'canonical_user_id':SHARED_PROFILE_ID}
        self.store.shared_profile={**self.store.profile,'brokerage_name':'Shared QA Realty'}
        self.store.office={'id':'actor-office','name':'Actor QA Realty','is_active':True}
        status,result=self.get('/api/admin-dashboard?scope=txr1101_context')
        self.assertEqual(status,200,result);self.assertEqual(result['brokerage']['name'],'Actor QA Realty')
        memberships=[r for r in self.store.requests if r.url.path.endswith('/hof_brokerage_members')]
        self.assertTrue(memberships)
        self.assertTrue(all(r.url.params.get('user_id')=='eq.'+USER['id'] for r in memberships))

    def test_bad_alias_readback_fails_closed_and_older_form_context_is_unchanged(self):
        self.store.alias={'login_user_id':USER['id'],'canonical_user_id':'malformed'}
        with self.assertRaises(PermissionError):
            asyncio.run(api._representation_professional_context(USER,include_listing_contacts=True))
        self.store.alias={'login_user_id':SHARED_PROFILE_ID,'canonical_user_id':SHARED_PROFILE_ID}
        self.store.alias_wrong_row=True
        with self.assertRaises(PermissionError):
            asyncio.run(api._representation_professional_context(USER,include_listing_contacts=True))
        self.store.requests=[]
        legacy=asyncio.run(api._representation_professional_context(USER))
        self.assertEqual(legacy['profile'],self.store.profile)
        self.assertFalse(any('hof_agent_profile_aliases' in r.url.path for r in self.store.requests))

    def add_iabs(self):
        self.store.iabs={'user_id':USER['id'],'document_type':'iabs','storage_bucket':'agent-documents',
                         'storage_path':USER['id']+'/iabs.pdf','mime_type':'application/pdf'}
        stream=BytesIO();canvas=Canvas(stream,pagesize=(612,792))
        canvas.drawString(40,740,'Fictional saved IABS for packet transport QA');canvas.showPage();canvas.save()
        self.store.iabs_bytes=stream.getvalue()

    def test_reviewed_disclosure_and_water_use_one_actual_send_with_a_bound_journal(self):
        from tests.test_listing_seller_disclosure import disclosure
        from tests.test_listing_packet import pdf
        from unittest.mock import AsyncMock
        self.store.disclosure=disclosure(True,agent_user_id=USER['id'])
        self.create(addenda=['B','P'],disclosure_draft_id=self.store.disclosure['id'])
        with patch.object(api,'_seller_reviews_complete_for_draft',AsyncMock(return_value=True)), \
             patch.object(api,'_render_seller_disclosure_draft_preview',AsyncMock(return_value=pdf('Fictional disclosure and water',6))):
            summary=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))['packet']
            self.assertEqual(summary['pageCount'],16);self.assertEqual(summary['pending'],[])
            body=self.send_body()
            status,result=self.post(body);self.assertEqual(status,200,result)
            status,retry=self.post(body);self.assertEqual(status,200,retry)
        self.assertEqual(self.store.provider_creates,1);self.assertEqual(self.store.provider_sends,1)
        self.assertEqual(len(self.store.provider['files']),1);self.assertEqual(len(self.store.provider['fields']),1)
        binding=self.store.record['agreement_data']['_hof_signature_delivery']['seller_disclosure']
        self.assertEqual(binding['id'],self.store.disclosure['id'])
        self.assertEqual(binding['revision'],self.store.disclosure['review_content_revision'])
        self.assertEqual({f['recipient_id'] for f in self.store.provider['fields'][0]}, {'1','2','associate'})

    def test_unfinished_selected_disclosure_does_not_stop_the_rest_of_the_package(self):
        from tests.test_listing_seller_disclosure import disclosure
        from tests.test_listing_packet import pdf
        from unittest.mock import AsyncMock
        self.store.disclosure=disclosure(agent_user_id=USER['id'])
        self.create(addenda=['B'],disclosure_draft_id=self.store.disclosure['id'])
        review=AsyncMock(return_value=True)
        with patch.object(api,'_seller_reviews_complete_for_draft',review), \
             patch.object(api,'_render_seller_disclosure_draft_preview',AsyncMock(return_value=pdf('Fictional disclosure',4))):
            body=self.send_body();review.return_value=False
            status,result=self.post(body);self.assertEqual(status,400,result)
            self.assertEqual(self.store.provider_creates,0)
            summary=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))['packet']
            self.assertEqual(summary['pageCount'],10)
            self.assertTrue(any('not confirmed' in p for p in summary['pending']))
            status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        self.assertEqual(self.store.provider_sends,1)
        self.assertNotIn('seller_disclosure',self.store.record['agreement_data']['_hof_signature_delivery'])

    def test_selected_saved_iabs_is_in_the_actual_single_file_without_new_signers_or_initials(self):
        from pypdf import PdfReader
        self.add_iabs();self.create()
        summary=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))['packet']
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        payload=self.store.provider
        self.assertEqual(len(payload['files']),1);self.assertEqual(len(payload['fields']),1)
        merged=base64.b64decode(payload['files'][0]['file_base64'])
        reader=PdfReader(BytesIO(merged));self.assertEqual(len(reader.pages),11)
        self.assertIn('Fictional saved IABS',reader.pages[10].extract_text())
        self.assertLessEqual(max(field['page'] for field in payload['fields'][0]),10)
        self.assertFalse(payload['apply_signing_order'])
        self.assertEqual({r['id'] for r in payload['recipients']},{'1','2','associate'})
        self.assertEqual(summary['included'],['Sale listing agreement','Information About Brokerage Services'])
        self.assertEqual(summary['pending'],['Seller’s Disclosure Notice'])
        self.assertEqual(summary['pageCount'],11)
        self.assertNotIn('storage_path',json.dumps(summary));self.assertNotIn('content_fingerprint',json.dumps(summary))

    def test_missing_disclosure_or_iabs_does_not_stop_listing_signing_and_manifest_is_truthful(self):
        self.create();context={}
        asyncio.run(api._render_representation_draft_preview(USER,AGREEMENT_ID,fingerprint_context=context))
        self.assertEqual([row['code'] for row in context['listing_packet']['included']],['TXR-1101'])
        self.assertEqual([row['code'] for row in context['listing_packet']['pending']],['A','B'])
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)

    def test_unselected_iabs_is_not_read_or_added(self):
        self.add_iabs();self.create(addenda=[])
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        self.assertFalse(any(r.url.path.endswith('/hof_agent_documents') for r in self.store.requests))
        self.assertFalse(any('/agent-documents/' in r.url.path for r in self.store.requests))

    def test_iabs_lookup_cannot_follow_source_host_shared_profile_or_wrong_storage_path(self):
        self.add_iabs();self.create()
        for key,value in (('user_id',SHARED_PROFILE_ID),('storage_path',SHARED_PROFILE_ID+'/iabs.pdf'),
                          ('storage_bucket','brokerage-form-sources'),('document_type','private-other')):
            with self.subTest(key=key):
                self.add_iabs();self.store.iabs[key]=value;self.store.iabs_wrong_row=True
                with self.assertRaises(PermissionError):
                    asyncio.run(api._render_representation_draft_preview(USER,AGREEMENT_ID))
        self.assertFalse(any('/agent-documents/' in r.url.path for r in self.store.requests))

    def test_unavailable_known_iabs_never_produces_an_invitation_with_an_unconfirmed_attachment(self):
        self.add_iabs();self.create();body=self.send_body();self.store.iabs_bytes=None;self.store.iabs_error=503
        status,result=self.post(body)
        self.assertGreaterEqual(status,400,result)
        self.assertEqual(self.store.provider_creates,0);self.assertEqual(self.store.provider_sends,0)

    def test_missing_iabs_object_is_pending_and_does_not_stop_a_reviewed_listing(self):
        self.add_iabs();self.create();self.store.iabs_bytes=None
        summary=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(summary['packet']['included'],['Sale listing agreement'])
        self.assertIn('Information About Brokerage Services',summary['packet']['pending'])
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)

    def test_changed_packet_review_is_required_before_any_new_invitation(self):
        self.add_iabs();self.create();body=self.send_body()
        self.store.iabs_bytes=None
        status,result=self.post(body);self.assertEqual(status,400,result)
        self.assertEqual(self.store.provider_creates,0);self.assertEqual(self.store.provider_sends,0)
        # A fresh review shows the now-pending IABS and can continue normally.
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)

    def test_missing_tampered_or_stale_packet_confirmation_never_creates_a_request(self):
        self.create();body=self.send_body()
        for value in (None,'','client-chosen-fingerprint'):
            status,result=self.post({**body,'confirmedPacketFingerprint':value})
            self.assertEqual(status,400,result)
        self.store.profile['brokerage_license']='9000002'
        self.assertEqual(self.post(body)[0],400)
        self.assertEqual(self.store.provider_creates,0);self.assertEqual(self.store.provider_sends,0)
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)

    def test_pre1978_listing_packet_contains_real_lead_source_and_seller_completion_controls(self):
        from pypdf import PdfReader
        self.create(built_before_1978='yes',addenda=[])
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertIn('Lead-based paint disclosure',preview['packet']['included'])
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        payload=self.store.provider;reader=PdfReader(BytesIO(base64.b64decode(payload['files'][0]['file_base64'])))
        self.assertIn('LEAD WARNING STATEMENT',reader.pages[10].extract_text())
        self.assertIn('Lead Disclosure Details',reader.pages[11].extract_text())
        self.assertEqual(len(payload['checkbox_groups']),2);self.assertEqual(len(payload['conditional_rules']),2)
        fields={field['api_id']:field for field in payload['fields'][0]}
        self.assertTrue(all(set(group['checkbox_ids'])<=fields.keys() for group in payload['checkbox_groups']))
        self.assertTrue(all(group['recipient_id']=='1' and group['exact_value']==1 for group in payload['checkbox_groups']))
        self.assertFalse(any('buyer' in key for key in fields if key.startswith('listing_C_')))
        self.assertFalse(payload['apply_signing_order'])

    def test_dropped_lead_choice_requirements_never_send_an_incomplete_provider_draft(self):
        self.create(built_before_1978='yes',addenda=[]);body=self.send_body()
        self.store.bad_completion_controls=True
        status,result=self.post(body);self.assertEqual(status,400,result)
        self.assertEqual(self.store.provider_creates,1);self.assertEqual(self.store.provider_sends,0)

    def test_iabs_packet_retry_reuses_one_provider_record_and_changed_iabs_cannot_replace_it(self):
        self.add_iabs();self.create();body=self.send_body();self.store.fail_inspect_once=True
        self.assertEqual(self.post(body)[0],409)
        self.assertEqual(self.post(body)[0],200)
        self.assertEqual(self.store.provider_creates,1);self.assertEqual(self.store.provider_sends,1)

    def test_changed_iabs_during_a_pending_request_cannot_cause_new_or_changed_invitations(self):
        self.add_iabs();self.create();body=self.send_body();self.store.fail_inspect_once=True
        self.assertEqual(self.post(body)[0],409)
        # A new upload changes the source hash, even if the page count is equal.
        self.store.iabs_bytes=self.rendered
        self.assertEqual(self.post(body)[0],400)
        self.assertEqual(self.store.provider_creates,1);self.assertEqual(self.store.provider_sends,0)

    def send_body(self):
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        contacts=[{key:r[key] for key in ('id','name','email')} for r in preview['recipients']]
        return {'action':'send_txr_agreement_for_signature','agreementId':AGREEMENT_ID,
                'confirmedRecipients':contacts,'confirmedPacketFingerprint':preview.get('packetFingerprint')}

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
        self.assertEqual(self.post(body)[0],200)  # Confirm the tracked record; never send a duplicate.
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

    def test_sent_request_retry_confirms_existing_document_without_new_provider_writes(self):
        self.create();body=self.send_body()
        status,result=self.post(body);self.assertEqual(status,200,result)
        self.assertFalse(result['signwell']['recovered'])
        for saved_status, provider_status in (('sent','sent'),('signed','completed'),('void','declined')):
            with self.subTest(status=saved_status):
                self.store.record['status']=saved_status;self.store.provider['status']=provider_status
                before=len(self.store.requests)
                status,result=self.post(body);self.assertEqual(status,200,result)
                self.assertTrue(result['signwell']['recovered']);self.assertEqual(result['signwell']['documentId'],'qa-provider')
                self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))
                self.assertFalse(any(r.url.host=='www.signwell.com' and r.method=='POST'
                                     for r in self.store.requests[before:]))

    def test_sent_record_without_exact_durable_identity_cannot_create_or_send(self):
        from lib.signwell_delivery import JOURNAL_KEY
        self.create();body=self.send_body()
        for document_id,journal in ((None,None),('existing',None),
            ('existing',{'version':1,'document_id':'other','fingerprint':'a'*64}),
            ('existing',{'version':1,'document_id':'existing','fingerprint':'not-a-digest'})):
            with self.subTest(document_id=document_id,journal=journal):
                self.store.record.update(status='sent',signwell_document_id=document_id)
                self.store.record['agreement_data'][JOURNAL_KEY]=journal
                status,result=self.post(body);self.assertEqual(status,403,result)
                self.assertEqual((self.store.provider_creates,self.store.provider_sends),(0,0))

    def test_changed_or_other_owner_sent_request_never_recreates_delivery(self):
        self.create();body=self.send_body()
        status,result=self.post(body);self.assertEqual(status,200,result)
        self.store.record['agent_user_id']='different-owner'
        status,result=self.post(body);self.assertEqual(status,403,result)
        self.store.record['agent_user_id']=USER['id']
        self.store.record['agreement_data']['listing_price']='900000'
        status,result=self.post(body);self.assertEqual(status,400,result)
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
    def test_real_source_saved_iabs_and_corrected_lead_details_form_one_retry_safe_packet(self):
        from pypdf import PdfReader
        self.store.storage_bytes=Path(os.environ['HOF_TXR1101_SOURCE']).read_bytes()
        self.render.side_effect=ACTUAL_RENDER
        self.add_iabs();self.create(built_before_1978='yes')
        reviewed=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(reviewed['packet']['included'],[
            'Sale listing agreement','Information About Brokerage Services','Lead-based paint disclosure'])
        self.assertEqual(reviewed['packet']['pending'],['Seller’s Disclosure Notice'])
        self.assertEqual(reviewed['packet']['pageCount'],13)
        body=self.send_body()
        status,result=self.post(body);self.assertEqual(status,200,result)
        packet=self.store.provider
        self.assertEqual(len(packet['files']),1)
        reader=PdfReader(BytesIO(base64.b64decode(packet['files'][0]['file_base64'])))
        self.assertEqual(len(reader.pages),13)
        self.assertIn('Fictional saved IABS',reader.pages[10].extract_text())
        self.assertIn('LEAD WARNING STATEMENT',reader.pages[11].extract_text())
        self.assertIn('Use one paragraph',reader.pages[12].extract_text())
        self.assertEqual({r['id'] for r in packet['recipients']},{'1','2','associate'})
        self.assertFalse(packet['apply_signing_order'])
        fields={f['api_id']:f for f in packet['fields'][0]}
        explanations=[f for f in fields.values() if f['type']=='text']
        self.assertEqual(len(explanations),2)
        self.assertEqual({f['page'] for f in explanations},{13})
        self.assertEqual({f['height'] for f in explanations},{18})
        self.assertEqual({f['recipient_id'] for f in explanations},{'1'})
        self.assertFalse(any(f['page']==11 for f in fields.values()))
        self.assertEqual(len(packet['checkbox_groups']),2)
        self.assertEqual(len(packet['conditional_rules']),2)
        self.assertTrue(all(set(g['checkbox_ids'])<=fields.keys() for g in packet['checkbox_groups']))
        self.assertTrue(all(r['target_id'] in fields and set(r['action_field_ids'])<=fields.keys()
                            for r in packet['conditional_rules']))
        # A lost final response/retry cannot recreate the combined packet or
        # send an extra invitation. All calls use the isolated fake transport.
        status,result=self.post(body);self.assertEqual(status,200,result)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

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
