"""Lease-listing API boundaries; all HTTP is isolated, no email or cloud writes."""
import asyncio
import base64
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
                'confirmedRecipients':preview['recipients']}

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
        self.assertNotIn('listing_packet',context)

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
