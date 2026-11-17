const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
const start = html.indexOf('  function listingWorkspaceCreateAttempt(');
const end = html.indexOf('\n\n  async function saveListingWorkspaceFoundation', start);
assert.ok(start >= 0 && end > start, 'listing workspace retry helper must be present');
const helper = html.slice(start, end);

function createContext(crypto) {
  const context = vm.createContext({ window: { crypto }, platformUser: () => ({id: 'fixture-agent'}) });
  vm.runInContext(`${helper}\nthis.createAttempt = listingWorkspaceCreateAttempt;`, context);
  return context;
}

test('listing creation retries reuse an attempt only for the same details', () => {
  let nextId = 0;
  const context = createContext({ randomUUID: () => `request-${++nextId}` });
  const payload = {
    sellerLeadId: 'lead-1', listingKind: 'sale', propertyAddress: '123 Main St',
    sellerNames: ['Seller One'], requestedWorkflows: ['listing_agreement'], confidentialNotes: null,
  };
  const first = context.createAttempt(payload);
  const retry = context.createAttempt({ ...payload });
  const changed = context.createAttempt({ ...payload, propertyAddress: '456 Oak St' });
  const restored = context.createAttempt(payload);
  assert.equal(first.requestId, 'request-1');
  assert.equal(retry.requestId, first.requestId);
  assert.equal(changed.requestId, 'request-2');
  assert.equal(restored.requestId, first.requestId);
  first.attempts.delete(first.snapshot);
  assert.equal(context.createAttempt(payload).requestId, 'request-3');
});

test('listing creation request IDs use cryptographic UUID support only', () => {
  const context = createContext({ getRandomValues: bytes => { bytes.fill(0); return bytes; } });
  assert.match(context.createAttempt({}).requestId, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-8[0-9a-f]{3}-[0-9a-f]{12}$/);
  const unsupported = createContext({});
  assert.throws(() => unsupported.createAttempt({}), /cannot safely create/);
});

test('the save flow retains form details on uncertain failure and clears only confirmed attempts', () => {
  const save = html.slice(html.indexOf('  async function saveListingWorkspaceFoundation()'), html.indexOf('\n\n  function renderListingWorkspaceNextStep'));
  assert.ok(save.includes('payload.clientRequestId = createAttempt.requestId'));
  assert.ok(save.indexOf('if (!response.ok || result.ok !== true') < save.indexOf('createAttempt.attempts.delete(createAttempt.snapshot)'));
  assert.ok(save.includes('Your details are still here. Try again to check whether the workspace was saved.'));
  assert.ok(!save.includes('localStorage'));
});
