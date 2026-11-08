from pathlib import Path
import subprocess
import unittest


class MyOffersRefreshRecoveryTests(unittest.TestCase):
    def test_refresh_preserves_results_and_discards_stale_responses(self):
        html = (Path(__file__).resolve().parents[1] / "index.html").read_text()
        start = html.index("  const HOF_OFFER_WORKSPACE_PAGE_SIZE")
        end = html.index("  function formatOfferDate", start)
        setup = """
const assert = require('node:assert/strict');
const list = {innerHTML: 'current'};
const notice = {hidden: true};
const document = {getElementById: id => ({myOffersList:list, myOffersRefreshNotice:notice})[id]};
const hofAuth = {session:{user:{id:'first'}}, myOffers:[{id:'current'}], myOffersNextOffset:25};
const pending = [];
const query = {
  from:()=>query, select:()=>query, eq:()=>query, is:()=>query, order:()=>query,
  range:()=>query, abortSignal:signal=>new Promise(resolve=>{
    pending.push(resolve);
    signal.addEventListener('abort',()=>resolve({error:signal.reason}),{once:true});
  })
};
const getSupabaseClient = () => query;
const renderMyOffers = offers => offers.map(offer=>offer.id).join(',');
const window = {};
let expire;
const setTimeout = (callback, delay) => { assert.equal(delay,60000); expire=callback; return callback; };
const clearTimeout = callback => { if (expire===callback) expire=null; };
"""
        scenario = """
(async () => {
  const failing = loadMyOffers();
  pending[0]({error:new Error('fictional failure')});
  await failing;
  assert.equal(list.innerHTML,'current');
  assert.equal(hofAuth.myOffersNextOffset,25);
  assert.equal(notice.hidden,false);

  const stale = loadMyOffers();
  const retry = loadMyOffers();
  pending[2]({data:[{id:'updated'}]});
  await retry;
  pending[1]({error:new Error('older failure')});
  await stale;
  assert.equal(list.innerHTML,'updated');
  assert.equal(notice.hidden,true);

  const previousAccount = loadMyOffers();
  hofAuth.session = {user:{id:'second'}};
  window.__hofAccountProfileEpoch = 1;
  list.innerHTML = 'new account';
  pending[3]({data:[{id:'old account'}]});
  await previousAccount;
  assert.equal(list.innerHTML,'new account');

  const stalled = window.loadOlderOffers();
  expire();
  await stalled;
  assert.equal(hofAuth.myOffersLoadMoreError,true);
  assert.equal(hofAuth.myOffersNextOffset,1);
  assert.equal(expire,null);
  const retryOlder = window.loadOlderOffers();
  pending[5]({data:[{id:'older'}]});
  await retryOlder;
  assert.equal(list.innerHTML,'updated,older');
})().catch(error=>{console.error(error);process.exitCode=1;});
"""
        result = subprocess.run(
            ["node", "-"], input=setup + html[start:end] + scenario,
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
