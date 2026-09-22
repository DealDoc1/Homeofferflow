const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'assets', 'acquisition-channel.js'),
  'utf8',
);

function classify({ search = '', referrer = '' } = {}) {
  const window = {
    location: {
      search,
      origin: 'https://www.homeofferflow.com',
    },
  };
  const document = { referrer };
  vm.runInNewContext(source, { window, document, URL, URLSearchParams, Set });
  return window.hofAcquisitionChannel();
}

test('classifies explicit privacy-safe campaign channels', () => {
  assert.equal(classify({ search: '?utm_source=email' }), 'email');
  assert.equal(classify({ search: '?utm_source=organic' }), 'organic');
  assert.equal(classify({ search: '?utm_source=pwa_shortcut' }), 'pwa_shortcut');
  assert.equal(classify({ search: '?utm_source=homeofferflow&utm_medium=homepage' }), 'homepage');
  assert.equal(classify({ search: '?utm_source=homeofferflow_admin&utm_medium=direct_outreach' }), 'direct_outreach');
});

test('reduces referrers to an aggregate category', () => {
  assert.equal(classify({ referrer: 'https://www.google.com/search?q=private-query' }), 'organic');
  assert.equal(classify({ referrer: 'https://search.brave.com/search?q=private-query' }), 'organic');
  assert.equal(classify({ referrer: 'https://example.com/private/path?person=value' }), 'referral');
  assert.equal(classify({ referrer: 'https://www.homeofferflow.com/agents' }), 'direct');
  assert.equal(classify(), 'direct');
});

test('never exposes the referrer value', () => {
  const privateReferrer = 'https://example.com/private/path?person=value';
  const result = classify({ referrer: privateReferrer });
  assert.equal(result, 'referral');
  assert.equal(result.includes('example.com'), false);
  assert.equal(result.includes('person'), false);
});
