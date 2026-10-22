"""Lease-listing API boundaries; all HTTP is isolated, no email or cloud writes."""
import asyncio
import base64
from copy import deepcopy
import hashlib
from contextlib import ExitStack
from io import BytesIO
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from tests import test_txr1101_api as sale_api_tests
from tests.test_txr1101_api import Store, USER, SOURCE_ID, AGREEMENT_ID, REAL_CLIENT, SHARED_PROFILE_ID
from tests.test_txr_1102 import sample, with_preferences
from tests.test_standalone_recipient_preview import MODULE as api
from lib.txr_1102 import render_txr_1102 as ACTUAL_RENDER, SOURCE_SHA256, REVISION


def payload(**changes):
    answers = sample(**changes)
    return {'action':'create_txr_1102_draft','formCode':'TXR-1102','formSourceId':SOURCE_ID,
            'clientNames':answers.pop('client_names'),'agreementData':answers}


class LeaseListingApiTests(unittest.TestCase):
    # Reuse only the synthetic HTTP request drivers, not the sale-only tests.
    post = sale_api_tests.Txr1101ApiTests.post
    get = sale_api_tests.Txr1101ApiTests.get

    @classmethod
    def setUpClass(cls):
        stream=BytesIO(); canvas=Canvas(stream,pagesize=(612,792))
        for page in range(11):
            canvas.drawString(36,740,'Fictional lease-listing API fixture '+str(page+1)); canvas.showPage()
        canvas.save(); cls.rendered=stream.getvalue()

    def setUp(self):
        self.store=Store(); self.stack=ExitStack(); self.addCleanup(self.stack.close)
        self.store.source.update(form_code='TXR-1102',source_revision='01-05-26',storage_path='source-host/1102.pdf')
        for key,value in {'SUPABASE_URL':'https://fixture.supabase.test','SUPABASE_SERVICE_ROLE_KEY':'qa-only',
                          'TXR_SIGNING_ENABLED':True,'SIGNWELL_ENABLED':True,'SIGNWELL_API_KEY':'qa-only',
                          'SIGNWELL_TEST_MODE':True}.items():
            self.stack.enter_context(patch.object(api,key,value))
        transport=httpx.MockTransport(self.store.handle)
        self.stack.enter_context(patch.object(api.httpx,'AsyncClient',
            side_effect=lambda *a,**kw:REAL_CLIENT(*a,transport=transport,**kw)))
        self.render=self.stack.enter_context(patch('lib.txr_1102.render_txr_1102',return_value=self.rendered))

    def create(self,**changes):
        status,result=self.post(payload(**changes)); self.assertEqual(status,201,result)
        return result['agreement']

    def update_body(self,**changes):
        return {**payload(**changes),'action':'update_txr_1102_draft','agreementId':AGREEMENT_ID,
                'updatedAt':self.store.record['updated_at']}

    def send_body(self):
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        return {'action':'send_txr_agreement_for_signature','agreementId':AGREEMENT_ID,
                'confirmedRecipients':preview['recipients'],'confirmedPacketFingerprint':preview['packetFingerprint']}

    def test_save_uses_actual_login_owner_and_lease_revision_without_seat_lookup(self):
        row=self.create()
        self.assertEqual(row['agent_user_id'],USER['id']); self.assertEqual(row['form_code'],'TXR-1102')
        self.assertEqual(row['agreement_data']['signing_map_revision'],api.TXR_SIGNING_MAP_REVISIONS['TXR-1102'])
        self.assertEqual(api.TXR_RENDER_REVISIONS['TXR-1102'],REVISION)
        self.assertFalse(any('/hof_brokerage_members' in r.url.path for r in self.store.requests))

    def test_create_and_update_cannot_cross_form_or_trust_browser_parties(self):
        for change in ({'formCode':'TXR-1101'},{'formSourceId':'bad'},
                       {'agreementData':{**payload()['agreementData'],'_for_signing':True}},
                       {'agreementData':{**payload()['agreementData'],'client_names':['injected']}},
                       {'agreementData':{**payload()['agreementData'],'foreign_person':'no'}}):
            self.assertEqual(self.post({**payload(),**change})[0],400)
        self.create(); self.store.record['form_code']='TXR-1101'
        self.assertEqual(self.post(self.update_body())[0],403)

    def test_source_approval_revision_and_form_are_checked(self):
        for key,value in [('form_code','TXR-1101'),('status','pending'),('authorization_attested',False)]:
            old=self.store.source[key]; self.store.source[key]=value
            self.assertEqual(self.post(payload())[0],400); self.store.source[key]=old
        self.create(); self.store.source['source_revision']='changed'
        with self.assertRaisesRegex(ValueError,'revision'):
            asyncio.run(api._render_owned_representation_agreement(USER,self.store.record))
        self.render.assert_not_called()

    def test_save_success_must_return_matching_owner_and_record(self):
        for setting in ('empty_create','wrong_owner_create'):
            setattr(self.store,setting,True); status,result=self.post(payload())
            self.assertEqual(status,409,result); self.assertTrue(result['refreshRequired'])
            setattr(self.store,setting,False)

    def test_long_lease_answers_use_only_the_bounded_listing_request_allowance(self):
        import json
        body=payload(special_provisions='QA note. '*400,health_safety_conditions='QA condition. '*200,
                     non_real_estate_items='QA item. '*200,exclusions='QA exclusion. '*140,
                     financial_exceptions='QA exception. '*140)
        self.assertGreater(len(json.dumps(body).encode()),api.MAX_BODY_BYTES)
        self.assertEqual(self.post(body)[0],201)
        # The larger allowance cannot be reused for unrelated admin actions.
        self.assertEqual(self.post({**body,'action':'unrelated_action'})[0],400)
        self.assertEqual(self.post({**body,'padding':'x'*api.MAX_LISTING_BODY_BYTES})[0],400)

    def test_reopen_strips_only_named_server_bookkeeping_and_is_owner_form_scoped(self):
        self.create(); self.store.record['agreement_data'].update(client_emails=['private@example.test'],broker_signer={'name':'QA'})
        url='/api/admin-dashboard?scope=txr1102_draft&agreement_id='+AGREEMENT_ID
        status,result=self.get(url); self.assertEqual(status,200,result)
        self.assertEqual(result['agreement']['agreement_data']['lease_min_months'],'12')
        self.assertNotIn('client_emails',result['agreement']['agreement_data'])
        self.assertNotIn('broker_signer',result['agreement']['agreement_data'])
        self.assertEqual(self.get(url,token='other-token')[0],404)
        self.assertEqual(self.get(url.replace('txr1102','txr1101'))[0],404)
        self.store.record['signwell_document_id']='tracked'; self.assertEqual(self.get(url)[0],404)

    def test_update_is_same_record_version_checked_and_disallows_tracked_records(self):
        self.create(); body=self.update_body(listing_price='2750')
        self.assertEqual(self.post(body,token='other-token')[0],403)
        self.assertEqual(self.post({**body,'updatedAt':'stale'})[0],400)
        status,result=self.post(body); self.assertEqual(status,200,result)
        self.assertEqual(result['agreement']['id'],AGREEMENT_ID)
        self.assertEqual(result['agreement']['agreement_data']['listing_price'],'2750')
        self.store.record['signwell_document_id']='tracked'
        self.assertEqual(self.post(self.update_body())[0],403)
        self.assertEqual(sum(r.method=='POST' and r.url.path.endswith('/hof_standalone_agreements') for r in self.store.requests),1)

    def test_update_race_or_empty_success_does_not_report_saved(self):
        for setting in ('race_update','empty_update'):
            self.create(); body=self.update_body(listing_price='2750'); setattr(self.store,setting,True)
            status,result=self.post(body); self.assertEqual(status,409,result)
            self.assertEqual(self.store.record['agreement_data']['listing_price'],'2500.00')
            setattr(self.store,setting,False)
        self.create(); self.store.normalize_timestamp=True
        self.assertEqual(self.post(self.update_body())[0],200)

    def test_preview_uses_saved_snapshot_notice_contacts_and_no_sale_renderer(self):
        self.create(broker_notice_contacts={'email':'saved-office@example.test'})
        self.store.record['agreement_data']['client_emails']=['bookkeeping@example.test']
        with patch('lib.txr_1101.render_txr_1101',side_effect=AssertionError('Wrong legal form renderer')):
            context={}; pdf=asyncio.run(api._render_owned_representation_agreement(USER,self.store.record,fingerprint_context=context))
        self.assertEqual(pdf,self.rendered)
        source,data,broker,profile=self.render.call_args.args
        self.assertEqual(data['client_names'],sample()['client_names'])
        self.assertNotIn('client_emails',data); self.assertNotIn('compensation',data)
        self.assertEqual(broker['email'],'saved-office@example.test'); self.assertEqual(context['render_revision'],REVISION)
        self.assertEqual(context['listing_packet']['included'][0]['code'],'TXR-1102')
        self.assertNotIn('seller_disclosure',context['listing_packet'])

    def test_recipient_preview_uses_landlords_saved_emails_and_associate(self):
        self.create(); result=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual([r['label'] for r in result['recipients']],['Landlord 1','Landlord 2','Associate signer (your account)'])
        self.assertEqual([r['email'] for r in result['recipients']],['landlord-one@example.test','landlord-two@example.test',USER['email']])
        self.assertEqual(self.store.provider_creates,0)

    def test_shared_profile_is_only_a_default_not_a_document_ownership_grant(self):
        self.store.alias={'login_user_id':USER['id'],'canonical_user_id':SHARED_PROFILE_ID}
        self.store.shared_profile={**self.store.profile,'agent_name':'QA Shared Agent'}
        status,result=self.get('/api/admin-dashboard?scope=txr1102_context')
        self.assertEqual(status,200,result)
        self.assertEqual(result['brokerage']['name'],'Independent QA Realty')
        self.create()
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(preview['recipients'][-1]['name'],'QA Shared Agent')
        self.assertEqual(preview['recipients'][-1]['email'],USER['email'])
        self.assertEqual(self.store.record['agent_user_id'],USER['id'])
        self.store.record['agent_user_id']=SHARED_PROFILE_ID
        with self.assertRaises(PermissionError):
            asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))

    def test_preview_and_signing_require_authentication_and_own_record(self):
        self.assertEqual(self.post(payload(),token='bad')[0],401)
        self.create()
        with self.assertRaises(PermissionError):
            asyncio.run(api._render_representation_draft_preview({**USER,'id':'other-owner'},AGREEMENT_ID))
        body=self.send_body(); self.assertEqual(self.post(body,token='other-token')[0],403)
        self.assertEqual(self.post(body,token='bad')[0],401)
        self.assertEqual(self.store.provider_creates,0)

    def test_simultaneous_send_and_retry_use_one_durable_provider_record(self):
        self.create(); body=self.send_body()
        status,result=self.post(body); self.assertEqual(status,200,result)
        status,result=self.post(body); self.assertEqual(status,200,result)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))
        self.assertFalse(self.store.provider['apply_signing_order'])
        self.assertEqual({f['recipient_id'] for f in self.store.provider['fields'][0]},{'1','2','associate'})
        self.assertEqual(self.store.provider['metadata']['render_revision'],REVISION)
        self.assertEqual(len(self.store.provider['fields'][0]),39)

    def test_failed_inspection_retries_same_document_without_duplicate_invites(self):
        self.create(); body=self.send_body(); self.store.fail_inspect_once=True
        self.assertEqual(self.post(body)[0],409)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,0))
        self.assertEqual(self.post(self.send_body())[0],200)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

    def test_confirmed_contacts_and_stale_signature_maps_cannot_be_sent(self):
        self.create(); body=self.send_body(); body['confirmedRecipients'][0]['email']='injected@example.test'
        self.assertEqual(self.post(body)[0],400); self.assertEqual(self.store.provider_creates,0)
        self.store.record['agreement_data']['signing_map_revision']='old'
        self.assertEqual(self.post(self.send_body())[0],400); self.assertEqual(self.store.provider_creates,0)

    def test_single_landlord_broker_plan_does_not_add_agent_or_second_landlord_fields(self):
        self.create(client_names=['QA Landlord One'],client_email_2='',signer_plan='clients_and_broker')
        body=self.send_body(); broker={'name':'QA Broker','email':'broker@example.test'}
        body['brokerSigner']=broker; body['confirmedRecipients'][-1]={'id':'broker',**broker}
        status,result=self.post(body); self.assertEqual(status,200,result)
        self.assertEqual([r['id'] for r in self.store.provider['recipients']],['1','broker'])
        self.assertEqual({f['recipient_id'] for f in self.store.provider['fields'][0]},{'1','broker'})

    def add_iabs(self):
        sale_api_tests.Txr1101ApiTests.add_iabs(self)

    def add_rental_sources(self):
        """Synthetic pinned one-page sources; actual-source coupling is separate."""
        from lib import lease_disclosures as rental
        from tests.test_listing_packet import pdf
        specs=deepcopy(rental.SOURCES)
        for index,code in enumerate(('TXR-2008','TXR-2015'),1):
            raw=pdf('Fictional '+code+' API source')
            specs[code]['sha256']=hashlib.sha256(raw).hexdigest()
            path='component-source-host/'+code+'.pdf'
            self.store.related_sources.append({'id':f'11111111-1111-4111-8111-{index:012d}',
                'brokerage_id':'component-source-host','form_code':code,'source_revision':specs[code]['revision'],
                'status':'approved','authorization_attested':True,'source_sha256':specs[code]['sha256'],
                'storage_bucket':'brokerage-form-sources','storage_path':path})
            self.store.related_files['/storage/v1/object/brokerage-form-sources/'+path]=(200,raw)
        self.stack.enter_context(patch.dict(rental.SOURCES,specs))
        # The synthetic page has no supplier imprint. All remaining answer,
        # rendering, completion-control, merging and delivery code is real.
        self.stack.enter_context(patch('lib.lease_disclosures._remove_member_footer'))

    def test_rental_sources_are_loaded_privately_and_delivered_in_one_bound_packet(self):
        self.add_rental_sources();self.create(addenda=['B','C'])
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(preview['packet']['pageCount'],14)
        self.assertEqual(preview['packet']['included'],['Lease listing agreement','Rental flood disclosure','Lead-based paint disclosure for a lease'])
        self.assertEqual(preview['packet']['pending'],[])
        self.assertTrue(any('Tenant receipt' in row for row in preview['packet']['followUp']))
        self.assertTrue(any('lead pamphlet' in row for row in preview['packet']['followUp']))
        self.assertNotIn('storage_path',str(preview));self.assertNotIn('component-source-host',str(preview))
        body=self.send_body();status,result=self.post(body);self.assertEqual(status,200,result)
        request=self.store.provider
        reader=PdfReader(BytesIO(base64.b64decode(request['files'][0]['file_base64'])))
        self.assertEqual(len(reader.pages),14);self.assertEqual(len(request['files']),1)
        self.assertEqual({r['id'] for r in request['recipients']},{'1','2','associate'})
        self.assertNotIn('signing_order',request);self.assertEqual(len(request['checkbox_groups']),4)
        self.assertEqual(len(request['conditional_rules']),2)
        fields=request['fields'][0];ids={f['api_id'] for f in fields}
        self.assertEqual({f['page'] for f in fields if f['api_id'].startswith('listing_B_')},{12})
        self.assertEqual({f['page'] for f in fields if f['api_id'].startswith('listing_C_')},{13,14})
        self.assertFalse(any('tenant' in f['api_id'] for f in fields))
        for group in request['checkbox_groups']:self.assertTrue(set(group['checkbox_ids'])<=ids)
        self.assertEqual(self.post(body)[0],200)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

    def test_unconfirmed_age_defers_lead_but_does_not_block_the_listing_and_flood(self):
        self.add_rental_sources();self.create(addenda=['B','C'],built_before_1978='unanswered')
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(preview['packet']['pageCount'],12)
        self.assertEqual(preview['packet']['included'],['Lease listing agreement','Rental flood disclosure'])
        self.assertTrue(any('Confirm the home’s age' in row for row in preview['packet']['pending']))
        self.assertFalse(any(r.url.params.get('form_code')=='eq.TXR-2008' for r in self.store.requests))
        self.assertEqual(self.post(self.send_body())[0],200)

    def test_confirmed_newer_home_clears_a_stale_lead_check_without_loading_it(self):
        self.add_rental_sources();self.create(addenda=['B','C'],built_before_1978='no')
        self.assertEqual(self.store.record['agreement_data']['addenda'],['B'])
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(preview['packet']['pending'],[])
        self.assertFalse(any(r.url.params.get('form_code')=='eq.TXR-2008' for r in self.store.requests))

    def test_wrong_source_metadata_or_private_path_is_rejected_before_component_download(self):
        self.add_rental_sources();self.create(addenda=['B'])
        source=self.store.related_sources[1]
        for key,value in [('source_sha256','0'*64),('storage_bucket','public-files'),
                          ('storage_path','component-source-host/../another/private.pdf'),('id','not-an-id')]:
            original=source[key];source[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
            source[key]=original
        self.assertFalse(any('/component-source-host/' in r.url.path for r in self.store.requests))
        self.assertEqual(self.store.provider_creates,0)

    def test_unapproved_or_changed_source_revision_remains_pending_not_falsely_included(self):
        self.add_rental_sources();self.create(addenda=['B'],built_before_1978='no')
        source=self.store.related_sources[1]
        for key,value in [('status','retired'),('authorization_attested',False),('source_revision','changed')]:
            original=source[key];source[key]=value
            preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
            self.assertEqual(preview['packet']['included'],['Lease listing agreement'])
            self.assertTrue(any('Rental flood disclosure' in row for row in preview['packet']['pending']))
            source[key]=original

    def test_missing_storage_is_pending_but_transient_errors_or_changed_bytes_are_visible(self):
        self.add_rental_sources();self.create(addenda=['B'],built_before_1978='no')
        path='/storage/v1/object/brokerage-form-sources/'+self.store.related_sources[1]['storage_path']
        saved=self.store.related_files[path];self.store.related_files[path]=(404,b'')
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(preview['packet']['included'],['Lease listing agreement'])
        self.assertEqual(self.post(self.send_body())[0],200)
        # Separate untracked draft, not a request to send another provider document.
        self.create(addenda=['B'],built_before_1978='no')
        self.store.related_files[path]=(503,b'')
        with self.assertRaises(RuntimeError):asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.store.related_files[path]=(200,saved[1]+b'\naltered')
        with self.assertRaises(ValueError):asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(self.store.provider_creates,1)

    def test_a_newly_available_or_reapproved_component_invalidates_previous_review(self):
        self.create(addenda=['B','C']);old=self.send_body();self.add_rental_sources()
        self.assertEqual(self.post(old)[0],400)
        current=self.send_body();self.store.related_sources[0]['id']='22222222-2222-4222-8222-222222222222'
        self.assertEqual(self.post(current)[0],400)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(0,0))

    def test_component_controls_must_survive_provider_readback_before_any_invitation(self):
        self.add_rental_sources();self.create(addenda=['B','C']);self.store.bad_completion_controls=True
        status,result=self.post(self.send_body());self.assertEqual(status,400,result)
        self.assertEqual(self.store.provider_sends,0)

    @unittest.skipUnless(os.environ.get('HOF_LEASE_DISCLOSURE_SOURCES'),'Exact private component sources are opt-in.')
    def test_actual_component_sources_flow_through_preview_and_same_provider_retry(self):
        from lib.lease_disclosures import SOURCES
        if os.environ.get('HOF_TXR1102_SOURCE'):
            self.store.storage_bytes=Path(os.environ['HOF_TXR1102_SOURCE']).read_bytes()
            self.render.side_effect=ACTUAL_RENDER
        files={'TXR-2008':'TXR-2008-2003-10-14.pdf','TXR-2015':'TXR-2015-2025-09-01.pdf'}
        for index,(code,filename) in enumerate(files.items(),1):
            spec=SOURCES[code];path='component-source-host/'+code+'.pdf'
            self.store.related_sources.append({'id':f'11111111-1111-4111-8111-{index:012d}',
                'brokerage_id':'component-source-host','form_code':code,'source_revision':spec['revision'],'status':'approved',
                'authorization_attested':True,'source_sha256':spec['sha256'],'storage_bucket':'brokerage-form-sources','storage_path':path})
            self.store.related_files['/storage/v1/object/brokerage-form-sources/'+path]=(200,(Path(os.environ['HOF_LEASE_DISCLOSURE_SOURCES'])/filename).read_bytes())
        self.create(addenda=['B','C'],client_names=['QA Sole Landlord'],client_email_2='',signer_plan='clients_and_broker')
        body=self.send_body();broker={'name':'QA Broker','email':'broker@example.test'}
        body['brokerSigner']=broker;body['confirmedRecipients'][-1]={'id':'broker',**broker}
        self.store.fail_inspect_once=True
        status,result=self.post(body);self.assertEqual(status,409,result)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,0))
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))
        self.assertEqual({r['id'] for r in self.store.provider['recipients']},{'1','broker'})
        reader=PdfReader(BytesIO(base64.b64decode(self.store.provider['files'][0]['file_base64'])))
        self.assertIn('ADDENDUM REGARDING',reader.pages[11].extract_text())

    def test_actual_saved_iabs_is_included_once_without_fabricated_disclosures_or_extra_signers(self):
        self.add_iabs();self.create()
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(preview['packet']['pageCount'],12)
        self.assertEqual(preview['packet']['included'],['Lease listing agreement','Information About Brokerage Services'])
        self.assertTrue(any('Rental flood disclosure' in row for row in preview['packet']['pending']))
        self.assertTrue(any('Lead-based paint disclosure for a lease' in row for row in preview['packet']['pending']))
        self.assertFalse(any('Seller’s Disclosure' in row for row in preview['packet']['pending']))
        body=self.send_body();status,result=self.post(body);self.assertEqual(status,200,result)
        request=self.store.provider
        reader=PdfReader(BytesIO(base64.b64decode(request['files'][0]['file_base64'])))
        self.assertEqual(len(reader.pages),12);self.assertIn('Fictional saved IABS',reader.pages[-1].extract_text())
        self.assertEqual(len(request['files']),1);self.assertEqual(len(request['fields']),1)
        self.assertLessEqual(max(f['page'] for f in request['fields'][0]),11)
        self.assertEqual({r['id'] for r in request['recipients']},{'1','2','associate'})
        self.assertEqual(self.post(body)[0],200)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

    def test_missing_saved_iabs_remains_pending_and_does_not_stop_other_documents(self):
        self.add_iabs();self.store.iabs_bytes=None;self.store.iabs_error=404;self.create()
        preview=asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(preview['packet']['pageCount'],11)
        self.assertEqual(preview['packet']['included'],['Lease listing agreement'])
        self.assertIn('Information About Brokerage Services',preview['packet']['pending'])
        self.assertEqual(self.post(self.send_body())[0],200)
        self.assertEqual(self.store.provider_sends,1)

    def test_changed_or_unconfirmed_package_cannot_be_sent_until_actual_contents_are_reviewed(self):
        self.create();body=self.send_body()
        for value in (None,'','browser-chosen-value'):
            status,result=self.post({**body,'confirmedPacketFingerprint':value})
            self.assertEqual(status,400,result)
        self.add_iabs()
        self.assertEqual(self.post(body)[0],400)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(0,0))
        status,result=self.post(self.send_body());self.assertEqual(status,200,result)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

    def test_wrong_account_iabs_row_is_rejected_before_private_storage_download(self):
        self.add_iabs();self.store.iabs['user_id']=SHARED_PROFILE_ID;self.store.iabs['storage_path']=SHARED_PROFILE_ID+'/iabs.pdf'
        self.store.iabs_wrong_row=True;self.create()
        with self.assertRaises(PermissionError):
            asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertFalse(any('/agent-documents/' in r.url.path for r in self.store.requests))
        self.assertEqual(self.store.provider_creates,0)

    def test_temporary_saved_file_error_is_not_misreported_as_a_missing_document(self):
        self.add_iabs();self.store.iabs_bytes=None;self.store.iabs_error=503;self.create()
        with self.assertRaisesRegex(RuntimeError,'IABS PDF could not be loaded'):
            asyncio.run(api._standalone_signing_recipient_preview(USER,AGREEMENT_ID))
        self.assertEqual(self.store.provider_creates,0)

    def test_saved_iabs_content_change_cannot_create_a_second_provider_request(self):
        self.add_iabs();self.create();body=self.send_body()
        self.assertEqual(self.post(body)[0],200)
        self.store.iabs_bytes+=b'\nchanged stored file'
        self.assertEqual(self.post(body)[0],400)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

    @unittest.skipUnless(os.environ.get('HOF_TXR1102_SOURCE'),'Exact private source is opt-in; no provider traffic.')
    def test_actual_private_source_preview_and_delivery_preserve_lease_terms(self):
        source=Path(os.environ['HOF_TXR1102_SOURCE']).read_bytes()
        from hashlib import sha256
        self.assertEqual(sha256(source).hexdigest(),SOURCE_SHA256)
        self.store.storage_bytes=source; self.render.side_effect=ACTUAL_RENDER
        answers=with_preferences(special_provisions='Fictional Unicode résumé — café. '*40)
        self.create(**answers)
        pdf=asyncio.run(api._render_owned_representation_agreement(USER,self.store.record))
        self.assertGreater(len(PdfReader(BytesIO(pdf)).pages),11)
        body=self.send_body()
        status,result=self.post(body); self.assertEqual(status,200,result)
        sent=PdfReader(BytesIO(base64.b64decode(self.store.provider['files'][0]['file_base64'])))
        text='\n'.join(p.extract_text() for p in sent.pages)
        self.assertIn('QA Landlord One',text); self.assertIn('Landlord-approved advertising',text)
        self.assertLessEqual(max(f['page'] for f in self.store.provider['fields'][0]),len(sent.pages))
        self.assertEqual(self.post(body)[0],200)
        self.assertEqual((self.store.provider_creates,self.store.provider_sends),(1,1))

    @unittest.skipUnless(os.environ.get('HOF_TXR1102_SOURCE'),'Exact private source is opt-in; no provider traffic.')
    def test_unreviewed_source_bytes_never_reach_provider_creation(self):
        self.store.storage_bytes=Path(os.environ['HOF_TXR1102_SOURCE']).read_bytes()+b'\nmodified'
        self.render.side_effect=ACTUAL_RENDER; self.create()
        with self.assertRaisesRegex(ValueError,'source'):
            asyncio.run(api._render_representation_draft_preview(USER,AGREEMENT_ID))
        self.assertEqual(self.store.provider_creates,0)


if __name__=='__main__':
    unittest.main()
