const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(new URL('../index.html', `file://${__dirname}/`), 'utf8');
const match = source.match(/<script id="hof-pwa-install-v1">([\s\S]*?)<\/script>/);
assert.ok(match, 'main PWA install module exists');

const listeners = {};
const requests = [];
const local = new Map();
const session = new Map();
const handlers = {};
const card = {
  dataset: {},
  classList: { add() {} },
  querySelector(selector) {
    const id = selector.slice(1);
    if (id === 'hofPwaInstallButton') return null;
    return {
      addEventListener(type, handler) { handlers[`${id}:${type}`] = handler; },
      disabled: false,
      textContent: ''
    };
  },
  remove() {}
};
const review = {
  classList: { contains: value => value === 'active' },
  prepend() {}
};
const document = {
  getElementById(id) {
    if (id === 'step8') return review;
    if (id === 'hofPwaInstallCard') return card;
    return null;
  },
  createElement() { return card; }
};
const storage = map => ({
  getItem: key => map.has(key) ? map.get(key) : null,
  setItem: (key, value) => map.set(key, String(value)),
  removeItem: key => map.delete(key)
});
const navigator = { userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)' };
const window = {
  navigator,
  matchMedia: () => ({ matches: false }),
  state: { data: { userType: 'homebuyer' } },
  hofAuth: { session: null },
  logOfferEvent() { throw new Error('PWA install events must not require authentication'); },
  addEventListener(type, handler) { listeners[type] = handler; }
};
const fetch = (url, options) => {
  requests.push({ url, options, payload: JSON.parse(options.body) });
  return Promise.resolve({ ok: true });
};
const context = {
  window,
  document,
  navigator,
  localStorage: storage(local),
  sessionStorage: storage(session),
  fetch,
  console,
  setTimeout
};
vm.runInNewContext(match[1], context);

listeners.beforeinstallprompt({ preventDefault() {} });
assert.deepEqual(requests.map(row => row.payload.event_type).sort(), [
  'pwa_install_native_available',
  'pwa_install_shown'
]);
assert.ok(requests.every(row => row.url === '/api/fsbo-lead'));
assert.ok(requests.every(row => row.payload.request_type === 'public_pwa_install_event'));
assert.ok(requests.every(row => row.payload.platform === 'ios' && row.payload.surface === 'buyer_review'));
assert.ok(requests.every(row => !('user_id' in row.payload) && !('offer_id' in row.payload)));
assert.equal(Object.keys(handlers).length, 2, 'dismiss and Home Screen help actions are attached');
console.log('Main PWA install events reach the anonymous aggregate endpoint without account or offer data.');
