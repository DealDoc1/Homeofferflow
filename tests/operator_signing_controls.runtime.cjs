const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const html = fs.readFileSync(require('node:path').join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  async function runPurchaseSigningTest(');
const end = html.indexOf('  async function loadAdminDashboard(', start);
assert.ok(start >= 0 && end > start);

function harness(phase) {
  const nodes = Object.fromEntries(['Purchase', 'Showing', 'Amendment', 'ListingLead', 'ListingPackage', 'LeaseListing'].flatMap(scope => [
    ['admin' + scope + 'SigningTestStatus', { textContent: '' }],
    ['admin' + scope + 'SigningTestSend', { textContent: 'Send', disabled: false }],
  ]));
  const requests = [];
  const ctx = vm.createContext({ hofAuth: { session: { access_token: 'FAKE' } },
    document: { getElementById: id => nodes[id] },
    fetch: async (url, input) => { requests.push({ url, input }); return { ok: true, json: async () => ({ signingTest: { phase, message: 'Scoped result' } }) }; },
  });
  vm.runInContext(html.slice(start, end), ctx);
  return { ctx, nodes, requests };
}
for (const [scope, actionPrefix, widget] of [['purchase', 'purchase', 'Purchase'], ['showing', 'showing', 'Showing'], ['amendment', 'amendment', 'Amendment'], ['listing-lead', 'listing_lead', 'ListingLead'], ['listing-package', 'listing_package', 'ListingPackage'], ['lease-listing', 'lease_listing', 'LeaseListing']]) {
  for (const send of [false, true]) test(`${scope} ${send ? 'send' : 'check'} uses only its fixed action and status`, async () => {
    const h = harness('created'), button = { textContent: 'Original', disabled: false };
    await h.ctx.runPurchaseSigningTest(send, button, scope);
    assert.equal(h.requests.length, 1);
    assert.deepEqual(JSON.parse(h.requests[0].input.body), { action: `${send ? 'send' : 'check'}_${actionPrefix}_signing_test` });
    assert.equal(h.nodes[`admin${widget}SigningTestStatus`].textContent, 'Scoped result');
    assert.equal(h.nodes[`admin${widget}SigningTestSend`].disabled, true);
    for (const other of ['Purchase', 'Showing', 'Amendment', 'ListingLead', 'ListingPackage', 'LeaseListing'].filter(value => value !== widget)) {
      assert.equal(h.nodes[`admin${other}SigningTestStatus`].textContent, '');
      assert.equal(h.nodes[`admin${other}SigningTestSend`].disabled, false);
    }
    assert.equal(button.textContent, 'Original');
  });
}
test('not-started status permits only the selected test send control', async () => {
  const h = harness('not_started');
  await h.ctx.runPurchaseSigningTest(false, { textContent: 'Check' }, 'showing');
  assert.equal(h.nodes.adminShowingSigningTestSend.disabled, false);
});

test('an unknown or inherited scope never falls back to sending a purchase test', async () => {
  for (const scope of ['unknown', 'lease_listing', 'constructor', 'toString', '__proto__', '', null]) {
    const h = harness('not_started'), button = {textContent: 'Original', disabled: false};
    await h.ctx.runPurchaseSigningTest(true, button, scope);
    assert.equal(h.requests.length, 0);
    assert.equal(button.disabled, false);
    assert.equal(button.textContent, 'Original');
    assert.ok(Object.values(h.nodes).filter(node => 'textContent' in node).every(node => node.textContent === '' || node.textContent === 'Send'));
  }
});

test('a missing session never submits the lease QA action', async () => {
  const h = harness('not_started');
  h.ctx.hofAuth.session = null;
  await h.ctx.runPurchaseSigningTest(true, {textContent: 'Send'}, 'lease-listing');
  assert.equal(h.requests.length, 0);
});

test('an ambiguous lease QA response leaves send disabled and permits read-only checking', async () => {
  const h = harness('not_started');
  h.ctx.fetch = async () => { throw new Error('Synthetic timeout'); };
  const check = {textContent: 'Check', disabled: false};
  await h.ctx.runPurchaseSigningTest(false, check, 'lease-listing');
  assert.equal(h.nodes.adminLeaseListingSigningTestSend.disabled, true);
  assert.equal(check.disabled, false);
  assert.match(h.nodes.adminLeaseListingSigningTestStatus.textContent, /could not be confirmed/);
  assert.equal(h.nodes.adminPurchaseSigningTestStatus.textContent, '');
});
