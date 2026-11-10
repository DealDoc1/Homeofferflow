const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');

const source = fs.readFileSync(require.resolve('../service-worker.js'), 'utf8');
const CURRENT_SHELL = source.match(/const SHELL_CACHE = '([^']+)'/)?.[1];
assert.ok(CURRENT_SHELL, 'service worker declares its current shell cache');

class CacheFixture {
  constructor() { this.entries = new Map(); }
  key(request) { return new URL(typeof request === 'string' ? request : request.url, 'https://homeofferflow.com').href; }
  async keys() { return [...this.entries.keys()].map(url => ({ url })); }
  async match(request) { return this.entries.get(this.key(request)); }
  async put(request, response) { this.entries.set(this.key(request), response.clone()); }
}

class ResponseFixture {
  constructor(body, contentType = 'text/html', ok = true) {
    this.body = body;
    this.ok = ok;
    this.headers = { get: name => name.toLowerCase() === 'content-type' ? contentType : null };
  }
  clone() { return new ResponseFixture(this.body, this.headers.get('content-type'), this.ok); }
}

async function activateWith(oldPages, fetchImpl = async () => new ResponseFixture('network response')) {
  const cachesByName = new Map();
  const caches = {
    async keys() { return [...cachesByName.keys()]; },
    async open(name) {
      if (!cachesByName.has(name)) cachesByName.set(name, new CacheFixture());
      return cachesByName.get(name);
    },
    async delete(name) { return cachesByName.delete(name); }
  };
  for (const [cacheName, entries] of Object.entries(oldPages)) {
    const cache = await caches.open(cacheName);
    for (const [url, response] of entries) await cache.put(url, response);
  }

  const listeners = {};
  const self = {
    location: { origin: 'https://homeofferflow.com' },
    clients: { claim: async () => { self.claimed = true; } },
    addEventListener: (name, callback) => { listeners[name] = callback; }
  };
  vm.runInNewContext(source, { self, caches, URL, Promise, fetch: fetchImpl });
  let activation;
  listeners.activate({ waitUntil: promise => { activation = promise; } });
  await activation;
  return { cachesByName, caches, listeners };
}

test('only exact precached public shell assets fall back on network failure', async () => {
  let offline = false;
  const { caches, listeners } = await activateWith({}, async () => {
    if (offline) throw new Error('offline');
    return new ResponseFixture('network script', 'text/javascript');
  });
  const asset = '/assets/pwa-register.js';
  await (await caches.open(CURRENT_SHELL)).put(asset, new ResponseFixture('cached script', 'text/javascript'));
  const request = (path, headers = new Map()) => {
    let response;
    listeners.fetch({
      request: {method: 'GET', mode: 'no-cors', url: 'https://homeofferflow.com' + path, headers},
      respondWith: promise => { response = promise; },
    });
    return response;
  };
  assert.equal((await request(asset)).body, 'network script');
  offline = true;
  assert.equal((await request(asset)).body, 'cached script');
  for (const path of [asset + '?different=1', '/assets/private.js', '/api/profile']) {
    assert.equal(request(path), undefined, path);
  }
  for (const name of ['Authorization', 'Range']) assert.equal(request(asset, new Map([[name, 'fixture']])), undefined);
  await assert.rejects(request('/assets/pwa-share-target.js'), /offline/);
});

test('navigation copies public HTML before asynchronous cache access', async () => {
  const page = new ResponseFixture('public agent page');
  const clone = page.clone.bind(page);
  let consumed = false;
  page.clone = () => {
    assert.equal(consumed, false, 'network HTML was consumed before it was cloned');
    return clone();
  };
  const { caches, listeners } = await activateWith({}, async () => page);
  const open = caches.open.bind(caches);
  let finishOpen;
  const pendingOpen = new Promise(resolve => { finishOpen = resolve; });
  caches.open = async name => { await pendingOpen; return open(name); };
  let navigation, background;
  listeners.fetch({
    request: {method: 'GET', mode: 'navigate', url: 'https://homeofferflow.com/agents'},
    respondWith: promise => { navigation = promise; },
    waitUntil: promise => { background = promise; },
  });
  assert.equal(await navigation, page);
  consumed = true;
  finishOpen();
  await background;
  assert.equal((await (await open(CURRENT_SHELL)).match('/agents')).body, 'public agent page');
});
