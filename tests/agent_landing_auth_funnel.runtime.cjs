const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const html = fs.readFileSync(path.resolve(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  function recordAgentLandingAuthStage(eventType)');
const end = html.indexOf('  async function signOutAccount()', start);
const source = html.slice(start, end);

function setup({ active = true, channel = 'organic' } = {}) {
  const store = new Map();
  if (active) store.set('hof_agent_landing_auth_funnel', '1');
  store.set('hof_agent_landing_channel', channel);
  const requests = [];
  const context = vm.createContext({
    window: {},
    sessionStorage: {
      getItem: key => store.has(key) ? store.get(key) : null,
      setItem: (key, value) => store.set(key, String(value)),
      removeItem: key => store.delete(key),
    },
    fetch: (url, options) => {
      requests.push({ url, options });
      return Promise.resolve({ ok: true });
    },
    Set,
    String,
    JSON,
  });
  vm.runInContext(`${source}\nglobalThis.recordStage = recordAgentLandingAuthStage;`, context);
  return { record: context.recordStage, requests, store };
}

test('records each allowlisted sign-in stage once without identity data', () => {
  const x = setup();
  for (const eventType of [
    'agent_landing_auth_opened',
    'agent_landing_email_started',
    'agent_landing_magic_link_requested',
  ]) {
    x.record(eventType);
    x.record(eventType);
  }
  assert.equal(x.requests.length, 3);
  const payloads = x.requests.map(request => JSON.parse(request.options.body));
  assert.deepEqual(payloads.map(payload => payload.event_type), [
    'agent_landing_auth_opened',
    'agent_landing_email_started',
    'agent_landing_magic_link_requested',
  ]);
  for (const payload of payloads) {
    assert.equal(payload.request_type, 'agent_landing_event');
    assert.equal(payload.channel, 'organic');
    assert.deepEqual(Object.keys(payload).sort(), ['channel', 'event_type', 'request_type']);
  }
});

test('does not record outside an active public-agent handoff', () => {
  const x = setup({ active: false });
  x.record('agent_landing_auth_opened');
  assert.equal(x.requests.length, 0);
});

test('rejects unknown stages and normalizes an unknown channel', () => {
  const x = setup({ channel: 'email@example.test' });
  x.record('untrusted_stage');
  x.record('agent_landing_auth_opened');
  assert.equal(x.requests.length, 1);
  assert.equal(JSON.parse(x.requests[0].options.body).channel, 'unspecified');
});
