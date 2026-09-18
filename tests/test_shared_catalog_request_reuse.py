"""Run the actual catalog loader in Node; no production requests or keys."""
from pathlib import Path
import subprocess
import unittest


HTML = (Path(__file__).resolve().parents[1] / 'index.html').read_text()
START = HTML.index('  let approvedCatalogCache = null;')
END = HTML.index('  // Keep a background form-library failure actionable', START)
LOADER = HTML[START:END]


class SharedCatalogRequestReuseTests(unittest.TestCase):
    def run_js(self, scenario):
        setup = '''
          const assert = require('node:assert/strict');
          const root = {hofAuth:{session:{access_token:'token-a',user:{id:'agent-a'}}}};
          let clock = 1000;
          const Date = {now:()=>clock};
          const requests = [];
          const rows = [{form_code:'TXR-1507',source_revision:'v1'},
                        {form_code:'TXR-1501',source_revision:'v1'}];
          const success = (sources=rows) => ({ok:true,json:async()=>({sources})});
          let respond = async () => success();
          const fetch = (url, options) => {
            requests.push({url,options});
            return respond();
          };
        '''
        script = setup + LOADER + '\n(async()=>{\n' + scenario + '\n})().catch(e=>{console.error(e);process.exitCode=1});'
        result = subprocess.run(['node', '-e', script], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_twelve_simultaneous_form_checks_share_one_authenticated_request(self):
        self.run_js('''
          const results = await Promise.all(Array.from({length:12},()=>root.hofLoadApprovedBrokerageSource('TXR-1507')));
          assert.equal(requests.length,1);
          assert.equal(results.length,12);
          assert.ok(results.every(row=>row.form_code==='TXR-1507'));
          assert.equal(requests[0].options.headers.Authorization,'Bearer token-a');
          await root.hofLoadApprovedFormCatalog();
          assert.equal(requests.length,1);
        ''')

    def test_success_expires_and_consumer_edits_do_not_pollute_other_cards(self):
        self.run_js('''
          const first = await root.hofLoadApprovedFormCatalog();
          first.reverse(); first[0].source_revision='changed';
          const second = await root.hofLoadApprovedFormCatalog();
          assert.equal(second[0].form_code,'TXR-1507');
          assert.equal(second[1].source_revision,'v1');
          clock += 30001;
          await root.hofLoadApprovedFormCatalog();
          assert.equal(requests.length,2);
        ''')

    def test_no_session_never_sends_an_undefined_bearer(self):
        self.run_js('''
          root.hofAuth.session=null;
          assert.deepEqual(await root.hofLoadApprovedFormCatalog(),[]);
          assert.equal(await root.hofLoadApprovedBrokerageSource('TXR-1507'),null);
          assert.equal(requests.length,0);
        ''')

    def test_failed_or_malformed_responses_are_not_cached_as_available_forms(self):
        for response in ("{ok:false,json:async()=>({error:'private backend diagnostic'})}",
                         "{ok:true,json:async()=>({sources:null})}",
                         "{ok:true,json:async()=>{throw new Error('bad JSON')}}"):
            with self.subTest(response=response):
                self.run_js('''
                  respond=async()=>(''' + response + ''');
                  await assert.rejects(root.hofLoadApprovedFormCatalog(), /couldn’t load the available forms/);
                  respond=async()=>success();
                  assert.equal((await root.hofLoadApprovedFormCatalog()).length,2);
                  assert.equal(requests.length,2);
                ''')

    def test_refresh_or_account_change_never_reuses_the_previous_session(self):
        self.run_js('''
          await root.hofLoadApprovedFormCatalog();
          root.hofAuth.session.access_token='refreshed';
          await root.hofLoadApprovedFormCatalog();
          assert.equal(requests.length,2);
          root.hofAuth.session.user.id='agent-b';
          await root.hofLoadApprovedFormCatalog();
          assert.equal(requests.length,3);
        ''')

    def test_sign_out_rejects_a_late_response_and_explicit_clear_drops_cache(self):
        self.run_js('''
          let finish;
          respond=()=>new Promise(resolve=>finish=resolve);
          const pending=root.hofLoadApprovedFormCatalog();
          root.hofAuth.session=null;
          root.hofClearApprovedFormCatalog();
          finish(success());
          await assert.rejects(pending,/sign-in changed/);
          root.hofAuth.session={access_token:'token-a',user:{id:'agent-a'}};
          respond=async()=>success();
          await root.hofLoadApprovedFormCatalog();
          assert.equal(requests.length,2);
        ''')

    def test_old_request_failure_cannot_clear_a_new_accounts_successful_cache(self):
        self.run_js('''
          let fail;
          respond=()=>new Promise((resolve,reject)=>fail=reject);
          const pending=root.hofLoadApprovedFormCatalog();
          const rejected=assert.rejects(pending,/connection failed/);
          root.hofAuth.session={access_token:'token-b',user:{id:'agent-b'}};
          respond=async()=>success([{form_code:'TXR-1508'}]);
          await root.hofLoadApprovedFormCatalog();
          fail(new Error('connection failed'));
          await rejected;
          assert.equal((await root.hofLoadApprovedFormCatalog())[0].form_code,'TXR-1508');
          assert.equal(requests.length,2);
        ''')

    def test_all_three_catalog_consumers_use_the_same_loader(self):
        self.assertEqual(HTML.count("fetch('/api/admin-dashboard?scope=approved_brokerage_sources'"), 1)
        self.assertIn('const sources = await root.hofLoadApprovedFormCatalog();', HTML)
        self.assertIn('async function approvedSources() {\n    return root.hofLoadApprovedFormCatalog();', HTML)
        self.assertNotIn('localStorage', LOADER)
        self.assertNotIn('sessionStorage', LOADER)
