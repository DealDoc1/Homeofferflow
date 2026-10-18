"""Seller link scope, saved facts and signing recipients. No external writes."""
import asyncio
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from lib.seller_questionnaire import parse_answers, required_answers
from tests.test_seller_review_revision_binding import DRAFT, VERSION, OTHER_VERSION, links

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('seller_questionnaire_api', ROOT / 'api/admin-dashboard.py')
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
SESSION = 'fictional-questionnaire-session-000000000000'


def context():
    draft = {**copy.deepcopy(DRAFT), 'property_address':'100 Fictional Lane',
             'response_data':{'notes':'Keep literal Élodie <trim> & café.\nSecond line.'}, 'water_rights_data':{}}
    link = {**links()[0], 'questionnaire_enabled':True, 'expires_at':'2099-01-01T00:00:00Z',
            'seller_email':'qa-one@example.test', 'review_content_revision':OTHER_VERSION}
    return link, draft


class SellerQuestionnaireTests(unittest.TestCase):
    def test_partial_save_and_explicit_unknown_are_not_guessed(self):
        payload={'reviewContentRevision':VERSION,'responseData':{'roof_type':'Unknown','defect_roof':'U'}}
        version, answers, water = parse_answers(payload)
        self.assertEqual(answers, payload['responseData']); self.assertEqual(water,{})
        with self.assertRaises(ValueError): parse_answers(payload,require_complete=True)

    def test_all_mapped_questions_require_explicit_answers_before_confirmation(self):
        main, water = required_answers(True)
        payload={'reviewContentRevision':VERSION,'responseData':dict.fromkeys(main,'U'),
                 'waterRightsData':dict.fromkeys(water,'U')}
        payload['responseData']['seller_occupancy']='N'
        parse_answers(payload,has_water=True,require_complete=True)
        del payload['responseData']['defect_roof']
        with self.assertRaises(ValueError): parse_answers(payload,has_water=True,require_complete=True)

    def test_public_answers_cannot_replace_identity_source_or_delivery(self):
        for answers in ({'_hof_signature_delivery':{}},{'seller_names':['Someone else']},
                        {'disclosure_source_id':'other'},{'property_address':'Different property'},
                        {'defect_roof':'incorrect'},{'defect_roof':{}},{'notes':'x'*3001}):
            with self.subTest(answers=answers), self.assertRaises(ValueError):
                parse_answers({'reviewContentRevision':VERSION,'responseData':answers})
        with self.assertRaises(ValueError):
            parse_answers({'reviewContentRevision':VERSION,'waterRightsData':{'water_wells_known':'Y'}})

    def test_stale_intake_can_load_current_answers_but_not_authorize_old_review(self):
        link, draft = context()
        with patch.object(API,'_get',AsyncMock(side_effect=[[link],[draft]])):
            self.assertEqual(asyncio.run(API._seller_review_context(SESSION,allow_questionnaire=True))[1],draft)
        with patch.object(API,'_get',AsyncMock(side_effect=[[link],[draft]])):
            with self.assertRaises(PermissionError): asyncio.run(API._seller_review_context(SESSION))

    def test_changed_owner_name_index_or_link_lifetime_is_rejected(self):
        for change in ({'agent_user_id':'someone-else'},{'seller_name':'Someone else'},
                       {'seller_index':3},{'expires_at':'2000-01-01T00:00:00Z'},
                       {'revoked_at':'2026-10-18'},{'session_expires_at':'2000-01-01T00:00:00Z'}):
            link,draft=context();link.update(change)
            with patch.object(API,'_get',AsyncMock(side_effect=[[link],[draft]])), self.assertRaises(PermissionError):
                asyncio.run(API._seller_review_context(SESSION,allow_questionnaire=True))

    def test_save_uses_atomic_rpc_and_only_answer_fields(self):
        link,draft=context(); writes=[]
        def transport(request):
            import json
            writes.append((str(request.url),json.loads(request.content)))
            return httpx.Response(200,json={'saved':True,'reviewContentRevision':OTHER_VERSION})
        real_client=httpx.AsyncClient
        with patch.object(API,'_seller_review_context',AsyncMock(return_value=(link,draft))), \
             patch.object(API.httpx,'AsyncClient',lambda **kw:real_client(transport=httpx.MockTransport(transport))), \
             patch.object(API,'SUPABASE_URL','https://fictional.example.test'):
            result=asyncio.run(API._save_seller_questionnaire(SESSION,{
                'reviewContentRevision':VERSION,'responseData':draft['response_data'],
                'agent_user_id':'ignored-attacker','signerEmails':['wrong@example.test']}))
        self.assertEqual(result['reviewContentRevision'],OTHER_VERSION)
        self.assertEqual(len(writes),1)
        self.assertTrue(writes[0][0].endswith('/rpc/hof_save_seller_questionnaire'))
        self.assertEqual(writes[0][1]['p_answers'],draft['response_data'])
        self.assertNotIn('signerEmails',writes[0][1]);self.assertNotIn('agent_user_id',writes[0][1])

    def test_legacy_review_link_cannot_edit_answers(self):
        link,draft=context();link['questionnaire_enabled']=False
        with patch.object(API,'_seller_review_context',AsyncMock(return_value=(link,draft))), self.assertRaises(PermissionError):
            asyncio.run(API._save_seller_questionnaire(SESSION,{'reviewContentRevision':VERSION}))

    def test_confirmation_cannot_substitute_complete_answers_for_an_incomplete_saved_pdf(self):
        link,draft=context(); main,_=required_answers()
        supplied={'reviewContentRevision':VERSION,'responseData':dict.fromkeys(main,'N'),
                  'confirmed':True,'sellerName':link['seller_name']}
        with patch.object(API,'_seller_review_context',AsyncMock(return_value=(link,draft))), \
             patch.object(API.httpx,'AsyncClient') as client:
            with self.assertRaises(ValueError): asyncio.run(API._save_seller_questionnaire(SESSION,supplied,attest=True))
            client.assert_not_called()

    def test_signing_uses_only_current_saved_seller_recipients_and_hides_bearer_links(self):
        link,draft=context()
        recipients=[{'seller_index':i,'seller_name':n,'seller_email':f'qa-{i}@example.test'} for i,n in enumerate(draft['seller_names'],1)]
        send=AsyncMock(return_value={'message':'Invitations sent','signingUrls':['private-other-signer']})
        with patch.object(API,'_seller_review_context',AsyncMock(return_value=(link,draft))), \
             patch.object(API,'_seller_reviews_complete_for_draft',AsyncMock(return_value=True)), \
             patch.object(API,'_get',AsyncMock(return_value=recipients)), \
             patch.object(API,'_send_seller_disclosure_for_signature',send):
            result=asyncio.run(API._send_seller_questionnaire_for_signature(SESSION))
        self.assertEqual(send.await_args.args,({'id':draft['agent_user_id']},{'draftId':draft['id'],
                         'signerEmails':['qa-1@example.test','qa-2@example.test']}))
        self.assertNotIn('signingUrls',result)

    def test_buyer_acknowledgment_or_incomplete_reviews_do_not_trigger_public_send(self):
        link,draft=context()
        for buyers,complete in [(['QA Buyer'],True),([],False)]:
            with patch.object(API,'_seller_review_context',AsyncMock(return_value=(link,{**draft,'buyer_names':buyers}))), \
                 patch.object(API,'_seller_reviews_complete_for_draft',AsyncMock(return_value=complete)), \
                 patch.object(API,'_send_seller_disclosure_for_signature',AsyncMock()) as send:
                with self.assertRaises(PermissionError): asyncio.run(API._send_seller_questionnaire_for_signature(SESSION))
                send.assert_not_awaited()


if __name__ == '__main__': unittest.main()
