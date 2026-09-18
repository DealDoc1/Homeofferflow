"""Execute the shipped retry controls/submit handler without network or email."""
from pathlib import Path
import json
import subprocess
import unittest

HTML = (Path(__file__).resolve().parents[1] / 'index.html').read_text()
START = HTML.index("modal.querySelector('#hofStandaloneSendForm').addEventListener('submit', async event => {")
SUBMIT = HTML[START:HTML.index('    });\n    try {', START) + len('    });')]
START = HTML.index("          const canRetryUnsent = agreement.status === 'failed'")
CONTROLS = HTML[START:HTML.index('          return `<div', START)]


class SignwellRecoveryUiTests(unittest.TestCase):
    def run_js(self, body):
        result = subprocess.run(['node', '-e', "const assert=require('node:assert/strict');\n" + body],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_retry_requires_supported_owned_saved_request_and_draft_state(self):
        self.run_js('''
          const signingEnabled=true, signingFormCodes=new Set(['TXR-1507']);
          function controls(agreement) {
        ''' + CONTROLS + '''
            return {canSend,sendLabel,canRefresh};
          }
          const base={form_code:'TXR-1507',status:'draft',signwell_document_id:'tracked'};
          assert.equal(controls(base).canSend,false);
          assert.equal(controls(base).canRefresh,'tracked');
          assert.equal(controls({...base,canRetrySavedRequest:true}).canSend,true);
          assert.equal(controls({...base,canRetrySavedRequest:true}).sendLabel,'Retry saved request');
          for (const status of ['sent','signed','void'])
            assert.equal(controls({...base,status,canRetrySavedRequest:true}).canSend,false);
          assert.equal(controls({...base,form_code:'unknown',canRetrySavedRequest:true}).canSend,false);
        ''')

    def submit_case(self, payload, response_ok=True, refresh_fails=False):
        return '''
          let handler, refreshes=0, requests=0, removals=0;
          const status={textContent:'',className:''}, submit={disabled:false};
          const formElement={querySelector:()=>submit,addEventListener:(_,fn)=>handler=fn};
          const modal={querySelector:key=>key==='#hofStandaloneSendForm'?formElement:status,remove:()=>removals++};
          const root={}, agreement={id:'draft-id',form_code:'TXR-1507'};
          const token=()=> 'test-session';
          const signers=[{id:'1',name:'Customer',emailEditable:true}];
          const FormData=class {get(){return 'customer@example.com'}};
          const setTimeout=()=>{};
          const refresh=async()=>{refreshes++; if (REFRESH_FAILS) throw Error('List unavailable');};
          const fetch=async(_,request)=>{
            requests++; assert.equal(JSON.parse(request.body).agreementId,'draft-id');
            return {ok:RESPONSE_OK,json:async()=>(PAYLOAD)};
          };
        '''.replace('REFRESH_FAILS', json.dumps(refresh_fails)).replace('RESPONSE_OK', json.dumps(response_ok)).replace('PAYLOAD', json.dumps(payload)) + SUBMIT

    def test_successful_delivery_is_not_reported_as_failed_when_list_refresh_fails(self):
        self.run_js(self.submit_case({'message': 'Signature request sent.'}, refresh_fails=True) + '''
          (async()=>{
            await handler({preventDefault(){},currentTarget:formElement});
            assert.equal(requests,1); assert.equal(refreshes,1);
            assert.equal(submit.disabled,true);
            assert.equal(status.className,'hof-iabs-status ready');
            assert.match(status.textContent,/Signature request sent/);
            assert.match(status.textContent,/could not refresh/);
          })().catch(e=>{console.error(e);process.exit(1)});
        ''')

    def test_already_completed_recovery_does_not_claim_new_invitation(self):
        message = 'This document is already fully signed. No new invitation was sent.'
        self.run_js(self.submit_case({'message': message, 'recovered': True}) + '''
          (async()=>{
            await handler({preventDefault(){},currentTarget:formElement});
            assert.equal(status.textContent,MESSAGE);
            assert.equal(submit.disabled,true); assert.equal(requests,1);
          })().catch(e=>{console.error(e);process.exit(1)});
        '''.replace('MESSAGE', json.dumps(message)))

    def test_uncertain_delivery_displays_status_instruction_without_success_claim(self):
        message = 'Delivery is still unconfirmed. Refresh its signature status before retrying.'
        self.run_js(self.submit_case({'error': message, 'deliveryUnconfirmed': True}, response_ok=False) + '''
          (async()=>{
            await handler({preventDefault(){},currentTarget:formElement});
            assert.equal(status.textContent,MESSAGE);
            assert.equal(status.className,'hof-iabs-status error');
            assert.equal(submit.disabled,false); assert.equal(refreshes,0);
          })().catch(e=>{console.error(e);process.exit(1)});
        '''.replace('MESSAGE', json.dumps(message)))
