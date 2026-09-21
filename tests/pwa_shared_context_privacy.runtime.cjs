const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const { test } = require('node:test');
const repo = path.resolve(__dirname, '..');
const source = process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git', ['show', `${process.env.HOF_TEST_SOURCE_REF}:assets/pwa-share-target.js`], { cwd: repo, encoding: 'utf8' })
  : fs.readFileSync(path.join(repo, 'assets/pwa-share-target.js'), 'utf8');

function run(search, { ready = true, blockedHistory = false, missingHistory = false, historyState = { navigation: 'preserve' } } = {}) {
  const nodes = [], handlers = [], replacements = [], network = [], persisted = [], calls = [];
  const create = tag => {
    const node = { tag, children: [], style: {}, attrs: {}, handlers: {}, textContent: '',
      appendChild: child => node.children.push(child),
      prepend: child => node.children.unshift(child),
      setAttribute: (key, value) => { node.attrs[key] = value; },
      addEventListener: (event, callback) => { node.handlers[event] = callback; },
    };
    nodes.push(node); return node;
  };
  const host = create('main');
  const location = { href: 'https://www.homeofferflow.com/' + search, search,
    assign: url => calls.push(['navigate', url]) };
  const window = { location,
    history: missingHistory ? undefined : { state: historyState, replaceState: (state, title, url) => {
      if (blockedHistory) throw Error('History unavailable');
      replacements.push({ state, title, url });
      location.href = new URL(url, location.href).href;
      location.search = new URL(location.href).search;
    } },
    trackEvent: (...args) => calls.push(['analytics', ...args]),
    logOfferEvent: (...args) => calls.push(['event', ...args]),
    setAudience: (...args) => calls.push(['audience', ...args]),
    beginOfferFrom: surface => calls.push(['buyer', surface]),
    startAccountTransaction: () => calls.push(['agent']),
    openFsboSellerModal: () => calls.push(['seller']),
  };
  const document = { title: 'HomeOfferFlow', readyState: ready ? 'complete' : 'loading',
    body: host, createElement: create, querySelector: () => host,
    getElementById: id => nodes.find(node => node.id === id),
    addEventListener: (event, callback) => { assert.equal(event, 'DOMContentLoaded'); handlers.push(callback); } };
  vm.runInNewContext(source, { window, document, URL, URLSearchParams,
    sessionStorage: { setItem: (...args) => persisted.push(args) },
    localStorage: { setItem: (...args) => persisted.push(args) },
    fetch: (...args) => { network.push(args); return Promise.resolve({ ok: true }); },
  });
  return { nodes, host, handlers, replacements, network, persisted, calls, window,
    card: () => document.getElementById('hofPwaSharedContext') };
}
const share = '?pwa_share=1&title=Sample%20listing&text=Private%20review%20note&url=https%3A%2F%2Fexample.com%2Flisting';
test('shared context is removed from history while remaining visible', () => {
  const x = run(share);
  assert.equal(x.window.location.href, 'https://www.homeofferflow.com/');
  assert.equal(x.replacements.length, 1);
  assert.equal(x.card().children.find(n => n.tag === 'p').textContent, 'Sample listing\nPrivate review note');
  const link = x.card().children.find(n => n.tag === 'a');
  assert.equal(link.href, 'https://example.com/listing');
  assert.equal(link.rel, 'noopener noreferrer');
  assert.equal(link.target, '_blank');
  assert.deepEqual(x.network, []);
  assert.deepEqual(x.persisted, []);
  assert.deepEqual(x.calls, []);
});
test('cleanup runs before DOM-ready rendering', () => {
  const x = run(share, { ready: false });
  assert.equal(x.window.location.search, '');
  assert.equal(x.card(), undefined);
  assert.equal(x.handlers.length, 1);
  x.handlers[0]();
  assert.ok(x.card());
});
test('unrelated route, campaign, hash, and history state survive cleanup', () => {
  const state = { position: 7 };
  const x = run(share + '&audience=agent&utm_source=example&code=auth-placeholder#workspace', { historyState: state });
  const url = new URL(x.window.location.href);
  assert.equal(url.searchParams.get('audience'), 'agent');
  assert.equal(url.searchParams.get('utm_source'), 'example');
  assert.equal(url.searchParams.get('code'), 'auth-placeholder');
  assert.equal(url.hash, '#workspace');
  for (const key of ['pwa_share', 'title', 'text', 'url']) assert.equal(url.searchParams.has(key), false);
  assert.equal(x.replacements[0].state, state);
});
test('duplicate share parameters are all removed', () => {
  const x = run(share + '&title=second&text=other&url=https%3A%2F%2Fexample.org&pwa_share=1');
  assert.equal(x.window.location.search, '');
  assert.equal(x.card().children.find(n => n.tag === 'p').textContent, 'Sample listing\nPrivate review note');
});
for (const search of ['?title=ordinary&text=not-a-share', '?pwa_share=0&text=not-a-share']) test(`non-share URL stays unchanged: ${search}`, () => {
  const x = run(search);
  assert.equal(x.window.location.search, search);
  assert.equal(x.replacements.length, 0);
  assert.equal(x.card(), undefined);
});
for (const search of ['?pwa_share=1', '?pwa_share=1&title=%20&text=%20&url=']) test(`empty share removes only share parameters: ${search}`, () => {
  const x = run(search);
  assert.equal(x.window.location.search, '');
  assert.equal(x.card(), undefined);
});
for (const options of [{ blockedHistory: true }, { missingHistory: true }]) test(`history failure does not block review: ${JSON.stringify(options)}`, () => {
  const x = run(share, options);
  assert.ok(x.card());
  x.card().children.find(n => n.tag === 'button').handlers.click();
  assert.ok(x.calls.some(row => row[0] === 'buyer'));
  assert.deepEqual(x.network, []);
});
test('unsafe links are not made clickable and markup stays text', () => {
  const x = run('?pwa_share=1&title=%3Cscript%3Etest%3C%2Fscript%3E&url=javascript%3Aalert(1)');
  assert.equal(x.window.location.search, '');
  assert.equal(x.card().children.find(n => n.tag === 'p').textContent, '<script>test</script>');
  assert.equal(x.card().children.some(n => n.tag === 'a'), false);
});
test('each explicit CTA still works without sending shared contents to telemetry', () => {
  const x = run(share);
  const buttons = x.card().children.filter(n => n.tag === 'button');
  assert.equal(buttons.length, 3);
  for (const button of buttons) button.handlers.click();
  for (const destination of ['buyer', 'agent', 'seller']) assert.equal(x.calls.filter(row => row[0] === destination).length, 1);
  const calls = JSON.stringify(x.calls);
  for (const sensitive of ['Sample listing', 'Private review note', 'example.com/listing']) assert.equal(calls.includes(sensitive), false);
  assert.deepEqual(x.persisted, [['hof_pwa_shared_context_agent_pending', '1']]);
  assert.deepEqual(x.network, []);
});
