'use strict';

const assert = require('node:assert/strict');
const { webcrypto } = require('node:crypto');
const fs = require('node:fs');
const test = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync('index.html', 'utf8');
const primer = html.split('<script id="hof-native-offer-link-primer">')[1].split('</script>')[0];
const runtime = html.slice(html.indexOf('  const NATIVE_OFFER_SIGN_IN_RETURN'), html.indexOf('function routeAfterMagicLinkIfNeeded('));
const id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const owner = { id: 'owner', email: 'owner@example.test' };
const returnKey = 'hof_native_offer_sign_in_return';

function setup(hash, { user = owner, storage = new Map(), now = 1000000 } = {}) {
  const calls = [];
  const elements = new Map();
  const element = name => {
    if (!elements.has(name)) elements.set(name, {
      hidden: true, textContent: '', classList: { contains: () => true },
      focus() { calls.push(['focus', name]); }
    });
    return elements.get(name);
  };
  const window = {
    __hofAccountProfileEpoch: 1,
    announceWorkspaceStatus: message => calls.push(['status', message])
  };
  const hofAuth = { profileReady: true, session: user ? { user } : null };
  const context = vm.createContext({
    window, hofAuth, URLSearchParams, TextEncoder, crypto: webcrypto,
    Date: { now: () => now },
    location: { hash, pathname: '/', search: '?fixture=1' },
    history: { replaceState: (_state, _title, url) => calls.push(['replace', url]) },
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value),
      removeItem: key => storage.delete(key)
    },
    document: { getElementById: element },
    closeAuthModal() {},
    openAccountDashboard: async ({ tab }) => calls.push(['dashboard', tab]),
    startAccountOffer: () => calls.push(['start']),
    resumeOffer: (offerId, _retry, options) => calls.push(['resume', offerId, options.openPreparedDetails]),
    reuseOfferTerms: offerId => calls.push(['reuse', offerId]),
    duplicateOffer: (offerId, _retry, openCopy) => calls.push(['duplicate', offerId, openCopy]),
    beginOfferOpenRequest: () => ({ isCurrent: () => true }),
    getOfferById: async () => ({ property_address: '42 Fictional Way' })
  });
  vm.runInContext(primer + '\n' + runtime, context);
  return { context, elements, calls, storage, hofAuth, window };
}

test('links select the existing start, resume and reuse actions after authentication', async () => {
  for (const [hash, expected] of [
    ['#hof_mobile_start_offer=1', ['start']],
    ['#hof_resume_offer=' + id.toUpperCase(), ['resume', id, true]],
    ['#hof_mobile_reuse_terms=' + id, ['reuse', id]]
  ]) {
    const { calls, context } = setup(hash);
    assert.equal(await context.openNativeOfferLinkAfterAuth(false), true);
    assert.equal(await context.openNativeOfferLinkAfterAuth(false), false);
    assert.deepEqual(calls, [['replace', '/?fixture=1'], ['dashboard', 'offers'], expected]);
  }
});

test('ignores malformed, repeated and ambiguous links without touching Supabase callbacks', async () => {
  for (const hash of [
    '#hof_resume_offer=bogus', '#hof_mobile_start_offer=0',
    '#hof_resume_offer=' + id + '&hof_resume_offer=' + id,
    '#hof_resume_offer=' + id + '&hof_mobile_start_offer=1',
    '#access_token=fixture&refresh_token=fixture&type=magiclink'
  ]) {
    const { calls, context } = setup(hash);
    assert.equal(await context.openNativeOfferLinkAfterAuth(false), false);
    assert.ok(calls.every(([action]) => action === 'replace'));
    if (hash.includes('access_token')) assert.deepEqual(calls, []);
  }
});

test('a saved sign-in return is account-bound, expiring, callback-only and consumed once', async () => {
  const start = setup('#hof_resume_offer=' + id, { user: null });
  await start.context.rememberNativeOfferLinkForSignIn('OWNER@example.test');
  assert.ok(start.storage.has(returnKey));
  assert.ok(!start.storage.get(returnKey).includes(owner.email));

  const unrelated = setup('', { user: {id: 'other', email: 'other@example.test'}, storage: start.storage });
  assert.equal(await unrelated.context.openNativeOfferLinkAfterAuth(true), false);
  assert.ok(start.storage.has(returnKey));

  const callback = setup('', { storage: start.storage });
  assert.equal(await callback.context.openNativeOfferLinkAfterAuth(false), false);
  assert.equal(await callback.context.openNativeOfferLinkAfterAuth(true), true);
  assert.equal(await callback.context.openNativeOfferLinkAfterAuth(true), false);
  assert.deepEqual(callback.calls, [['dashboard', 'offers'], ['resume', id, true]]);

  await start.context.rememberNativeOfferLinkForSignIn(owner.email);
  const expired = setup('', {storage: start.storage, now: 2000000});
  assert.equal(await expired.context.openNativeOfferLinkAfterAuth(true), false);
  assert.ok(!start.storage.has(returnKey));
});

test('duplicate prompts only after an owned offer loads and a click writes once', async () => {
  const denied = setup('#hof_mobile_duplicate_offer=' + id);
  denied.context.getOfferById = async () => null;
  assert.equal(await denied.context.openNativeOfferLinkAfterAuth(false), true);
  assert.ok(denied.calls.some(([action]) => action === 'status'));
  assert.ok(!denied.elements.has('nativeOfferDuplicateConfirm'));

  const allowed = setup('#hof_mobile_duplicate_offer=' + id);
  await allowed.context.openNativeOfferLinkAfterAuth(false);
  const confirm = allowed.elements.get('nativeOfferDuplicateConfirm');
  assert.ok(!allowed.calls.some(([action]) => action === 'duplicate'));
  confirm.onclick();
  assert.equal(confirm.onclick, null);
  assert.deepEqual(allowed.calls.filter(([action]) => action === 'duplicate'), [['duplicate', id, true]]);
});

test('changing the account before confirmation blocks a copy', async () => {
  const { calls, context, elements, hofAuth } = setup('#hof_mobile_duplicate_offer=' + id);
  await context.openNativeOfferLinkAfterAuth(false);
  hofAuth.session.user = { id: 'other' };
  elements.get('nativeOfferDuplicateConfirm').onclick();
  assert.ok(!calls.some(([action]) => action === 'duplicate'));
  assert.equal(elements.get('nativeOfferDuplicateDetails').textContent, '');
});
