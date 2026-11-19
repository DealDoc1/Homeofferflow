'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync('index.html', 'utf8');
const sync = html.slice(html.indexOf('  let signingSyncAccount;'), html.indexOf('  root.hofReuseTermsFromMostRecentOffer'));
const refresh = html.slice(html.indexOf('  async function refreshSignWellStatus('), html.indexOf('  window.refreshSignWellStatus = refreshSignWellStatus;'));

const offer = (id, status = 'Sent', day = 1) => ({
  id, status, signwell_document_id: 'fictional', created_at: new Date(2026, 0, day).toISOString()
});

function setup(offers = []) {
  const status = { textContent: '' };
  const calls = [];
  const hofAuth = { session: { user: { id: 'first' }, access_token: 'fixture' }, myOffers: offers };
  const root = {
    hofAuth,
    __hofAccountProfileEpoch: 0,
    async loadMyOffers() { calls.push('list'); return hofAuth.myOffers; },
    async refreshSignWellStatus(id) { calls.push(id); return true; }
  };
  const document = { getElementById: id => id === 'myOffersSigningSyncStatus' ? status : null };
  const context = vm.createContext({
    root, window: root, document, console: { warn() {}, error() {} }, hofAuth,
    getOfferBestStatus: row => row.status, rerender() {},
    AbortController, setTimeout, clearTimeout
  });
  vm.runInContext(sync + '\n' + refresh + '\nthis.refreshSignWellStatus = refreshSignWellStatus;', context);
  return { root, status, calls, context };
}

test('the first visit loads offers before syncing and a manual click joins the automatic batch', async () => {
  const { root, status, calls } = setup();
  let finishLoad;
  root.loadMyOffers = () => {
    calls.push('list');
    if (calls.length === 1) return new Promise(resolve => { finishLoad = resolve; });
    return Promise.resolve(root.hofAuth.myOffers);
  };
  const automatic = root.hofRefreshOfferWorkspace({ automatic: true });
  const manual = root.hofRefreshOfferWorkspace();
  const repeated = root.hofRefreshOfferWorkspace();
  assert.equal(status.textContent, 'Checking signing status…');
  root.hofAuth.myOffers = [offer('waiting', 'Awaiting Buyer Signature')];
  finishLoad(root.hofAuth.myOffers);
  await Promise.all([automatic, manual, repeated]);
  assert.deepEqual(calls, ['list', 'waiting', 'list']);
  assert.match(status.textContent, /Checked signing status for 1 offer/);
});

test('a manual batch states partial failures and preserves the limit and oldest-first order', async () => {
  const offers = Array.from({ length: 12 }, (_, index) => offer('offer-' + (12 - index), 'Created', 12 - index));
  const { root, status, calls } = setup([...offers, offer('done', 'Complete')]);
  root.refreshSignWellStatus = async (id, _button, skipReload, suppressAlert) => {
    calls.push(id);
    assert.equal(skipReload, true);
    assert.equal(suppressAlert, true);
    return id !== 'offer-3';
  };
  await root.hofRefreshOfferWorkspace();
  assert.deepEqual(calls, [...Array.from({ length: 10 }, (_, n) => 'offer-' + (n + 1)), 'list']);
  assert.match(status.textContent, /Checked signing status for 9 offers\. Couldn’t check 1 offer\. Try syncing again/);
});

test('a failed history load shows recovery rather than claiming the queue is empty', async () => {
  const { root, status } = setup();
  root.loadMyOffers = async () => { root.hofAuth.myOffersRefreshError = true; return []; };
  await root.hofRefreshOfferWorkspace();
  assert.equal(status.textContent, 'The offer list couldn’t refresh. Try syncing again.');
  root.hofAuth.myOffersRefreshError = false;
  root.loadMyOffers = async () => [];
  await root.hofRefreshOfferWorkspace();
  assert.equal(status.textContent, 'No loaded offers need a signing status check.');
});

test('account changes suppress late results and reset the automatic cooldown', async () => {
  const { root, status, calls } = setup([offer('first-offer')]);
  let finish;
  root.refreshSignWellStatus = (id) => {
    calls.push(id);
    if (id === 'first-offer') return new Promise(resolve => { finish = resolve; });
    return Promise.resolve(true);
  };
  const first = root.hofRefreshOfferWorkspace({ automatic: true });
  const joined = root.hofRefreshOfferWorkspace();
  root.hofAuth.session.user.id = 'second';
  root.__hofAccountProfileEpoch++;
  root.hofAuth.myOffers = [offer('second-offer')];
  status.textContent = '';
  await root.hofRefreshOfferWorkspace({ automatic: true });
  await root.hofRefreshOfferWorkspace({ automatic: true });
  finish(false);
  await Promise.all([first, joined]);
  assert.deepEqual(calls, ['first-offer', 'second-offer', 'list']);
  assert.equal(status.textContent, '');
});

test('the actual per-offer handler distinguishes a confirmed provider result from a failure', async () => {
  const { context, calls } = setup([offer('active')]);
  context.fetch = async () => ({ ok: true, json: async () => ({ status: 'Sent' }) });
  assert.equal(await context.refreshSignWellStatus('active', null, true, true), true);
  context.fetch = async () => ({ ok: false, json: async () => ({ error: 'fixture failure' }) });
  assert.equal(await context.refreshSignWellStatus('active', null, true, true), false);
  assert.deepEqual(calls, []);
});
