const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const html = fs.readFileSync(path.resolve(__dirname, '..', 'index.html'), 'utf8');
const helpers = html.slice(html.indexOf('  function adminSafe('), html.indexOf('  // Event metadata is inserted'));

function context(metrics = {}) {
  const result = { metrics, escapeAttr: value => String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;') };
  vm.createContext(result);
  vm.runInContext(helpers, result);
  return result;
}

function renderCard(title, metrics) {
  const titleAt = html.indexOf(`>${title}</div>`);
  assert.ok(titleAt > 0);
  const start = html.lastIndexOf('<div class="admin-metric">', titleAt);
  const end = html.indexOf('<div class="admin-metric">', titleAt);
  const sandbox = context(metrics);
  vm.runInContext('rendered = `' + html.slice(start, end) + '`;', sandbox);
  return sandbox.rendered;
}

test('repeat actions remain visible with event units rather than inflated conversion claims', () => {
  const sandbox = context();
  assert.equal(sandbox.adminLandingEventRate(6, 1), '600.0 per 100 landing views');
  assert.equal(sandbox.adminLandingEventRate(6, 5), '120.0 per 100 landing views');
  assert.equal(sandbox.adminLandingEventRate(0, 5), '0.0 per 100 landing views');
});

test('no denominator produces an explicit unavailable rate', () => {
  const sandbox = context();
  for (const views of [0, undefined, -1, Infinity, 'invalid']) {
    assert.equal(sandbox.adminLandingEventRate(6, views), 'no landing views recorded');
  }
});

test('channel summary includes direct starts without a recorded landing and escapes labels', () => {
  const sandbox = context();
  assert.equal(sandbox.adminChannelEventRateSummary({direct: 1}, {direct: 6, '<script>': 2}),
    'direct (600.0 per 100 landing views) · &lt;script&gt; (no landing views recorded)');
  assert.equal(sandbox.adminChannelEventRateSummary({}, {}), 'activity appears after the next landing visit or workspace start');
});

test('actual homebuyer card reports repeated and direct starts without percent conversion', () => {
  const rendered = renderCard('Homebuyer $99 Funnel', {
    homebuyerLandingViewCount: 5, homebuyerLandingOfferStartedCount: 6,
    homebuyerLandingOfferStartRate: 120,
    homebuyerLandingViewCountsByChannel: {unspecified: 1},
    homebuyerLandingOfferStartedCountsByChannel: {unspecified: 6, pwa: 2},
    homebuyerLandingOfferStartRatesByChannel: {unspecified: 600},
  });
  assert.match(rendered, /6 opened the guided workspace \(120\.0 per 100 landing views\)/);
  assert.match(rendered, /unspecified \(600\.0 per 100 landing views\)/);
  assert.match(rendered, /pwa \(no landing views recorded\)/);
  assert.match(rendered, /Counts include repeat actions and direct workspace entries/);
  assert.doesNotMatch(rendered, /channel conversion|120\.0%|600\.0%/i);
});

test('actual agent card keeps activity and recorded view counts distinct', () => {
  const rendered = renderCard('Agent Workspace Funnel', {
    agentLandingViewCount: 1, agentLandingCtaCount: 6, agentLandingCtaRate: 600,
    agentLandingViewCountsByChannel: {unspecified: 1},
    agentLandingCtaCountsByChannel: {unspecified: 6},
    agentLandingCtaRatesByChannel: {unspecified: 600},
  });
  assert.match(rendered, /6 continued to the workspace \(600\.0 per 100 landing views\)/);
  assert.match(rendered, /Agent channel activity:/);
  assert.match(rendered, /Counts include repeat actions and direct workspace entries/);
  assert.doesNotMatch(rendered, /Agent channel conversion|600\.0%/);
});
