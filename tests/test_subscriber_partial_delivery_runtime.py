"""Run the actual subscriber JS response path with controlled dependencies."""
import json
from pathlib import Path
import subprocess
import unittest

HTML = (Path(__file__).resolve().parents[1] / 'index.html').read_text()
START = HTML.index('  async function generateSubscribedPacket()')
END = HTML.index('  function pad2(', START)


class SubscriberPartialDeliveryRuntimeTests(unittest.TestCase):
    def run_generation(self, status, result):
        harness = '''
        const calls = {usage:[], refreshed:0, failed:[], success:[], logs:[], saves:[], requests:[]};
        const state = {data:{buyerEmail:'buyer@example.test',userType:'agent',_hofOfferId:'owned-offer'}};
        const hofAuth = {session:{access_token:'fixture',user:{email:'agent@example.test'}}};
        const window = {};
        const button = {disabled:false,textContent:'Generate Packet'};
        const document = {getElementById:()=>button};
        const sessionStorage = {setItem:()=>{}};
        const clearPacketGenerationRecoveryNotice = ()=>{};
        const canGenerateOffer = async()=>true;
        const preflightUsage = async()=>true;
        const collectAllData = ()=>{};
        const confirmControlledLaunchSupport = ()=>true;
        const validateParagraph4LeaseInputs = ()=>true;
        const validateSellerTemporaryLeaseInputs = ()=>true;
        const validateUploadedDisclosureDocs = ()=>true;
        const saveOfferDraftToSupabase = async status=>{calls.saves.push(status);return {id:'owned-offer'};};
        const logOfferEvent = async(...args)=>calls.logs.push(args);
        const forceOfferGeneratedStatus = async()=>{};
        const recordUsageEvent = async(...args)=>calls.usage.push(args);
        const loadCurrentUsage = async()=>{calls.refreshed++;};
        const showPaymentSuccess = (...args)=>calls.success.push(args);
        const forceOfferGenerationFailedStatus = async(...args)=>calls.failed.push(args);
        const packetGenerationFailureDetails = ()=>({category:'unknown'});
        const showPacketGenerationRecoveryNotice = ()=>{};
        const console = {error:()=>{}};
        const fetch = async(url, options)=>{calls.requests.push({url,options});return {
          ok:STATUS >= 200 && STATUS < 300,
          headers:{get:()=> 'application/json'}, json:async()=>RESULT
        };};
        '''
        script = 'const STATUS=' + str(status) + ';const RESULT=' + json.dumps(result) + ';\n'
        script += harness + HTML[START:END]
        script += '\ngenerateSubscribedPacket().then(()=>process.stdout.write(JSON.stringify({calls,state,button})));'
        return json.loads(subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True).stdout)

    def test_pending_email_preserves_successful_signing_instead_of_marking_generation_failed(self):
        result = {'status': 'delivery_pending', 'packetGenerated': True,
                  'usage': {'status': 'recorded'},
                  'documentEmail': {'status': 'unconfirmed'},
                  'signwell': {'ok': True, 'document_id': 'original-document'}}
        actual = self.run_generation(202, result)
        calls = actual['calls']
        self.assertEqual(calls['failed'], [])
        self.assertEqual(len(calls['requests']), 1)
        self.assertEqual(calls['requests'][0]['url'], '/api/fill-pdf')
        self.assertEqual(calls['success'][0][1]['documentEmail']['status'], 'unconfirmed')
        self.assertEqual(actual['state']['data']['signwellDocumentId'], 'original-document')
        self.assertEqual(calls['saves'], [])
        self.assertEqual(calls['usage'], [])
        self.assertEqual(calls['refreshed'], 1)

    def test_true_generation_error_never_becomes_a_success_or_usage_event(self):
        calls = self.run_generation(500, {'error': 'Packet could not be generated.'})['calls']
        self.assertEqual(calls['success'], [])
        self.assertEqual(calls['usage'], [])
        self.assertEqual(calls['failed'], [])

    def test_accepted_email_result_reaches_success_page(self):
        calls = self.run_generation(200, {'status': 'ok', 'packetGenerated': True, 'usage': {'status': 'recorded'}, 'documentEmail': {'status': 'accepted'},
                                        'signwell': {'ok': True}})['calls']
        self.assertEqual(calls['success'][0][1]['documentEmail']['status'], 'accepted')

    def test_missing_usage_receipt_is_not_treated_as_success(self):
        calls = self.run_generation(200, {'packetGenerated': True})['calls']
        self.assertEqual(calls['success'], [])
        self.assertEqual(calls['usage'], [])
        self.assertEqual(calls['failed'], [])

    def test_busy_or_uncertain_request_never_overwrites_saved_status(self):
        for code in ('packet_generation_busy', 'packet_generation_unconfirmed', 'packet_allowance_unavailable'):
            with self.subTest(code=code):
                calls = self.run_generation(409, {'error': 'Check your saved offer.', 'code': code})['calls']
                self.assertEqual(calls['failed'], [])
                self.assertEqual(calls['saves'], [])
                self.assertEqual(calls['usage'], [])


if __name__ == '__main__':
    unittest.main()
