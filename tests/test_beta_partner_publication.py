from pathlib import Path
import unittest
from unittest.mock import patch
import httpx
from lib import beta_partner_publication as publication


LEAD_ID = '11111111-1111-4111-8111-111111111111'
PLACEMENT_ID = '22222222-2222-4222-8222-222222222222'
ROOT = Path(__file__).resolve().parents[1]
LEAD = {'id': LEAD_ID, 'company_name': 'Fictional QA Roofing', 'partner_type': 'roofing', 'partner_program': 'beta', 'status': 'qualified',
        'onboarding_website_url': 'https://example.com', 'onboarding_logo_url': 'https://example.com/logo.jpg', 'onboarding_market_area': 'DFW',
        'onboarding_public_contact_name': 'QA Contact', 'onboarding_public_contact_phone': '+19728376378', 'onboarding_public_description': 'Fictional roofing profile.',
        'partner_agreement_status': 'not_started', 'partner_agreement_signed_at': None, 'message': 'Existing beta terms.'}


class Client:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    async def __aenter__(self): return self
    async def __aexit__(self, *_): return False

    async def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        status, body = self.responses.pop(0)
        return httpx.Response(status, json=body, request=httpx.Request(method, url))

    async def get(self, url, **kwargs): return await self.request('GET', url, **kwargs)
    async def patch(self, url, **kwargs): return await self.request('PATCH', url, **kwargs)
    async def post(self, url, **kwargs): return await self.request('POST', url, **kwargs)


class BetaPartnerPublicationTests(unittest.IsolatedAsyncioTestCase):
    async def run_fixture(self, responses, actor='QA admin'):
        client = Client(responses)
        with patch.object(publication.httpx, 'AsyncClient', return_value=client):
            result = await publication.publish('https://example.supabase.co', 'NONAUTHENTICATING-QA-KEY', LEAD_ID, actor)
        return result, client

    async def test_explicit_free_publication_preserves_unsigned_status_and_private_contacts(self):
        result, client = await self.run_fixture([(200,[LEAD]),(200,[]),(200,[{'id':LEAD_ID}]),(201,[{'id':PLACEMENT_ID}])])
        self.assertEqual(result, {'placementId':PLACEMENT_ID,'published':True,'alreadyPublished':False,'monthlyFee':0})
        update, placement = client.calls[2][2]['json'], client.calls[3][2]['json']
        self.assertEqual(update['onboarding_status'], 'complete')
        self.assertTrue(update['message'].startswith('Existing beta terms.'))
        self.assertIn('QA admin', update['message'])
        self.assertIn('no partner signature is asserted', update['message'])
        for field in ['payment_status','partner_program','partner_agreement_status','partner_agreement_signed_at','stripe_subscription_id']:
            self.assertNotIn(field, update)
        self.assertEqual(placement['monthly_fee'], 0)
        self.assertIsNone(placement['brokerage_id'])
        self.assertIsNone(placement['agreement_confirmed_at'])
        for field in ['contact_email','contact_phone','contact_name']:
            self.assertNotIn(field, placement)
        self.assertEqual(placement['source_lead_id'], LEAD_ID)
        self.assertEqual(placement['logo_url'], LEAD['onboarding_logo_url'])
        self.assertEqual(placement['placement_tier'], 'founding')
        self.assertTrue(all(url.startswith('https://example.supabase.co/rest/v1/') for _,url,_ in client.calls))

    async def test_missing_operator_is_rejected_before_network(self):
        with patch.object(publication.httpx,'AsyncClient') as factory:
            with self.assertRaises(ValueError):
                await publication.publish('https://example.supabase.co','fixture',LEAD_ID,'')
            factory.assert_not_called()

    async def test_modern_privileged_key_is_not_sent_as_a_fake_jwt(self):
        client = Client([(200,[LEAD]),(200,[{'id':PLACEMENT_ID,'monthly_fee':0,'brokerage_id':None}])])
        with patch.object(publication.httpx,'AsyncClient',return_value=client) as factory:
            await publication.publish('https://example.supabase.co','sb_secret_FICTIONAL_KEY',LEAD_ID,'QA admin')
        self.assertNotIn('Authorization',factory.call_args.kwargs['headers'])
        self.assertEqual(factory.call_args.kwargs['headers']['apikey'],'sb_secret_FICTIONAL_KEY')
        with patch.object(publication.httpx,'AsyncClient') as factory:
            with self.assertRaises(RuntimeError):
                await publication.publish('https://example.supabase.co','sb_publishable_FICTIONAL',LEAD_ID,'QA admin')
            factory.assert_not_called()

    async def test_non_beta_or_unqualified_records_are_not_mutated(self):
        for change in ({'partner_program':'commercial'},{'status':'declined'},{'status':'waitlist'},{'id':PLACEMENT_ID},{'partner_type':'lender'}):
            lead = {**LEAD, **change}; client = Client([(200,[lead])])
            with patch.object(publication.httpx,'AsyncClient',return_value=client):
                with self.assertRaises(ValueError):
                    await publication.publish('https://example.supabase.co','fixture',LEAD_ID,'QA admin')
            self.assertEqual([c[0] for c in client.calls], ['GET'])

    async def test_invalid_or_incomplete_public_creative_does_not_publish(self):
        for change in ({'company_name':''},{'onboarding_market_area':'','market_area':''},{'onboarding_public_description':''},
                       {'onboarding_website_url':'javascript:alert(1)'},{'onboarding_logo_url':'https://secret@example.com/logo'},
                       {'onboarding_public_contact_phone':'javascript:evil'}):
            client = Client([(200,[{**LEAD, **change}])])
            with patch.object(publication.httpx,'AsyncClient',return_value=client):
                with self.assertRaises(ValueError):
                    await publication.publish('https://example.supabase.co','fixture',LEAD_ID,'QA admin')
            self.assertEqual(len(client.calls), 1)

    async def test_existing_zero_cost_platform_profile_is_idempotent(self):
        result, client = await self.run_fixture([(200,[LEAD]),(200,[{'id':PLACEMENT_ID,'monthly_fee':0,'brokerage_id':None}])])
        self.assertTrue(result['alreadyPublished'])
        self.assertEqual([c[0] for c in client.calls], ['GET','GET'])

    async def test_existing_paid_or_brokerage_profile_is_not_reclassified(self):
        for active in ({'id':PLACEMENT_ID,'monthly_fee':399,'brokerage_id':None},{'id':PLACEMENT_ID,'monthly_fee':0,'brokerage_id':'brokerage'}):
            client = Client([(200,[LEAD]),(200,[active])])
            with patch.object(publication.httpx,'AsyncClient',return_value=client):
                with self.assertRaises(ValueError):
                    await publication.publish('https://example.supabase.co','fixture',LEAD_ID,'QA admin')
            self.assertEqual(len(client.calls), 2)

    async def test_changed_application_and_failed_save_do_not_create_placement(self):
        for response in [(200,[]),(403,{'error':'denied'})]:
            client = Client([(200,[LEAD]),(200,[]),response])
            with patch.object(publication.httpx,'AsyncClient',return_value=client):
                with self.assertRaises((RuntimeError,httpx.HTTPStatusError)):
                    await publication.publish('https://example.supabase.co','fixture',LEAD_ID,'QA admin')
            self.assertEqual([c[0] for c in client.calls], ['GET','GET','PATCH'])

    async def test_unique_index_race_is_recovered_without_a_second_insert(self):
        result, client = await self.run_fixture([(200,[LEAD]),(200,[]),(200,[{'id':LEAD_ID}]),(409,{}),(200,[{'id':PLACEMENT_ID,'monthly_fee':0,'brokerage_id':None}])])
        self.assertTrue(result['alreadyPublished'])
        self.assertEqual([c[0] for c in client.calls].count('POST'), 1)

    def test_new_api_action_is_after_existing_platform_admin_boundary(self):
        source = (ROOT/'api/admin-dashboard.py').read_text()
        start = source.index('if data.get("action") == "publish_free_beta_partner":')
        guard = source.rfind('if not asyncio.run(_is_platform_admin(user)):', 0, start)
        self.assertGreater(guard, source.index('def do_POST'))
        self.assertIn("'Platform admin ' + str(user.get('id') or '')",source[start:start+600])

    def test_publication_job_is_main_only_and_keeps_credentials_in_its_last_step(self):
        workflow = (ROOT/'.github/workflows/beta-publication.yml').read_text()
        self.assertIn("github.ref == 'refs/heads/main'",workflow)
        self.assertIn("inputs.confirmation == 'PUBLISH_FREE_BETA'",workflow)
        self.assertIn('environment: production',workflow)
        self.assertIn('persist-credentials: false',workflow)
        for forbidden in ['vercel build','vercel deploy','SIGNWELL','STRIPE','RESEND','echo "$SUPABASE']:
            self.assertNotIn(forbidden,workflow)
        self.assertGreater(workflow.index('SUPABASE_SECRET_KEY:'),workflow.index('- name: Publish only'))


if __name__ == '__main__': unittest.main()
