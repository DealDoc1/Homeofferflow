from pathlib import Path
import subprocess
import unittest


class MyOffersRefreshRecoveryTests(unittest.TestCase):
    def test_refresh_preserves_results_and_discards_stale_responses(self):
        html = (Path(__file__).resolve().parents[1] / "index.html").read_text()
        start = html.index("  const HOF_OFFER_WORKSPACE_PAGE_SIZE")
        end = html.index("  function formatOfferDate", start)
        api_start = html.index("  root.hofLoadAgentOfferHistory")
        api_end = html.index("  function bucketForOffer", api_start)
        setup = """
const assert = require('node:assert/strict');
const list = {innerHTML: 'current'};
const notice = {hidden: true};
const document = {getElementById: id => ({myOffersList:list, myOffersRefreshNotice:notice})[id]};
const hofAuth = {session:{user:{id:'first'},access_token:'token-first'}, myOffers:[{id:'current'}], myOffersNextOffset:25};
const pending = [];
const retryButton = {
  textContent: 'Retry offers',
  attrs: new Map(),
  getAttribute(name) { return this.attrs.get(name); },
  setAttribute(name, value) { this.attrs.set(name, value); },
  removeAttribute(name) { this.attrs.delete(name); }
};
const renderMyOffers = offers => offers.map(offer=>offer.id).join(',');
const window = {hofAuth, refreshSignWellStatus() { assert.fail('Offer retry must not call SignWell'); }};
const root = window;
const fetch=(url,{headers,signal})=>{
  const params = new URLSearchParams(url.split('?')[1]);
  assert.equal(params.get('scope'),'agent_offer_history');
  assert.equal(params.get('limit'),'25');
  assert.equal(headers.Authorization,'Bearer '+hofAuth.session.access_token);
  const offset = Number(params.get('offset'));
  return new Promise((resolve,reject)=>{
    pending.push(({data,error})=> {
      if (error) return reject(error);
      resolve({ok:true,json:async()=>({offers:data,offset,nextOffset:offset+data.length,hasMore:data.length===25})});
    });
    signal.addEventListener('abort',()=>reject(signal.reason),{once:true});
  });
};
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
  const retry = window.hofRetryOfferHistory(retryButton);
  assert.equal(retryButton.getAttribute('aria-disabled'), 'true');
  await window.hofRetryOfferHistory(retryButton);
  assert.equal(pending.length, 3);
  pending[2]({data:[{id:'updated'}]});
  await retry;
  assert.equal(retryButton.getAttribute('aria-disabled'), undefined);
  assert.equal(retryButton.textContent, 'Retry offers');
  pending[1]({error:new Error('older failure')});
  await stale;
  assert.equal(list.innerHTML,'updated');
  assert.equal(notice.hidden,true);

  const previousAccount = loadMyOffers();
  hofAuth.session = {user:{id:'second'},access_token:'token-second'};
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
            ["node", "-"], input=setup + html[start:end] + html[api_start:api_end] + scenario,
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_paging_keeps_focus_and_ignores_repeated_activation(self):
        html = (Path(__file__).resolve().parents[1] / "index.html").read_text()
        start = html.index("  const HOF_OFFER_WORKSPACE_PAGE_SIZE")
        end = html.index("  function formatOfferDate", start)
        setup = """
const assert = require('node:assert/strict');
const pending = [];
const hofAuth = {
  session: {user: {id: 'agent'}, access_token: 'fictional'},
  myOffers: [{id: 'first'}], myOffersHasMore: true, myOffersNextOffset: 25
};
const window = {hofLoadAgentOfferHistory: offset => {
  assert.equal(offset, hofAuth.myOffersNextOffset);
  return new Promise((resolve, reject) => pending.push({resolve, reject}));
}};
const renderMyOffers = () => '';
const body = {};
const other = {};
function control(text = '') {
  return {textContent: text, attrs: {},
    setAttribute(name, value) { this.attrs[name] = value; },
    removeAttribute(name) { delete this.attrs[name]; },
    focus() { document.activeElement = this; }
  };
}
let button = control('Load 25 older offers');
let summary = control();
const list = {
  set innerHTML(_) {
    if (document.activeElement === button) document.activeElement = body;
    button = hofAuth.myOffersHasMore
      ? control(hofAuth.myOffersLoadMoreError ? 'Retry loading older offers' : 'Load 25 older offers')
      : null;
    summary = control();
  },
  querySelector(selector) {
    return selector === '#loadOlderOffersButton' ? button : summary;
  }
};
const document = {
  activeElement: body,
  getElementById: id => ({myOffersList: list, loadOlderOffersButton: button})[id]
};
"""
        scenario = """
(async () => {
  button.focus();
  const initial = button;
  const fail = window.loadOlderOffers();
  assert.equal(initial.attrs['aria-disabled'], 'true');
  assert.equal(document.activeElement, initial);
  await window.loadOlderOffers();
  assert.equal(pending.length, 1);
  pending[0].reject(new Error('fictional connection failure'));
  await fail;
  assert.equal(document.activeElement, button);
  assert.equal(button.textContent, 'Retry loading older offers');
  assert.equal(button.attrs['aria-disabled'], undefined);

  const retry = window.loadOlderOffers();
  pending[1].resolve({offers: [{id: 'older'}], hasMore: true, nextOffset: 26});
  await retry;
  assert.equal(document.activeElement, button);
  assert.equal(button.textContent, 'Load 25 older offers');

  const moved = window.loadOlderOffers();
  document.activeElement = other;
  pending[2].resolve({offers: [{id: 'older-still'}], hasMore: true, nextOffset: 27});
  await moved;
  assert.equal(document.activeElement, other);

  button.focus();
  const final = window.loadOlderOffers();
  pending[3].resolve({offers: [{id: 'last'}], hasMore: false, nextOffset: 28});
  await final;
  assert.equal(button, null);
  assert.equal(document.activeElement, summary);
  assert.deepEqual(hofAuth.myOffers.map(offer => offer.id), ['first', 'older', 'older-still', 'last']);
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
        result = subprocess.run(
            ["node", "-"], input=setup + html[start:end] + scenario,
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
