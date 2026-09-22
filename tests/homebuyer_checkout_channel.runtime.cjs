const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const page = fs.readFileSync(path.resolve(__dirname, '..', 'index.html'), 'utf8');
const start = page.indexOf('  const homebuyerCheckoutChannels = new Set(');
const end = page.indexOf('  function recordHomebuyerCheckoutEvent(', start);
assert.notEqual(start, -1);
assert.notEqual(end, -1);
const source = page.slice(start, end);

function remember({ search = '', saved = '' } = {}) {
  const values = new Map();
  if (saved) values.set('hof_homebuyer_checkout_channel', saved);
  const sessionStorage = {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
  };
  const context = {
    window: { location: { search } },
    sessionStorage,
    URLSearchParams,
    Set,
  };
  vm.runInNewContext(`${source}\nresult = rememberHomebuyerCheckoutChannel();`, context);
  return { result: context.result, saved: values.get('hof_homebuyer_checkout_channel') || '' };
}

test('keeps direct and homepage attribution from the public buyer page', () => {
  assert.deepEqual(remember({ saved: 'direct' }), { result: 'direct', saved: 'direct' });
  assert.deepEqual(remember({ saved: 'homepage' }), { result: 'homepage', saved: 'homepage' });
});

test('keeps installed-app attribution through checkout recovery', () => {
  assert.deepEqual(remember({ saved: 'pwa_shortcut' }), { result: 'pwa_shortcut', saved: 'pwa_shortcut' });
});

test('a new allowlisted campaign replaces an older saved channel', () => {
  assert.deepEqual(
    remember({ search: '?utm_source=organic', saved: 'direct' }),
    { result: 'organic', saved: 'organic' },
  );
  assert.deepEqual(
    remember({ search: '?utm_source=homeofferflow_admin&utm_medium=direct_outreach' }),
    { result: 'direct_outreach', saved: 'direct_outreach' },
  );
});

test('an untrusted campaign cannot enter checkout attribution', () => {
  assert.deepEqual(remember({ search: '?utm_source=private-value' }), { result: 'unspecified', saved: '' });
});
