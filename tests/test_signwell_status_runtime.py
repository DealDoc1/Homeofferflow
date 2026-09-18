"""Exercise the real status API and dashboard classifiers with offline fixtures."""
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text()
FRONTEND = (
    HTML[HTML.index('  function getOfferBestStatus'):HTML.index('  function offerStatusClass')]
    + '\nconst cleanStatus=o=>cleanOfferStatus(getOfferBestStatus(o));\n'
    + HTML[HTML.index('  function bucketForOffer(o)'):HTML.index('  function nextAction(o)')]
)
EARLY_NORMALIZERS = HTML[HTML.index('  window.cleanOfferStatus = function(status)'):HTML.index('  window.offerStatusClass = function(status)')]


class SignwellStatusRuntimeTests(unittest.TestCase):
    def test_stale_refresh_is_rejected_instead_of_overwriting_retry_or_completion(self):
        self.run_js('''
          rejectStaleWrite = true;
          for (const kind of ['offerId', 'agreementId', 'sellerDisclosureId']) {
            const res = await run(kind, {status:'draft'});
            assert.equal(res.code,409);
            assert.match(res.body.error,/changed while its status was being checked/);
            assert.equal(res.body.ok,undefined);
          }
        ''')

    def run_js(self, scenario):
        setup = r'''
          const assert = require('node:assert/strict');
          const vm = require('node:vm');
          const source = require('node:fs').readFileSync(SOURCE_PATH,'utf8');
          const writes = [], providerCalls = [];
          let providerDocument = {}, allowRead = true, rejectStaleWrite = false, savedOfferStatus = 'draft';
          const response = (data, ok=true) => ({ok,status:ok?200:403,
            json:async()=>data,text:async()=>JSON.stringify(data),
            arrayBuffer:async()=>Buffer.from('%PDF-test')});
          const tables={offerId:'hof_offers',agreementId:'hof_standalone_agreements',
            sellerDisclosureId:'hof_seller_disclosure_drafts'};
          const fetch = async (url,options={}) => {
            if (url.includes('/auth/v1/user')) return response({id:'owner',email:'owner@example.com'});
            if (url.startsWith('https://www.signwell.com/')) {
              providerCalls.push({url,options});
              return response(providerDocument);
            }
            const table=Object.values(tables).find(name=>url.includes('/'+name+'?'));
            if (table) {
              assert.ok(url.includes(table==='hof_offers'?'user_id=eq.owner':'agent_user_id=eq.owner'));
              if (options.method==='PATCH') {
                if (table !== 'hof_offers') {
                  assert.ok(url.includes('updated_at=eq.2026-09-15T10%3A00%3A00Z'));
                  assert.ok(url.includes('signwell_document_id=eq.provider-doc'));
                  assert.ok(url.includes('status=eq.draft'));
                } else {
                  assert.ok(url.includes('last_updated=eq.2026-09-15T10%3A00%3A00Z'));
                  assert.ok(url.includes('signwell_document_id=eq.provider-doc'));
                }
                const payload=JSON.parse(options.body);
                writes.push({url,payload});
                if (rejectStaleWrite) return response([]);
                return response([{id:'packet',...payload}]);
              }
              return response(allowRead?[{id:'packet',user_id:'owner',agent_user_id:'owner',
                signwell_document_id:'provider-doc',status:table==='hof_offers'?savedOfferStatus:'draft',updated_at:'2026-09-15T10:00:00Z',last_updated:'2026-09-15T10:00:00Z',offer_data:{},agreement_data:{}}]:[]);
            }
            if (url.endsWith('/hof_offer_events')) return response(null);
            throw new Error('Unexpected request: '+url);
          };
          const context={module:{exports:{}},process:{env:{SUPABASE_URL:'https://database.example',
            SUPABASE_SERVICE_ROLE_KEY:'test-only',SIGNWELL_API_KEY:'test-only'}},
            fetch,Buffer,console:{error(){}}};
          vm.runInNewContext(source,context);
          const run = async (kind,doc,action='refresh_status')=>{
            providerDocument=doc; writes.length=0; providerCalls.length=0;
            const res={status(code){this.code=code;return this},json(body){this.body=body;return this},
              setHeader(){},send(body){this.body=body;return this}};
            await context.module.exports({method:'POST',headers:{authorization:'Bearer test-token'},
              body:{[kind]:'packet',action}},res);
            assert.ok(providerCalls.every(call=>(call.options.method||'GET')==='GET'));
            return res;
          };
        '''.replace('SOURCE_PATH', json.dumps(str(ROOT / 'api/signwell-status.js')))
        result = subprocess.run(['node', '-e', setup + FRONTEND + '\nconst window={};\n' + EARLY_NORMALIZERS + '\n(async()=>{\n' + scenario
                                 + '\n})().catch(e=>{console.error(e);process.exitCode=1});'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_draft_is_never_persisted_as_sent_or_shown_awaiting_signature(self):
        self.run_js('''
          for (const kind of Object.keys(tables)) {
            for (const status of ['draft','created','saved']) {
              const res=await run(kind,{status});
              assert.equal(res.code,200);
              assert.equal(res.body.status,'Draft - not sent');
              assert.equal(writes[0].payload.status,kind==='offerId'?'Generated':'draft');
              assert.equal(writes[0].payload.signwell_status,'Draft - not sent');
              assert.equal(writes[0].payload.signed_at,undefined);
            }
          }
          const offer={signwell_document_id:'provider-doc',signwell_status:'Draft - not sent',
            offer_data:{signwell:{response:{status:'completed'}}}};
          assert.equal(getOfferBestStatus(offer),'Draft - not sent');
          assert.equal(bucketForOffer(offer),'generated');
          assert.equal(signingLabel(offer),'Not sent yet');
          assert.equal(getOfferSigningBucket(offer),'');
        ''')

    def test_unknown_or_empty_provider_result_never_changes_saved_status(self):
        self.run_js('''
          for (const kind of Object.keys(tables)) {
            for (const doc of [{},{status:'unsigned'},{status:'not sent'},
              {status:'not completed'},{status:'future-state',recipients:[{status:'completed'}]}]) {
              const res=await run(kind,doc);
              assert.equal(res.code,400);
              assert.equal(writes.length,0);
            }
          }
          for (const status of ['not completed','not signed','unsigned']) {
            const offer={signwell_status:status,signwell_document_id:'doc'};
            assert.notEqual(bucketForOffer(offer),'signed');
            assert.notEqual(getOfferSigningBucket(offer),'signed');
          }
        ''')

    def test_partial_document_and_individual_signature_never_complete_packet(self):
        self.run_js('''
          for (const kind of Object.keys(tables)) {
            for (const status of ['pending','in_progress','signed','document_signed']) {
              const res=await run(kind,{status});
              assert.equal(res.code,200);
              assert.equal(res.body.status,'Partially Signed');
              assert.notEqual(writes[0].payload.status,'signed');
              assert.equal(writes[0].payload.signed_at,undefined);
            }
          }
          const offer={signwell_status:'Partially Signed',signwell_document_id:'provider-doc',
            offer_data:{signwell:{response:{status:'completed'}}}};
          assert.equal(bucketForOffer(offer),'signing');
          assert.equal(signingLabel(offer),'Partially signed');
        ''')

    def test_missing_signer_status_and_cc_only_cannot_unlock_completed_pdf(self):
        self.run_js('''
          for (const kind of Object.keys(tables)) {
            for (const recipients of [[{status:'completed'},{}],
              [{status:'signed'},{status:'signed'}],[{status:'completed',role:'cc'}]]) {
              const res=await run(kind,{recipients},'download_completed_pdf');
              assert.equal(res.code,400);
              assert.equal(writes.length,0);
              assert.equal(providerCalls.length,1);
            }
          }
        ''')

    def test_document_completion_still_updates_owned_packet_and_allows_download(self):
        self.run_js('''
          for (const kind of Object.keys(tables)) {
            const res=await run(kind,{status:'completed'});
            assert.equal(res.code,200);
            assert.equal(res.body.status,'Buyer Signatures Complete');
            assert.equal(writes[0].payload.status,kind==='offerId'?'Signed':'signed');
            const download=await run(kind,{status:'completed'},'download_completed_pdf');
            assert.equal(download.code,200);
            assert.equal(writes.length,0);
            assert.ok(providerCalls[1].url.includes('/completed_pdf?'));
          }
          assert.equal(cleanOfferStatus('Buyer Signatures Complete'),'Buyer Signatures Complete');
        ''')

    def test_sent_and_cancelled_have_distinct_noncompletion_states(self):
        self.run_js('''
          for (const kind of Object.keys(tables)) {
            assert.equal((await run(kind,{status:'sent'})).body.status,'Awaiting Buyer Signature');
            const res=await run(kind,{status:'canceled'});
            assert.equal(res.body.status,'Cancelled');
            if(kind!=='offerId') assert.equal(writes[0].payload.status,'void');
          }
          assert.equal(bucketForOffer({signwell_status:'Cancelled',signwell_document_id:'doc'}),'inactive');
        ''')

    def test_ownership_denial_prevents_provider_access_and_database_write(self):
        self.run_js('''
          allowRead=false;
          for (const kind of Object.keys(tables)) {
            const res=await run(kind,{status:'completed'});
            assert.equal(res.code,400);
            assert.equal(providerCalls.length,0);
            assert.equal(writes.length,0);
          }
        ''')

    def test_offer_refresh_uses_database_supported_lifecycle_values(self):
        self.run_js('''
          for (const [provider,expected] of Object.entries({sent:'Sent for Signature',
            viewed:'Buyer Viewed',pending:'Partially Signed',declined:'Rejected',canceled:'Rejected',expired:'Expired'})) {
            const res=await run('offerId',{status:provider});
            assert.equal(res.code,200);
            assert.equal(writes[0].payload.status,expected);
          }
        ''')

    def test_offer_refresh_cannot_regress_completion_or_business_progress(self):
        self.run_js('''
          for (const saved of ['Signed','Buyer Signed','Buyer Signatures Complete','Rejected','Expired']) {
            savedOfferStatus=saved;
            const res=await run('offerId',{status:'draft'});
            assert.equal(res.code,400); assert.equal(writes.length,0);
          }
          for (const saved of ['Submitted','Accepted','Deleted']) {
            savedOfferStatus=saved;
            const res=await run('offerId',{status:'completed'});
            assert.equal(res.code,200); assert.equal(writes[0].payload.status,saved);
            assert.equal(writes[0].payload.signwell_status,'Buyer Signatures Complete');
          }
        ''')

    def test_early_dashboard_normalizers_preserve_partial_and_unconfirmed_states(self):
        self.run_js('''
          assert.equal(window.cleanOfferStatus('Partially Signed'),'Partially Buyer Signed');
          assert.equal(window.cleanOfferStatus('Draft - not sent'),'Draft - not sent');
          assert.notEqual(window.cleanOfferStatus('not completed'),'Buyer Signed');
          assert.notEqual(window.cleanOfferStatus('unsigned'),'Buyer Signed');
          assert.equal(window.getOfferBestStatus({signwell_status:'Partially Signed',
            offer_data:{signwell:{response:{status:'completed'}}}}),'Partially Signed');
        ''')


if __name__ == '__main__':
    unittest.main()
