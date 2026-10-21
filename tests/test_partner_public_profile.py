import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from lib.partner_public_profile import approved_public_profile, public_phone, public_profile_update, public_headshot

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('SUPABASE_URL', 'https://example.supabase.co')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'fixture')
spec = importlib.util.spec_from_file_location('public_profile_api', ROOT / 'api/fsbo-lead.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class PartnerPublicProfileTests(unittest.TestCase):
    def test_private_contact_and_message_are_never_public_fallbacks(self):
        self.assertEqual(approved_public_profile({'contact_phone':'972-837-6378', 'contact_name':'Private', 'message':'Private'}),
                         {'partner_program':'commercial', 'public_contact_name':'', 'public_contact_phone':'', 'public_description':'', 'public_headshot_url':''})

    def test_headshot_is_explicit_optional_preserved_or_removed_without_private_fallback(self):
        image = 'https://example.com/public-photo.jpg'
        previous = {'onboarding_public_headshot_url':image, 'avatar_url':'https://private.example/avatar.jpg'}
        self.assertEqual(public_profile_update({},previous)['onboarding_public_headshot_url'],image)
        self.assertIsNone(public_profile_update({'public_headshot_url':''},previous)['onboarding_public_headshot_url'])
        self.assertEqual(approved_public_profile({'avatar_url':image,'photo_url':image})['public_headshot_url'],'')
        self.assertEqual(approved_public_profile(previous)['public_headshot_url'],image)

    def test_invalid_stored_or_supplied_headshots_never_become_public_images(self):
        for value in ('javascript:alert(1)','data:image/png;base64,AAA','http://example.com/photo.jpg',
                      'https://user:pass@example.com/photo.jpg','https://example.com:wrong/a.jpg',
                      'https://example.com:8443/a.jpg','https://example.com/a\n.jpg',
                      'https://example.com/" onerror="evil','https://example.com/'+'a'*501):
            with self.subTest(value=value):
                with self.assertRaises(ValueError): public_headshot(value)
                self.assertEqual(approved_public_profile({'onboarding_public_headshot_url':value})['public_headshot_url'],'')

    def test_headshot_path_is_bound_to_partner_before_any_save_or_dispatch(self):
        lead_id='b7b2ede6-bca8-400f-86d7-6ec80a5a2575'
        with patch.object(api,'_get_partner_onboarding',return_value={'id':lead_id}), \
             patch.object(api.httpx,'Client') as client, \
             patch.object(api,'_dispatch_partner_agreement_after_onboarding') as dispatch:
            with self.assertRaisesRegex(ValueError,'headshot upload is unavailable'):
                api._complete_partner_onboarding('fixture',{'market_area':'DFW','headshot_path':
                    'partners/11111111-1111-4111-8111-111111111111/'+'a'*32+'.jpg'})
            client.assert_not_called(); dispatch.assert_not_called()

    def test_headshot_setup_uses_existing_bounded_upload_and_never_activates_placement(self):
        from tests.test_partner_self_service_onboarding import fsbo
        lead_id='b7b2ede6-bca8-400f-86d7-6ec80a5a2575'
        path='partners/'+lead_id+'/'+'a'*32+'.jpg'
        class Response:
            status_code=200; text='[{}]'
            def json(self): return [{'id':lead_id}]
        class Client:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def patch(self,url,**kwargs): self.payload=kwargs['json']; return Response()
        client=Client()
        with patch.object(fsbo,'_get_partner_onboarding',return_value={'id':lead_id}), \
             patch.object(fsbo.httpx,'Client',return_value=client), \
             patch.object(fsbo,'_dispatch_partner_agreement_after_onboarding'), \
             patch.object(fsbo,'_record_partner_onboarding_event'):
            fsbo._complete_partner_onboarding('fixture',{'market_area':'DFW','headshot_path':path})
        self.assertEqual(client.payload['onboarding_public_headshot_url'],
            'https://example.supabase.co/storage/v1/object/public/brokerage-branding/'+path)
        for field in ('is_active','payment_status','monthly_fee','partner_program'):
            self.assertNotIn(field,client.payload)

    def test_nullable_headshot_migration_preserves_existing_access_and_release_probes_column(self):
        sql=(ROOT/'supabase/migrations/20261021202420_partner_public_headshot.sql').read_text()
        self.assertIn('add column if not exists onboarding_public_headshot_url text',sql)
        self.assertIn("lock_timeout = '5s'",sql)
        for forbidden in ('grant ', 'create policy', 'disable row level security', 'update public.', 'delete from'):
            self.assertNotIn(forbidden,sql.lower())
        readiness=(ROOT/'scripts/check_production_schema_readiness.py').read_text()
        self.assertIn('onboarding_public_description,onboarding_public_headshot_url',readiness)

    def test_headshot_upload_has_same_partner_scoped_token_and_size_type_limits_as_logo(self):
        lead_id='b7b2ede6-bca8-400f-86d7-6ec80a5a2575'
        response=type('Response',(),{'status_code':200,'text':'{}','json':lambda self:{'token':'short-lived'}})()
        client=type('Client',(),{'__enter__':lambda self:self,'__exit__':lambda *args:False})()
        client.post=unittest.mock.Mock(return_value=response)
        with patch.object(api,'_get_partner_onboarding',return_value={'id':lead_id}), \
             patch.object(api.httpx,'Client',return_value=client):
            result=api._create_partner_logo_upload('fictional',{'image_kind':'headshot','content_type':'image/webp','size_bytes':2048})
            self.assertEqual(result['bucket'],'brokerage-branding')
            self.assertRegex(result['path'],r'^partners/'+lead_id+r'/[0-9a-f]{32}\.webp$')
            self.assertEqual(result['token'],'short-lived')
            self.assertEqual(client.post.call_args.kwargs['json'],{'upsert':False})
            client.post.reset_mock()
            for data in ({'image_kind':'headshot','content_type':'image/svg+xml','size_bytes':1},
                         {'image_kind':'headshot','content_type':'image/png','size_bytes':2097153},
                         {'image_kind':{},'content_type':'image/png','size_bytes':1}):
                with self.subTest(data=data),self.assertRaises(ValueError):
                    api._create_partner_logo_upload('fictional',data)
            client.post.assert_not_called()

    def test_phone_is_normalized_and_bad_uri_input_rejected(self):
        for number in ('972-837-6378', '(972) 837 6378', '+1 972 837 6378', '19728376378'):
            self.assertEqual(public_phone(number), '+19728376378')
        self.assertEqual(public_phone('+44 20 7946 0958'), '+442079460958')
        for number in ('javascript:alert(1)', 'tel:+19728376378', '972-837-6378 ext 2', 'abc', '+00000000000', '911', '972\n8376378'):
            with self.subTest(number=number), self.assertRaises(ValueError): public_phone(number)

    def test_empty_phone_removes_call_action_and_legacy_submit_preserves_public_details(self):
        previous = {'onboarding_public_contact_phone':'+19728376378', 'onboarding_public_contact_name':'Tedd Hansen'}
        self.assertEqual(public_profile_update({}, previous)['onboarding_public_contact_phone'], '+19728376378')
        self.assertIsNone(public_profile_update({'public_contact_phone':''}, previous)['onboarding_public_contact_phone'])
        self.assertIsNone(public_profile_update({})['onboarding_public_contact_phone'])

    def test_description_and_name_limits_and_unicode(self):
        result = public_profile_update({'public_contact_name':'Tédd', 'public_description':'DFW roof inspections'})
        self.assertEqual(result['onboarding_public_contact_name'], 'Tédd')
        with self.assertRaises(ValueError): public_profile_update({'public_description':'a'*601})
        with self.assertRaises(ValueError): public_profile_update({'public_contact_name':'a'*81})
        self.assertEqual(approved_public_profile({'onboarding_public_contact_phone':'javascript:evil'})['public_contact_phone'], '')

    def test_public_directory_uses_only_opted_in_profile_and_strips_private_data(self):
        lead_id = 'b7b2ede6-bca8-400f-86d7-6ec80a5a2575'
        calls = []
        class Response:
            status_code=200
            text='yes'
            def __init__(self, rows): self.rows=rows
            def json(self): return self.rows
        class Client:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def get(self,url,**kwargs):
                calls.append(url)
                if 'hof_partner_placements?' in url:
                    return Response([{'id':'placement','partner_name':'Integrity First','source_lead_id':lead_id,
                                      'contact_email':'private@invalid.test','contact_phone':'9999999999'}])
                return Response([{'id':lead_id,'onboarding_cta_label':'Visit site',
                                  'onboarding_public_contact_phone':'+19728376378',
                                  'onboarding_public_contact_name':'Tedd Hansen',
                                  'onboarding_public_description':'DFW roof inspections',
                                  'onboarding_public_headshot_url':'https://example.com/public-photo.jpg',
                                  'avatar_url':'https://private.example/photo.jpg',
                                  'contact_phone':'9999999999','message':'PRIVATE'}])
        with patch.object(api.httpx,'Client',return_value=Client()): rows=api._list_public_partner_placements()
        self.assertEqual(rows[0]['public_contact_phone'], '+19728376378')
        self.assertEqual(rows[0]['public_description'], 'DFW roof inspections')
        self.assertEqual(rows[0]['cta_label'], 'Visit site')
        self.assertEqual(rows[0]['public_headshot_url'],'https://example.com/public-photo.jpg')
        for field in ('source_lead_id','contact_email','contact_phone','message','avatar_url','onboarding_public_contact_phone'):
            self.assertNotIn(field, rows[0])
        self.assertNotIn('contact_email', calls[1])
        self.assertIn('onboarding_public_contact_phone', calls[1])

    def test_phone_validation_occurs_before_setup_write_or_agreement_dispatch(self):
        with patch.object(api,'_get_partner_onboarding',return_value={'id':'fixture'}), \
             patch.object(api.httpx,'Client') as client, \
             patch.object(api,'_dispatch_partner_agreement_after_onboarding') as agreement:
            with self.assertRaises(ValueError):
                api._complete_partner_onboarding('fixture',{'market_area':'DFW','public_contact_phone':'javascript:evil'})
            client.assert_not_called()
            agreement.assert_not_called()

    def test_actual_client_helpers(self):
        result = subprocess.run(['node','--test',str(ROOT/'tests/partner_public_profile.runtime.cjs')],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_actual_headshot_setup_upload_and_retry_handlers(self):
        result = subprocess.run(['node','--test',str(ROOT/'tests/partner_headshot_setup.runtime.cjs')],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_both_surfaces_and_setup_use_same_public_model(self):
        directory=(ROOT/'directory.html').read_text()
        html=(ROOT/'index.html').read_text()
        self.assertIn("hofPartnerProfile.actions(provider, esc, 'data-partner-link')",directory)
        self.assertIn("hofPartnerProfile.actions(partner, nowWhatEscape, 'data-offer-completion-partner-link')",html)
        for field in ('public_contact_name','public_contact_phone','public_description'):
            self.assertIn(field,html)
        self.assertIn('Leave blank to keep your contact number private.',html)
        self.assertIn('/assets/partner-profile.js',(ROOT/'service-worker.js').read_text())
        for source in (directory, html, (ROOT/'assets/inspection-partners.js').read_text(),
                       (ROOT/'assets/insurance-partners.js').read_text()):
            self.assertIn('hofPartnerProfile.portrait?.(',source)
        self.assertIn('/assets/partner-profile.css',(ROOT/'service-worker.js').read_text())
        self.assertIn('Use a photo you approve for public display.',html)
        self.assertIn("document.getElementById('partnerSetupHeadshotRemove').checked = false",html)
        self.assertIn('#partnerOnboardingStatus:not(:empty){display:block}',(ROOT/'assets/partner-profile.css').read_text())
