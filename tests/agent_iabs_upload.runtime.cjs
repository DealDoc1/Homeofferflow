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
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
const fakeButton = () => ({ disabled: false, attributes: {}, setAttribute(name, value) { this.attributes[name] = value; }, removeAttribute(name) { delete this.attributes[name]; } });

function failureSetup({ metadataFailure = false } = {}) {
  const events = [];
  const status = { className: '', textContent: '' };
  const button = fakeButton();
  const file = { name: 'Brokerage IABS.pdf', type: 'application/pdf', size: 2048,
    slice: () => ({ arrayBuffer: async () => Uint8Array.from([37, 80, 68, 70]).buffer }) };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: { session: { user: { id: 'agent-1' } }, role: 'agent', agentIabsDocument: null },
    __hofAccountProfileEpoch: 4,
    getSupabaseClient: () => ({
      storage: { from: () => ({ upload: async () => {
        events.push('storage');
        return metadataFailure ? { error: null } : { error: new Error('storage unreachable') };
      } }) },
      from: () => ({ upsert: async () => {
        events.push('metadata');
        return { error: new Error('database unavailable') };
      } })
    }),
    document: { getElementById: id => ({
      agentIabsFile: { files: [file] }, agentIabsStatus: status, agentIabsUploadButton: button
    })[id] || null },
    console: { error() {} },
    window: { hofCustomerActionError: (_error, fallback) => fallback }
  });
  context.root = context;
  context.window = context;
  vm.runInNewContext(source, context);
  return { context, status, button, events };
}

test('IABS upload uses the Supabase Storage cache lifetime contract and saves metadata', async () => {
  const events = [];
  const status = { className: '', textContent: '' };
  const button = fakeButton();
  const auth = { session: { user: { id: 'agent-1' } }, role: 'agent', agentIabsDocument: null };
  const file = { name: 'Brokerage IABS.pdf', type: 'application/pdf', size: 2048,
    slice: () => ({ arrayBuffer: async () => Uint8Array.from([37, 80, 68, 70]).buffer }) };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: auth,
    __hofAccountProfileEpoch: 4,
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
      agentIabsUploadButton: button,
      agentIabsProfileCard: { remove() { events.push({ kind: 'remove-card' }); } }
    })[id] || null },
    loadAgentIabsDocument: async () => { events.push({ kind: 'unexpected-readback' }); throw new Error('simulated readback failure'); },
    renderProfileIabsCard() { events.push({ kind: 'render-card', document: auth.agentIabsDocument }); },
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
  assert.equal(auth.agentIabsDocument.original_filename, file.name);
  assert.equal(auth.agentIabsDocument.user_id, 'agent-1');
  assert.equal(events.some(event => event.kind === 'unexpected-readback'), false);
  assert.equal(events.find(event => event.kind === 'render-card').document.original_filename, file.name);
  assert.equal(events.at(-1).kind, 'mount-offer-option');
  assert.equal(button.disabled, false);
  assert.equal(button.attributes['aria-busy'], undefined);
});

test('storage failure gives a retry hint and releases the upload control without a metadata write', async () => {
  const { context, status, button, events } = failureSetup();
  await context.uploadAgentIabsDocument();
  assert.deepEqual(events, ['storage']);
  assert.equal(status.className, 'hof-iabs-status error');
  assert.match(status.textContent, /couldn’t upload this PDF.*Check your connection and try again/i);
  assert.equal(button.disabled, false);
  assert.equal(button.attributes['aria-busy'], undefined);
});

test('metadata failure explains that the private file uploaded and retry is idempotent', async () => {
  const { context, status, button, events } = failureSetup({ metadataFailure: true });
  await context.uploadAgentIabsDocument();
  assert.deepEqual(events, ['storage', 'metadata']);
  assert.equal(status.className, 'hof-iabs-status error');
  assert.match(status.textContent, /couldn’t confirm the profile save.*same private file/i);
  assert.equal(button.disabled, false);
  assert.equal(button.attributes['aria-busy'], undefined);
});

test('repeated upload clicks start only one storage and metadata write', async () => {
  const events = [];
  const status = { className: '', textContent: '' };
  const button = fakeButton();
  const storageWrite = deferred();
  const auth = { session: { user: { id: 'agent-1' } }, role: 'agent', agentIabsDocument: null };
  const file = { name: 'Brokerage IABS.pdf', type: 'application/pdf', size: 2048,
    slice: () => ({ arrayBuffer: async () => Uint8Array.from([37, 80, 68, 70]).buffer }) };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: auth,
    __hofAccountProfileEpoch: 4,
    getSupabaseClient: () => ({
      storage: { from: bucket => ({ upload: async (objectPath, body, options) => {
        events.push({ kind: 'storage', bucket, objectPath, body, options });
        await storageWrite.promise;
        return { error: null };
      } }) },
      from: table => ({ upsert: async payload => { events.push({ kind: 'metadata', table, payload }); return { error: null }; } })
    }),
    document: { getElementById: id => ({
      agentIabsFile: { files: [file] }, agentIabsStatus: status,
      agentIabsUploadButton: button,
      agentIabsProfileCard: { remove() { events.push({ kind: 'remove-card' }); } }
    })[id] || null },
    loadAgentIabsDocument: async () => null,
    renderProfileIabsCard() { events.push({ kind: 'render-card' }); },
    mountIabsOfferOption() { events.push({ kind: 'mount-offer-option' }); },
    console: { error() {} },
    window: { hofCustomerActionError: (_error, fallback) => fallback }
  });
  context.root = context;
  context.window = context;
  vm.runInContext(source, context);

  const first = context.uploadAgentIabsDocument();
  assert.equal(button.disabled, true);
  assert.equal(button.attributes['aria-busy'], 'true');
  await new Promise(setImmediate);
  await context.uploadAgentIabsDocument();
  assert.equal(events.filter(event => event.kind === 'storage').length, 1);
  storageWrite.resolve();
  await first;

  assert.equal(events.filter(event => event.kind === 'metadata').length, 1);
  assert.equal(button.disabled, false);
  assert.equal(button.attributes['aria-busy'], undefined);
});

test('a mislabeled non-PDF IABS is rejected before storage or metadata writes', async () => {
  const events = [];
  const status = { className: '', textContent: '' };
  const button = fakeButton();
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
    document: { getElementById: id => ({ agentIabsFile: { files: [file] }, agentIabsStatus: status, agentIabsUploadButton: button })[id] || null },
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
  assert.equal(button.disabled, false);
  assert.equal(button.attributes['aria-busy'], undefined);
});

test('an account switch during storage upload cannot save metadata or populate the new profile', async () => {
  const events = [];
  const status = { className: '', textContent: '' };
  const button = fakeButton();
  const storageWrite = deferred();
  const auth = { session: { user: { id: 'agent-1' } }, role: 'agent', agentIabsDocument: null };
  const file = { name: 'Brokerage IABS.pdf', type: 'application/pdf', size: 2048,
    slice: () => ({ arrayBuffer: async () => Uint8Array.from([37, 80, 68, 70]).buffer }) };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: auth,
    __hofAccountProfileEpoch: 4,
    getSupabaseClient: () => ({
      storage: { from: bucket => ({ upload: async (objectPath, body) => {
        events.push({ kind: 'storage', bucket, objectPath, body });
        await storageWrite.promise;
        return { error: null };
      } }) },
      from: table => ({ upsert: async payload => { events.push({ kind: 'metadata', table, payload }); return { error: null }; } })
    }),
    document: { getElementById: id => ({
      agentIabsFile: { files: [file] }, agentIabsStatus: status,
      agentIabsUploadButton: button,
      agentIabsProfileCard: { remove() { events.push({ kind: 'remove-card' }); } }
    })[id] || null },
    loadAgentIabsDocument: async () => { events.push({ kind: 'unexpected-readback' }); return null; },
    renderProfileIabsCard() { events.push({ kind: 'render-card' }); },
    mountIabsOfferOption() { events.push({ kind: 'mount-offer-option' }); },
    console: { error() {} },
    window: { hofCustomerActionError: (_error, fallback) => fallback }
  });
  context.root = context;
  context.window = context;
  vm.runInContext(source, context);

  const pending = context.uploadAgentIabsDocument();
  await new Promise(setImmediate);
  assert.equal(events[0].kind, 'storage');
  auth.session.user.id = 'agent-2';
  context.__hofAccountProfileEpoch = 5;
  auth.agentIabsDocument = null;
  storageWrite.resolve();
  await pending;

  assert.equal(events.some(event => event.kind === 'metadata'), false);
  assert.equal(events.some(event => event.kind === 'render-card' || event.kind === 'mount-offer-option'), false);
  assert.equal(auth.agentIabsDocument, null);
  assert.equal(button.disabled, false);
  assert.equal(button.attributes['aria-busy'], undefined);
});
