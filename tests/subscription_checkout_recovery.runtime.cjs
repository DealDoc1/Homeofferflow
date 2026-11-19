const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {test} = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
function cut(start, end) {
  const first = html.indexOf(start);
  const last = html.indexOf(end, first + 1);
  assert.ok(first >= 0 && last > first, start);
  return html.slice(first, last);
}
const code = [
  cut('  const SUBSCRIPTION_CHECKOUT_SOURCE_KEY', '  function checkSubscriptionReturn()'),
  cut("  async function recordCurrentLegalAcceptance(", '  function subscriptionLegalConsentModal()'),
  cut('  async function ensureCurrentLegalAcceptanceForSubscription()', '  async function preflightUsage('),
].join('\n');

function fixture() {
  const calls = {legal: [], record: [], checkout: [], notices: [], events: [], timeouts: []};
  const callbacks = {};
  const session = {user: {id: 'first-account', email: 'agent@example.test'}, access_token: 'fixture'};
  const store = new Map();
  const window = {__hofAccountProfileEpoch: 0, location: {href: 'original'},
    addEventListener: (name, listener) => {callbacks[name] = listener;}};
  const state = {accepted: false, checkError: null, saveError: null, consent: true, promptCount: 0};
  let legalLookup;
  const client = {
    from(table) {
      assert.equal(table, 'hof_legal_acceptances');
      return {
        select: () => legalLookup,
        insert: data => ({
          abortSignal: signal => {
            calls.record.push({signal, data});
            return Promise.resolve({error: state.saveError});
          },
        }),
      };
    },
  };
  const filters = [];
  legalLookup = {
    eq: (key, value) => {filters.push([key, value]); return legalLookup;},
    limit: () => legalLookup,
    abortSignal: signal => {
      calls.legal.push({signal, filters: filters.splice(0)});
      return state.legalResponse || Promise.resolve({
        data: state.accepted ? [{policy_version: 'fixture-policy'}] : [], error: state.checkError,
      });
    },
  };
  const context = vm.createContext({
    window, hofAuth: {session}, LEGAL_POLICY_VERSION: 'fixture-policy',
    AbortController, AbortSignal: {timeout: milliseconds => {
      calls.timeouts.push(milliseconds);
      return {milliseconds};
    }},
    setTimeout: () => 1, clearTimeout() {},
    console: {warn() {}, error() {}},
    setSubscriptionActionStatus: message => calls.notices.push(message),
    setSubscriptionActionBusy: message => calls.notices.push(message),
    logOfferEvent: (...args) => calls.events.push(args[1]),
    getSupabaseClient: () => client,
    subscriptionLegalConsentModal: async () => {state.promptCount++; return state.consent;},
    sessionStorage: {
      getItem: key => store.get(key),
      setItem: (key, value) => store.set(key, value),
      removeItem: key => store.delete(key),
    },
    fetch: async (url, options) => {
      if (url.includes('legal_acceptance_status')) {
        calls.legal.push(options);
        if (state.legalResponse) await state.legalResponse;
        if (state.checkError) throw state.checkError;
        return {ok: true, json: async () => ({acceptedCurrent: state.accepted})};
      }
      if (url === '/api/admin-dashboard') {
        calls.record.push(options);
        if (state.saveError) throw state.saveError;
        return {ok: true, json: async () => ({ok: true, accepted: true, policyVersion: 'fixture-policy'})};
      }
      assert.equal(url, '/api/create-subscription-checkout');
      calls.checkout.push(options);
      return state.checkoutResponse || {ok: true, json: async () => ({url: 'https://checkout.stripe.test/session'})};
    },
  });
  vm.runInContext(code, context);
  return {calls, callbacks, window, context, state, store};
}

test('an unavailable terms check has a time limit and can be retried without logging a Stripe failure', async () => {
  const {calls, window, context, state} = fixture();
  state.checkError = new Error('Internal fixture diagnostic');
  await context.startSubscriptionCheckout();
  assert.equal(state.promptCount, 0);
  assert.deepEqual(calls.checkout, []);
  assert.deepEqual(calls.events, []);
  assert.match(calls.notices.at(-1), /check your acceptance of the current terms/);
  assert.ok(!calls.notices.at(-1).includes('Internal fixture diagnostic'));
  assert.deepEqual(calls.timeouts, [15000]);
  assert.equal(window.__hofSubscriptionCheckoutInFlight, false);
  state.checkError = null;
  state.accepted = true;
  await context.startSubscriptionCheckout();
  assert.equal(calls.checkout.length, 1);
});

test('new acceptance must be saved before opening checkout and storage is optional', async () => {
  const {calls, context, state} = fixture();
  context.sessionStorage.getItem = context.sessionStorage.setItem = () => {throw Error('storage blocked');};
  state.consent = false;
  await context.startSubscriptionCheckout();
  assert.equal(state.promptCount, 1);
  assert.deepEqual(calls.record, []);
  state.consent = true;
  state.saveError = new Error('network failure');
  await context.startSubscriptionCheckout();
  assert.match(calls.notices.at(-1), /could not save your legal acceptance/);
  assert.deepEqual(calls.checkout, []);
  state.saveError = null;
  await context.startSubscriptionCheckout();
  assert.equal(calls.record.length, 2);
  assert.equal(calls.checkout.length, 1);
});

test('a late checkout response from the prior account cannot redirect after an account switch', async () => {
  const {calls, window, context, state} = fixture();
  let release;
  state.accepted = true;
  state.checkoutResponse = new Promise(resolve => {release = resolve;});
  const attempt = context.startSubscriptionCheckout();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(calls.checkout.length, 1);
  window.__hofAccountProfileEpoch++;
  context.hofAuth.session = {user: {id: 'other-account'}, access_token: 'other-fixture'};
  release({ok: true, json: async () => ({url: 'https://checkout.stripe.test/stale'})});
  await attempt;
  assert.equal(window.location.href, 'original');
  assert.equal(window.__hofSubscriptionCheckoutInFlight, false);
});

test('restoring the page from the browser cache reopens the checkout controls', async () => {
  const {calls, callbacks, window, context, state} = fixture();
  state.accepted = true;
  await context.startSubscriptionCheckout();
  await context.startSubscriptionCheckout();
  assert.equal(calls.checkout.length, 1);
  callbacks.pageshow({persisted: true});
  assert.equal(window.__hofSubscriptionCheckoutInFlight, false);
  assert.match(calls.notices.at(-1), /back from checkout/);
  await context.startSubscriptionCheckout();
  assert.equal(calls.checkout.length, 2);
});
