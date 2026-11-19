const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const html = fs.readFileSync(path.resolve(__dirname, '..', 'index.html'), 'utf8');
const source = html.split('<script id="hof-pwa-shortcuts-v1">', 2)[1].split('</script>', 1)[0];

function run({ standalone = true, ok = true, userAgent = 'Mozilla/5.0 (iPhone)', surface = 'agent_saved_offer', action = '' } = {}) {
  const local = new Map([['hof_pwa_install_intent_surface', surface]]);
  if (action) local.set('hof_pwa_preferred_launch_action', action);
  const session = new Map();
  const requests = [];
  const assignments = [];
  const handlers = {};
  const window = {
    location: { pathname: '/', search: '', hash: '', assign: url => assignments.push(url) },
    navigator: { standalone: false },
    matchMedia: () => ({ matches: standalone }),
    history: { replaceState() {} },
    setTimeout: callback => callback(),
    addEventListener: (event, callback) => { handlers[event] = callback; },
    hofAuth: {},
  };
  const document = {
    title: 'HomeOfferFlow',
    addEventListener: (event, callback) => { handlers[event] = callback; },
  };
  const storage = map => ({
    getItem: key => map.has(key) ? map.get(key) : null,
    setItem: (key, value) => map.set(key, String(value)),
    removeItem: key => map.delete(key),
  });
  const context = vm.createContext({
    window,
    document,
    navigator: { userAgent },
    localStorage: storage(local),
    sessionStorage: storage(session),
    URLSearchParams,
    fetch: async (url, options) => {
      requests.push({ url, options });
      return { ok };
    },
  });
  vm.runInContext(source, context);
  return { handlers, local, session, requests, assignments };
}

test('first standalone return records only an allowlisted surface once', async () => {
  const x = run();
  x.handlers.DOMContentLoaded();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(x.requests.length, 1);
  const payload = JSON.parse(x.requests[0].options.body);
  assert.deepEqual(payload, {
    request_type: 'public_pwa_install_event',
    event_type: 'pwa_install_returned',
    platform: 'ios',
    surface: 'agent_saved_offer',
  });
  assert.equal(x.local.get('hof_pwa_install_returned_agent_saved_offer'), '1');
  x.handlers.DOMContentLoaded();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(x.requests.length, 1);
});

test('normal browser visits do not record an installed-app return', async () => {
  const x = run({ standalone: false });
  x.handlers.DOMContentLoaded();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(x.requests.length, 0);
});

test('a Build Readiness install returns to the blueprint and records the public return', async () => {
  const x = run({ surface: '/build-readiness', action: 'build_readiness' });
  x.handlers.DOMContentLoaded();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(x.assignments[0], '/build-readiness?utm_source=pwa_shortcut&utm_medium=installed_app&utm_campaign=build_readiness');
  const payload = JSON.parse(x.requests[0].options.body);
  assert.equal(payload.surface, '/build-readiness');
  assert.equal(payload.event_type, 'pwa_install_returned');
});

test('failed recording remains retryable without duplicating the pending request', async () => {
  const x = run({ ok: false });
  x.handlers.DOMContentLoaded();
  x.handlers.DOMContentLoaded();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(x.requests.length, 1);
  assert.equal(x.session.has('hof_pwa_install_returned_agent_saved_offer'), false);
  x.handlers.DOMContentLoaded();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(x.requests.length, 2);
});
