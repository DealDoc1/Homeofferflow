"""No providers: real HTTP handler, private-source hydration and packet builder."""
from io import BytesIO
import hashlib
import hmac
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from tests.test_assumption_purchase_packet import assumption_offer, SOURCE
from tests.test_controlled_launch import configure_local_forms
from tests.test_paragraph4_source_hydration import load_offer_api, FakeResponse
from lib import production_adapter as adapter
from lib.checkout_payload import load_checkout_payload

ROOT = Path(__file__).resolve().parents[1]
SECRET = 'local-preflight-secret'


def run_preflight(body, signature, *, source=SOURCE, hydrate_error=False):
    api = load_offer_api()
    configure_local_forms()
    api.INTERNAL_CHECKOUT_FORWARD_SECRET = SECRET
    api.SUPABASE_URL = 'https://db.example.test'
    api.SUPABASE_SERVICE_ROLE_KEY = 'fake'
    request = api.handler.__new__(api.handler)
    request.headers = {'Content-Length': str(len(body)), 'x-homeofferflow-preflight-signature': signature}
    request.rfile = BytesIO(body)
    replies = []
    request._json = lambda status, data: replies.append((status, data))
    reads = [FakeResponse(503)] if hydrate_error else [
        FakeResponse(200, payload=[{'id':'source-fixture','source_revision':'11-07-2022',
                                  'storage_bucket':'private','storage_path':'TXR1919.pdf'}]),
        FakeResponse(200, content=source)]
    with patch.object(adapter, 'ASSUMPTION_SOURCE_SHA256', hashlib.sha256(SOURCE).hexdigest()), \
         patch.object(api.httpx, 'get', side_effect=reads) as get, \
         patch.object(api, 'create_signwell_signature_request') as send, \
         patch.object(api, 'send_email') as email, \
         patch.object(api, 'prepare_offer_signing_record') as record, \
         patch.object(api, 'render_subscribed_packet') as usage:
        request.do_POST()
        send.assert_not_called(); email.assert_not_called()
        record.assert_not_called(); usage.assert_not_called()
    return {'status':replies[0][0], 'payload':replies[0][1], 'reads':get.call_count}


def signed_request(offer, timestamp=None, prefix='checkout-preflight.'):
    body = json.dumps({'action':'checkout_packet_preflight','offerData':offer}, separators=(',',':')).encode()
    stamp = str(int(time.time()) if timestamp is None else timestamp)
    signature = hmac.new(SECRET.encode(), stamp.encode()+b'.'+prefix.encode()+body, hashlib.sha256).hexdigest()
    return body, f't={stamp},v1={signature}'


def public_offer(**updates):
    offer = assumption_offer(**updates)
    offer.pop('_paragraph4_source_pdf_bytes')
    return offer


class AssumptionCheckoutTests(unittest.TestCase):
    def test_node_checkout_boundary(self):
        run = subprocess.run(['node','--test','tests/assumption_checkout.runtime.cjs'], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_actual_preflight_normalizes_without_sending_or_persisting(self):
        offer = public_offer(_paragraph4_source_pdf_bytes={'TXR-1919':'forged'}, paragraph4SourceRevisions={'TXR-1919':'forged'})
        result = run_preflight(*signed_request(offer))
        self.assertEqual(result['status'],200,result)
        self.assertEqual(result['reads'],2)
        self.assertEqual(result['payload'],{'ok':True,'pages':14,'totals':{
            'price':'500000.55','loanAmount':'270000.35','downPayment':'230000.20'}})
        self.assertNotIn('source',json.dumps(result['payload']).lower())

    def test_bad_terms_and_signers_are_rejected_before_source_reads(self):
        for changes in [{'assumptionFirstBalance':'1.001'}, {'assumptionCreditDays':'0'},
                        {'assumptionCreditDocuments':[]}, {'assumptionFirstLender':''},
                        {'assumptionFirstRateCap':'101'}, {'assumptionVarianceThreshold':''},
                        {'assumptionFirstEnabled':False,'assumptionSecondEnabled':False},
                        {'price':'1'}, {'seller1Email':'bad'}, {'buyer2':'Missing email'},
                        {'seller1Email':'buyer@example.com'}, {'address':''}, {'sellerFinancing':'yes'}]:
            with self.subTest(changes=changes):
                result=run_preflight(*signed_request(public_offer(**changes)))
                self.assertEqual(result['status'],422,result)
                self.assertEqual(result['reads'],0)

    def test_missing_or_changed_source_cannot_become_ready(self):
        for args in [{'hydrate_error':True},{'source':SOURCE+b'changed'}]:
            result=run_preflight(*signed_request(public_offer()),**args)
            self.assertEqual(result['status'],422)
            self.assertNotIn('storage_path',json.dumps(result['payload']))

    def test_missing_expired_tampered_or_delivery_signature_cannot_call_builder(self):
        body, signature = signed_request(public_offer())
        for raw, sig in [(body,''),signed_request(public_offer(),timestamp=1),
                         (body+b' ',signature),signed_request(public_offer(),prefix='')]:
            result=run_preflight(raw,sig)
            self.assertEqual(result['status'],401)
            self.assertEqual(result['reads'],0)

        api=load_offer_api()
        self.assertFalse(api.verify_internal_checkout_forward_signature(body,signature,SECRET),
                         'A preflight signature must not authorize paid delivery')

    def test_first_second_and_two_loan_choices_preserve_exact_totals(self):
        for changes, loan, cash in [({'assumptionSecondEnabled':False},'240000.12','260000.43'),
                                   ({'assumptionFirstEnabled':False},'30000.23','470000.32'),
                                   ({},'270000.35','230000.20')]:
            with self.subTest(changes=changes):
                result=run_preflight(*signed_request(public_offer(**changes)))
                self.assertEqual(result['status'],200,result)
                self.assertEqual(result['payload']['totals']['loanAmount'],loan)
                self.assertEqual(result['payload']['totals']['downPayment'],cash)

    def test_node_to_python_to_saved_checkout_and_paid_loader(self):
        # The fake fetch crosses the language boundary into the real handler;
        # only remote source reads and Stripe/storage writes are substituted.
        script = r"""
const {checkout}=require('./tests/assumption_checkout.runtime.cjs');
const {spawnSync}=require('node:child_process');
let raw='';process.stdin.on('data',c=>raw+=c);process.stdin.on('end',async()=>{
 const result=await checkout(JSON.parse(raw),async(url,options)=>{
  const child=spawnSync(process.env.HOF_TEST_PYTHON,['tests/test_assumption_checkout.py','--preflight'],{
   input:JSON.stringify({body:options.body,signature:options.headers['X-HomeOfferFlow-Preflight-Signature']}),encoding:'utf8',env:process.env});
  if(child.status!==0)throw Error(child.stderr);
  const response=JSON.parse(child.stdout);return{ok:response.status===200,status:response.status,json:async()=>response.payload};
 });process.stdout.write(JSON.stringify(result));
});
"""
        import os
        result=subprocess.run(['node','-e',script],input=json.dumps(public_offer()),cwd=ROOT,
                              env={**os.environ,'HOF_TEST_PYTHON':sys.executable},capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data['status'],200,data)
        self.assertEqual(data['events'],['preflight','stripe','save','create','bind'])
        offer=data['saved'][0]
        self.assertEqual(offer['loanAmount'],'270000.35')
        session=data['sessions'][0]
        self.assertNotIn('assumptionFirstLender',session['metadata'])
        # JSON serialization must reproduce the exact bytes saved by Node.
        raw=json.dumps(offer,ensure_ascii=False,separators=(',',':'))
        row={'id':session['metadata']['offer_payload_id'],'payload_text':raw,
             'payload_sha256':session['metadata']['offer_payload_sha256'],'stripe_session_id':'cs_local'}
        self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(),row['payload_sha256'])
        paid={**session,'id':'cs_local','payment_status':'paid'}
        from unittest.mock import Mock
        client=Mock();client.get.return_value=FakeResponse(200,payload=[row])
        restored=load_checkout_payload(paid,supabase_url='https://db.example.test',service_key='fake',client=client)
        self.assertEqual(restored,offer)
        terms,total,price=adapter.parse_assumption_terms(restored)
        self.assertEqual(str(total),'270000.35');self.assertEqual(str(price-total),'230000.20')
        self.assertEqual(terms['loans']['first']['monthly_payment'],'1,750.25')

        # Continue through actual paid fulfillment and signature-payload creation.
        # Provider sends, email and offer writes remain mocked and captured.
        api=load_offer_api();configure_local_forms()
        api.SUPABASE_URL='https://db.example.test';api.SUPABASE_SERVICE_ROLE_KEY='fake'
        api.SIGNWELL_ENABLED=True;api.SIGNWELL_API_KEY='fake'
        with patch.object(adapter,'ASSUMPTION_SOURCE_SHA256',hashlib.sha256(SOURCE).hexdigest()), \
             patch.object(api.httpx,'get',side_effect=[FakeResponse(200,payload=[row]),
                 FakeResponse(200,payload=[{'source_revision':'11-07-2022','storage_bucket':'private','storage_path':'TXR1919.pdf'}]),
                 FakeResponse(200,content=SOURCE)]), \
             patch.object(api,'prepare_offer_signing_record',return_value={'id':'offer-fixture'}), \
             patch.object(api,'deliver_offer_document',return_value={'document_id':'document-fixture',
                 'document':{'status':'sent'},'state':'sent','message':'sent','recovered':False}) as deliver, \
             patch.object(api,'send_email',return_value={'status':'accepted'}) as email, \
             patch.object(api,'send_admin_order_email',return_value={'status':'accepted'}):
            result=api.handle_checkout({'type':'checkout.session.completed','data':{'object':paid}})
        self.assertTrue(result['packetGenerated'])
        payload=deliver.call_args.args[1]
        self.assertFalse(payload['apply_signing_order'])
        self.assertEqual(len(payload['files']),1)
        self.assertEqual([r['id'] for r in payload['recipients']],['1','3'])
        self.assertEqual(email.call_args.kwargs['delivery_identity'],'checkout:cs_local')
        from pypdf import PdfReader
        reader=PdfReader(BytesIO(email.call_args.args[3]))
        self.assertEqual(len(reader.pages),14)
        for amount in ['500,000.55','270,000.35','230,000.20']:
            self.assertIn(amount,reader.pages[0].extract_text())


if __name__=='__main__':
    if '--preflight' in sys.argv:
        request=json.load(sys.stdin)
        print(json.dumps(run_preflight(request['body'].encode(),request['signature'])))
    else:
        unittest.main()
