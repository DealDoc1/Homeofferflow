"""Run the shipped purchase retry handler with controlled service responses."""
import json
from pathlib import Path
import subprocess
import unittest

HTML = (Path(__file__).resolve().parents[1] / 'index.html').read_text()
HANDLER = HTML[HTML.index('  async function retryOfferSignature('):HTML.index('  async function refreshSignWellStatus(')]


class OfferRecoveryUiTests(unittest.TestCase):
    def run_case(self, payload, *, success=True, refresh_fails=False, signed_in=True):
        setup = '''
        const messages=[],requests=[];
        let refreshes=0;
        const hofAuth={session:SIGNED_IN?{access_token:'test-only'}:null};
        const window={announceWorkspaceStatus:message=>messages.push(message)};
        const setAuthStatus=message=>messages.push(message);
        const fetch=async(url,options)=>{
          requests.push({url,body:JSON.parse(options.body),headers:options.headers});
          return {ok:SUCCESS,json:async()=>(PAYLOAD)};
        };
        const loadMyOffers=async()=>{refreshes++;if(REFRESH_FAILS)throw Error('List unavailable')};
        const button={disabled:false,textContent:'Retry signing'};
        '''.replace('SIGNED_IN', json.dumps(signed_in)).replace('SUCCESS', json.dumps(success)).replace('PAYLOAD', json.dumps(payload)).replace('REFRESH_FAILS', json.dumps(refresh_fails))
        script = setup + HANDLER + '''
        retryOfferSignature('offer-id',button).then(()=>{
          process.stdout.write(JSON.stringify({messages,requests,refreshes,button}));
        }).catch(error=>{console.error(error);process.exitCode=1});
        '''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_success_survives_list_refresh_failure_without_reenabling_send(self):
        result = self.run_case({'ok': True, 'message': 'Signature request sent.'}, refresh_fails=True)
        self.assertTrue(result['button']['disabled'])
        self.assertEqual(len(result['requests']), 1)
        self.assertEqual(result['requests'][0]['body'], {'action': 'retry_offer_signature', 'offerId': 'offer-id'})
        self.assertEqual(result['requests'][0]['headers']['Authorization'], 'Bearer test-only')
        self.assertIn('Signature request sent.', result['messages'][-1])
        self.assertIn('could not refresh', result['messages'][-1])

    def test_completed_recovery_does_not_claim_a_new_invitation(self):
        message = 'This document is already fully signed. No new invitation was sent.'
        result = self.run_case({'ok': True, 'message': message})
        self.assertEqual(result['messages'], [message])
        self.assertTrue(result['button']['disabled'])

    def test_uncertain_delivery_keeps_the_status_instruction(self):
        message = 'Delivery is still unconfirmed. Check signature status before retrying.'
        result = self.run_case({'error': message, 'deliveryUnconfirmed': True}, success=False)
        self.assertEqual(result['messages'], [message])
        self.assertEqual(result['refreshes'], 0)
        self.assertFalse(result['button']['disabled'])

    def test_signed_out_user_cannot_send(self):
        result = self.run_case({}, signed_in=False)
        self.assertEqual(result['requests'], [])
        self.assertIn('sign in', result['messages'][0])
