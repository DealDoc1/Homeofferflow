const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('index.html', 'utf8');
const start = source.indexOf('async function logOfferEvent(');
const end = source.indexOf('async function recordCurrentLegalAcceptance', start);
assert.ok(start >= 0 && end > start, 'offer-event helper is present');
const helper = source.slice(start, end);

function load(fetch, accessToken = 'session-token') {
  const context = {
    hofAuth: { session: accessToken ? { access_token: accessToken } : null },
    state: { data: { _hofOfferId: 'saved-offer-id' } },
    AbortSignal,
    fetch,
    console: { warn() {} },
  };
  vm.runInNewContext(`${helper}\nglobalThis.logOfferEvent = logOfferEvent;`, context);
  return { context, log: context.logOfferEvent };
}

async function run() {
  let request;
  const { log } = load(async (...args) => {
    request = args;
    return { ok: true };
  });
  assert.equal(await log(null, 'resume_clicked', 'Draft', 'Resumed offer.', { surface: 'dashboard' }), true);
  assert.equal(request[0], '/api/admin-dashboard');
  assert.equal(request[1].headers.Authorization, 'Bearer session-token');
  assert.deepEqual(JSON.parse(request[1].body), {
    action: 'record_offer_event', offerId: 'saved-offer-id',
    eventType: 'resume_clicked', status: 'Draft', message: 'Resumed offer.',
    metadata: { surface: 'dashboard' },
  });

  let unauthenticatedRequests = 0;
  const signedOut = load(async () => { unauthenticatedRequests++; return { ok: true }; }, null);
  assert.equal(await signedOut.log(null, 'resume_clicked'), false);
  assert.equal(unauthenticatedRequests, 0);

  const failure = load(async () => ({ ok: false }));
  assert.equal(await failure.log(null, 'resume_clicked'), false);

  const queueStart = source.indexOf('  let checkoutReturnEventInFlight');
  const queueEnd = source.indexOf('  async function logOfferEvent(', queueStart);
  assert.ok(queueStart >= 0 && queueEnd > queueStart);
  const first = JSON.stringify({result: 'success', queuedAt: 1});
  const second = JSON.stringify({result: 'cancelled', queuedAt: 2});
  const storage = new Map([['return', first]]);
  let calls = 0;
  let confirmSave;
  const queue = {
    SUBSCRIPTION_CHECKOUT_RETURN_KEY: 'return',
    SUBSCRIPTION_CHECKOUT_SOURCE_KEY: 'source',
    subscriptionCheckoutSource: value => value,
    hofAuth: {session: {user: {id: 'agent'}}},
    sessionStorage: {getItem: key => storage.get(key), removeItem: key => storage.delete(key)},
    logOfferEvent: () => { calls++; return new Promise(resolve => { confirmSave = resolve; }); },
    console: {warn() {}},
  };
  vm.runInNewContext(source.slice(queueStart, queueEnd), queue);
  const pending = queue.flushSubscriptionCheckoutReturnEvent();
  assert.equal(await queue.flushSubscriptionCheckoutReturnEvent(), false);
  assert.equal(calls, 1);
  storage.set('return', second);
  confirmSave(true);
  assert.equal(await pending, true);
  assert.equal(storage.get('return'), second);
  const next = queue.flushSubscriptionCheckoutReturnEvent();
  confirmSave(true);
  assert.equal(await next, true);
  assert.equal(storage.has('return'), false);
}

run().then(() => process.stdout.write('✔ offer event client sends owner-scoped authenticated API requests and remains best effort\n'));
