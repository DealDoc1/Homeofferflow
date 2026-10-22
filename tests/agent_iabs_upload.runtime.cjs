const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  root.uploadAgentIabsDocument = async function uploadAgentIabsDocument() {');
const end = html.indexOf('\n  root.removeAgentIabsDocument =', start);
assert.ok(start >= 0 && end > start, 'IABS upload handler is present');
const source = html.slice(start, end);

test('IABS upload uses the Supabase Storage cache lifetime contract and saves metadata', async () => {
  const events = [];
  const status = { className: '', textContent: '' };
  const file = { name: 'Brokerage IABS.pdf', type: 'application/pdf', size: 2048,
    slice: () => ({ arrayBuffer: async () => Uint8Array.from([37, 80, 68, 70]).buffer }) };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: { session: { user: { id: 'agent-1' } }, agentIabsDocument: null },
    getSupabaseClient: () => ({
      storage: { from: bucket => ({ upload: async (objectPath, body, options) => {
        events.push({ kind: 'storage', bucket, objectPath, body, options });
        return { error: null };
      } }) },
      from: table => ({ upsert: async (payload, options) => {
        events.push({ kind: 'metadata', table, payload, options });
        return { error: null };
      } })
    }),
    document: { getElementById: id => ({
      agentIabsFile: { files: [file] }, agentIabsStatus: status,
      agentIabsProfileCard: { remove() { events.push({ kind: 'remove-card' }); } }
    })[id] || null },
    loadAgentIabsDocument: async () => ({ original_filename: file.name }),
    renderProfileIabsCard() { events.push({ kind: 'render-card' }); },
    mountIabsOfferOption() { events.push({ kind: 'mount-offer-option' }); },
    console: { error() {} },
    window: { hofCustomerActionError: (_error, fallback) => fallback }
  });
  context.root = context;
  context.window = context;
  vm.runInContext(source, context);

  await context.uploadAgentIabsDocument();

  const upload = events.find(event => event.kind === 'storage');
  assert.equal(upload.bucket, 'agent-documents');
  assert.equal(upload.objectPath, 'agent-1/iabs.pdf');
  assert.equal(upload.options.contentType, 'application/pdf');
  assert.equal(upload.options.upsert, true);
  assert.equal(upload.options.cacheControl, '0');
  assert.equal(events.find(event => event.kind === 'metadata').table, 'hof_agent_documents');
  assert.equal(events.at(-1).kind, 'mount-offer-option');
});

test('a mislabeled non-PDF IABS is rejected before storage or metadata writes', async () => {
  const events = [];
  const status = { className: '', textContent: '' };
  const file = { name: 'Brokerage IABS.pdf', type: 'application/pdf', size: 2048,
    slice: () => ({ arrayBuffer: async () => Uint8Array.from([80, 75, 3, 4]).buffer }) };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: { session: { user: { id: 'agent-1' } }, agentIabsDocument: null },
    getSupabaseClient: () => ({
      storage: { from: () => ({ upload: async (...args) => { events.push(['storage', ...args]); return { error: null }; } }) },
      from: () => ({ upsert: async (...args) => { events.push(['metadata', ...args]); return { error: null }; } })
    }),
    document: { getElementById: id => ({ agentIabsFile: { files: [file] }, agentIabsStatus: status })[id] || null },
    console: { error() {} },
    window: { hofCustomerActionError: (_error, fallback) => fallback }
  });
  context.root = context;
  context.window = context;
  vm.runInContext(source, context);

  await context.uploadAgentIabsDocument();

  assert.equal(status.className, 'hof-iabs-status error');
  assert.match(status.textContent, /not a readable PDF/);
  assert.deepEqual(events, []);
});
