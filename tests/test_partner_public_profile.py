import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from lib.partner_public_profile import approved_public_profile, public_phone, public_profile_update

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('SUPABASE_URL', 'https://example.supabase.co')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'fixture')
spec = importlib.util.spec_from_file_location('public_profile_api', ROOT / 'api/fsbo-lead.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class PartnerPublicProfileTests(unittest.TestCase):
    def test_private_contact_and_message_are_never_public_fallbacks(self):
        self.assertEqual(approved_public_profile({'contact_phone':'972-837-6378', 'contact_name':'Private', 'message':'Private'}),
                         {'partner_program':'commercial', 'public_contact_name':'', 'public_contact_phone':'', 'public_description':''})

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
                                  'contact_phone':'9999999999','message':'PRIVATE'}])
        with patch.object(api.httpx,'Client',return_value=Client()): rows=api._list_public_partner_placements()
        self.assertEqual(rows[0]['public_contact_phone'], '+19728376378')
        self.assertEqual(rows[0]['public_description'], 'DFW roof inspections')
        self.assertEqual(rows[0]['cta_label'], 'Visit site')
        for field in ('source_lead_id','contact_email','contact_phone','message','onboarding_public_contact_phone'):
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

    def test_both_surfaces_and_setup_use_same_public_model(self):
        directory=(ROOT/'directory.html').read_text()
        html=(ROOT/'index.html').read_text()
        self.assertIn("hofPartnerProfile.actions(provider, esc, 'data-partner-link')",directory)
        self.assertIn("hofPartnerProfile.actions(partner, nowWhatEscape, 'data-offer-completion-partner-link')",html)
        for field in ('public_contact_name','public_contact_phone','public_description'):
            self.assertIn(field,html)
        self.assertIn('Leave blank to keep your contact number private.',html)
        self.assertIn('/assets/partner-profile.js',(ROOT/'service-worker.js').read_text())
