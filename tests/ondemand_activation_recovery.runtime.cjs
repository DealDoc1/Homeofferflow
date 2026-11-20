const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'ondemand.html'), 'utf8');
const code = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const session = id => ({user: {id, email: `${id}@example.com`}, access_token: `fictional-${id}`});
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return {promise, resolve}; };
async function settle() { for (let i = 0; i < 30; i++) await new Promise(r => setImmediate(r)); }
function fixture({saved = session('a'), savedRead, failRead = false, access = async () => false, search = '?checkout=success', eventResponseOk = true} = {}) {
  const elements = new Map();
  const el = id => {
    if (!elements.has(id)) elements.set(id, {style: {}, textContent: '', innerHTML: '', checked: false,
      hidden: false, disabled: false, listeners: {}, classList: {add() {}, remove() {}},
      addEventListener(name, fn) { this.listeners[name] = fn; }, appendChild() {}, setAttribute() {}, focus() {}, checkValidity() { return true; }});
    return elements.get(id);
  };
  const timers = new Map();
  let listener; const calls = []; const apiEvents = []; let directWrites = 0; const storage = new Map();
  const auth = {
    onAuthStateChange(fn) { listener = fn; },
    async getSession() { if (failRead) throw Error('temporary read failure'); return savedRead ? await savedRead.promise : {data: {session: saved}}; },
  };
  const location = {origin: 'https://www.homeofferflow.com', pathname: '/ondemand', search, href: `https://www.homeofferflow.com/ondemand${search}`, assign() { throw Error('unexpected navigation'); }};
  const context = {URL, URLSearchParams, Date, AbortController, navigator: {userAgent: 'desktop'}, console: {warn() {}},
    document: {referrer: '', title: 'HomeOfferFlow', getElementById: el, documentElement: {style: {setProperty() {}}}, createElement: () => ({style: {}})},
    window: {location, history: {replaceState() {}}, addEventListener() {}, supabase: {createClient: () => ({auth, from: () => ({insert: async () => { directWrites++; return {error: null}; }})})}},
    sessionStorage: {getItem: k => storage.get(k), setItem: (k,v) => storage.set(k,v)},
    setTimeout(fn, ms) {
      const id = Symbol();
      if (ms === 1000) queueMicrotask(fn);
      else timers.set(id, {fn, ms});
      return id;
    },
    clearTimeout: id => timers.delete(id),
    fetch: async (url, options) => {
      if (url.includes('status=access')) { calls.push(options.headers.Authorization); return {ok: true, json: async () => ({access: await access(options.headers.Authorization, options.signal)})}; }
      if (url === '/api/admin-dashboard') {
        apiEvents.push({headers: options.headers, body: JSON.parse(options.body)});
        return {ok: eventResponseOk, json: async () => ({ok: eventResponseOk})};
      }
      return {ok: true, json: async () => ({brokerage: {}})};
    },
  };
  vm.runInNewContext(code, context);
  return {el, calls, apiEvents, timers, get directWrites() { return directWrites; }, emit: value => listener('SIGNED_IN', value)};
}
test('OnDemand checkout returns record funnel events through the authenticated API', async () => {
  const f = fixture({search: '?checkout=cancelled'}); await settle();
  assert.equal(f.apiEvents.length, 2);
  assert.equal(f.apiEvents[0].headers.Authorization, 'Bearer fictional-a');
  assert.equal(f.apiEvents[0].body.action, 'record_offer_event');
  assert.equal(f.apiEvents[0].body.offerId, null);
  assert.equal(f.apiEvents[0].body.eventType, 'subscription_checkout_returned');
  assert.equal(f.apiEvents[0].body.status, 'cancelled');
  assert.equal(f.apiEvents[0].body.metadata.source, 'ondemand');
  assert.equal(f.apiEvents[1].body.eventType, 'subscription_checkout_recovery_shown');
  assert.equal(f.apiEvents[1].body.status, 'shown');
  assert.equal(f.directWrites, 0);
});
test('a funnel API failure does not block the canceled-checkout recovery path', async () => {
  const f = fixture({search: '?checkout=cancelled', eventResponseOk: false}); await settle();
  assert.equal(f.apiEvents.length, 2);
  assert.equal(f.el('checkoutRecovery').style.display, 'block');
  assert.equal(f.directWrites, 0);
});
test('a success URL never exposes workspace links before server access confirmation', async () => {
  const pending = deferred(); const f = fixture({access: () => pending.promise}); await settle();
  assert.equal(f.el('workspaceButton').style.display, 'none');
  assert.equal(f.el('firstOfferButton').style.display, 'none');
  pending.resolve(false); await settle();
});
test('late sign-in recovery resumes the authoritative activation check', async () => {
  const f = fixture({failRead: true, access: async () => true}); await settle(); f.emit(session('a')); await settle();
  assert.equal(f.calls.length, 1); assert.equal(f.el('workspaceButton').style.display, 'block');
  assert.match(f.el('activationNote').innerHTML, /workspace is ready/);
  assert.equal(f.el('status').textContent, '');
});
test('late saved-session data cannot overwrite a newer signed-in account', async () => {
  const read = deferred(); const f = fixture({savedRead: read, access: async () => true}); await settle();
  f.emit(session('b')); await settle(); read.resolve({data: {session: session('a')}}); await settle();
  assert.equal(f.el('signedInEmail').textContent, 'b@example.com');
  assert.ok(f.calls.every(value => value === 'Bearer fictional-b'));
});
test('token refresh shares the in-flight access check and preserves the acknowledged terms', async () => {
  const pending = deferred(); const f = fixture({access: () => pending.promise}); await settle();
  f.el('terms').checked = true; f.el('checkoutButton').disabled = false;
  f.emit({...session('a'), access_token: 'fictional-refreshed'}); await settle();
  assert.equal(f.calls.length, 1); assert.equal(f.el('terms').checked, true);
  pending.resolve(true); await settle(); assert.equal(f.el('workspaceButton').style.display, 'block');
});
test('a late access response cannot activate the page after sign-out', async () => {
  const pending = deferred(); const f = fixture({access: () => pending.promise}); await settle();
  f.emit(null); pending.resolve(true); await settle();
  assert.equal(f.el('workspaceButton').style.display, 'none');
  assert.equal(f.el('firstOfferButton').style.display, 'none');
  assert.equal(f.el('activationNote').style.display, 'none');
});
test('an access response from the previous identity cannot overwrite the current identity', async () => {
  const old = deferred(); const f = fixture({access: auth => auth.endsWith('fictional-a') ? old.promise : Promise.resolve(false)}); await settle();
  f.emit(session('b')); await settle(); old.resolve(true); await settle();
  assert.equal(f.el('signedInEmail').textContent, 'b@example.com');
  assert.equal(f.el('workspaceButton').style.display, 'none');
});
test('a delayed activation offers a read-only retry without restarting checkout', async () => {
  let ready = false; const f = fixture({access: async () => ready}); await settle();
  assert.equal(f.el('activationRetryButton').hidden, false); assert.equal(f.el('workspaceButton').style.display, 'none');
  ready = true; await f.el('activationRetryButton').listeners.click(); await settle();
  assert.equal(f.el('workspaceButton').style.display, 'block'); assert.equal(f.el('activationRetryButton').hidden, true);
  assert.equal(f.calls.length, 7);
});
test('a checkout return uses access recovery rather than asking for checkout again', async () => {
  const f = fixture(); await settle();
  assert.equal(f.el('checkoutButton').style.display, 'none');
  assert.equal(f.el('enrollmentConsent').style.display, 'none');
  const enrollment = fixture({search: ''}); await settle();
  assert.equal(enrollment.el('checkoutButton').style.display, 'block');
  assert.equal(enrollment.el('enrollmentConsent').style.display, 'flex');
  assert.equal(enrollment.el('terms').checked, false);
  assert.equal(enrollment.el('checkoutButton').disabled, true);
  assert.equal(enrollment.calls.length, 0);
});

test('a stalled access response releases the agent to retry without reopening checkout', async () => {
  let stalled = true;
  const f = fixture({access: (_auth, signal) => {
    if (!stalled) return true;
    return new Promise((_resolve, reject) => {
      signal.addEventListener('abort', () => reject(signal.reason), {once: true});
    });
  }});
  await settle();
  assert.equal(f.el('activationRetryButton').hidden, true);
  assert.equal(f.timers.size, 1);
  const [{fn, ms}] = f.timers.values();
  assert.equal(ms, 8000);
  fn();
  await settle();
  assert.equal(f.calls.length, 1);
  assert.equal(f.timers.size, 0);
  assert.equal(f.el('activationRetryButton').hidden, false);
  assert.equal(f.el('checkoutButton').style.display, 'none');
  assert.equal(f.el('workspaceButton').style.display, 'none');

  stalled = false;
  await f.el('activationRetryButton').listeners.click();
  await settle();
  assert.equal(f.calls.length, 2);
  assert.equal(f.timers.size, 0);
  assert.equal(f.el('activationRetryButton').hidden, true);
  assert.equal(f.el('workspaceButton').style.display, 'block');
  assert.equal(f.el('firstOfferButton').style.display, 'block');
});
