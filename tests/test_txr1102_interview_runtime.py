"""Client/server answer-contract alignment and actual JavaScript runtime checks."""
import json
from pathlib import Path
import subprocess
import unittest

from lib import txr_1102 as form

ROOT=Path(__file__).resolve().parents[1]


def javascript(expression):
    result=subprocess.run(['node','-e','const m=require("./assets/txr1102-interview.js");console.log(JSON.stringify('+expression+'));'],
                          cwd=ROOT,capture_output=True,text=True,check=True)
    return json.loads(result.stdout)


class LeaseInterviewRuntimeTests(unittest.TestCase):
    def test_real_javascript_mapping_and_async_account_guards(self):
        result=subprocess.run(['node','--test',str(Path(__file__).with_name('txr1102_interview.runtime.cjs'))],
                              cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_all_answer_limits_and_preference_contracts_match_the_server(self):
        self.assertEqual(javascript('m.textLimits'),form.TEXT_LIMITS)
        self.assertEqual(javascript('m.preferenceTextLimits'),form.PREFERENCE_TEXT_LIMITS)
        self.assertEqual(javascript('m.preferenceIntegers'),list(form.PREFERENCE_INTEGERS))
        self.assertEqual(javascript('m.preferenceAmounts'),list(form.PREFERENCE_AMOUNTS))
        self.assertEqual(javascript('Object.fromEntries(Object.entries(m.preferenceChoices).map(([k,v])=>[k,v.map(x=>x[0])]))'),
                         {key:list(values) for key,values in form.PREFERENCE_CHOICES.items()})
        choices=javascript('Object.fromEntries(Object.entries(m.choices).map(([k,v])=>[k,v.map(x=>x[0])]))')
        for key,values in form.CHOICES.items():
            expected=list(values)
            if key=='internet_display':expected.remove('not_applicable')
            self.assertEqual(choices[key],expected)
        self.assertEqual(javascript('m.documentChoices'),[list(row) for row in form.DOCUMENT_CHOICES])

    def test_actual_browser_mapper_answers_are_accepted_losslessly_by_the_api_parser(self):
        from tests.test_txr_1102 import sample,with_preferences
        from tests.test_standalone_recipient_preview import MODULE as api
        cases=[sample(),with_preferences(),sample(client_names=['QA Landlord One'],client_email_2='',
            signer_plan='clients_and_broker',fee_scope='broker_only',cobroker_basis='',cobroker_amount='',
            fee_basis='other',fee_amount='',fee_other='No fee for this fictional test',
            mls_filing='none',internet_display='not_applicable',built_before_1978='unanswered')]
        script='''const m=require('./assets/txr1102-interview.js'),fs=require('node:fs');
const a=JSON.parse(fs.readFileSync(0,'utf8'));
console.log(JSON.stringify(m.collect({get:k=>a[k]??'',getAll:k=>a[k]||[]})));'''
        for original in cases:
            data={**original,'seller_one':original['client_names'][0],'seller_two':original['client_names'][1] if len(original['client_names'])==2 else ''}
            data['include_rental_preferences']='on' if original.get('include_rental_preferences') else ''
            result=subprocess.run(['node','-e',script],input=json.dumps(data),cwd=ROOT,capture_output=True,text=True,check=True)
            packet=json.loads(result.stdout)
            parsed=api._parse_txr_1102_draft({**packet,'formCode':'TXR-1102','formSourceId':'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'})
            self.assertEqual(parsed['client_names'],original['client_names'])
            expected=form.validate_answers({**original,'broker_notice_contacts':dict.fromkeys(['address','city_state_zip','phone','email','email_2'],'')})
            expected.pop('client_names')
            self.assertEqual(parsed['agreement_data'],expected)

    def test_shared_engine_and_prepared_queue_are_wired_for_both_listing_types(self):
        html=(ROOT/'index.html').read_text()
        self.assertLess(html.index('src="/assets/txr1102-interview.js?v='),html.index('src="/assets/txr1101-interview.js?v='))
        self.assertIn("openRelationshipDraft('hofOpenTxr1102Draft'",html)
        self.assertTrue("window.hofOpenAgentPackageInterview?.('lease_listing', { directPackage: 'listing_agreement' })" in html,
                        'Lease entry must open the landlord interview without a redundant task question.')
        self.assertIn("['TXR-1101','TXR-1102'].includes(agreement.form_code)",html)
        self.assertIn("const open = agreement?.form_code === 'TXR-1102'",html)
        self.assertIn("'/assets/txr1102-interview.js?v=",(ROOT/'service-worker.js').read_text())

    def test_interview_uses_the_existing_google_address_observer_and_companions(self):
        js=(ROOT/'assets/txr1102-interview.js').read_text()
        html=(ROOT/'index.html').read_text()
        self.assertIn('id="txr1101InterviewForm"',js)
        self.assertIn('autocomplete="street-address"',js)
        self.assertIn("client_address:'client_city_state_zip'",html)
        self.assertIn("broker_notice_address:'broker_notice_city_state_zip'",html)


if __name__=='__main__':
    unittest.main()
