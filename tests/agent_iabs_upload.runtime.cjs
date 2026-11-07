const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const renderStart = html.indexOf('  function renderProfileIabsCard() {');
const renderEnd = html.indexOf('\n  root.uploadAgentIabsDocument =', renderStart);
assert.ok(renderStart >= 0 && renderEnd > renderStart, 'IABS profile card renderer is present');
const renderSource = html.slice(renderStart, renderEnd);
const start = html.indexOf('  root.uploadAgentIabsDocument = async function uploadAgentIabsDocument(');
const end = html.indexOf('\n  root.removeAgentIabsDocument =', start);
assert.ok(start >= 0 && end > start, 'IABS upload handler is present');
const source = html.slice(start, end);
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
const fakeButton = () => ({ disabled: false, attributes: {}, setAttribute(name, value) { this.attributes[name] = value; }, removeAttribute(name) { delete this.attributes[name]; } });

test('an unavailable IABS profile check offers an in-place retry and prevents upload until verified', async () => {
  let retry;
  const status = { className: '', innerHTML: '' };
  const uploadButton = fakeButton();
  const actions = { children: [], appendChild(button) { this.children.push(button); } };
  const existingCard = { querySelector(selector) {
    return ({ '#agentIabsStatus': status, '#agentIabsUploadButton': uploadButton,
      '.hof-iabs-actions': actions })[selector] || null;
  } };
  const auth = { session: { user: { id: 'agent-1' } }, role: 'agent', agentIabsDocumentLoadFailed: true };
  const context = vm.createContext({
    hofAuth: auth, isAgentAccount: () => true, escape: value => String(value || ''),
    document: { getElementById: id => id === 'agentIabsProfileCard' ? existingCard
      : (id === 'accountProfileForm' ? {} : null),
      createElement: () => ({ addEventListener: (event, handler) => { assert.equal(event, 'click'); retry = handler; } }) },
    loadCalls: 0,
    loadAgentIabsDocument: async () => { context.loadCalls += 1; }
  });
  context.root = context;
  vm.runInContext(renderSource, context);
  context.renderProfileIabsCard();
  assert.match(status.innerHTML, /Try again before uploading/);
  assert.equal(uploadButton.disabled, true);
  assert.equal(actions.children.length, 1);
  assert.equal(actions.children[0].id, 'agentIabsRetryButton');
  assert.equal(actions.children[0].textContent, 'Check again');
  await retry();
  assert.equal(context.loadCalls, 1);
});

function failureSetup({ metadataFailure = false, metadataPayload, storageError = null, prepareError = null, uploadPayload = null } = {}) {
  const events = [];
  const status = { className: '', textContent: '' };
  const button = fakeButton();
  const file = { name: 'Brokerage IABS.pdf', type: 'application/pdf', size: 2048,
    slice: () => ({ arrayBuffer: async () => Uint8Array.from([37, 80, 68, 70]).buffer }) };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: { session: { user: { id: 'agent-1', access_token: 'test-token' } }, role: 'agent', agentIabsDocument: null },
    __hofAccountProfileEpoch: 4,
    loadAgentIabsDocument: async () => null,
    getSupabaseClient: () => ({
      storage: { from: () => ({ uploadToSignedUrl: async () => {
        events.push('storage');
        return metadataFailure || metadataPayload !== undefined ? { error: null } : { error: storageError || new Error('storage unreachable') };
      } }) },
    }),
    callIabsProfileApi: async (_method, body) => {
      if (body.action === 'prepare_agent_iabs_upload') {
        events.push('prepare');
        if (prepareError) throw prepareError;
        return { upload: uploadPayload || { bucket: 'agent-documents', path: 'agent-1/iabs.pdf', token: 'signed-token' } };
      }
      events.push('metadata');
      assert.equal(body.action, 'save_agent_iabs_metadata');
      if (metadataPayload !== undefined) return { document: metadataPayload };
      throw Object.assign(new Error('database unavailable'), { status: metadataFailure ? 500 : 0 });
    },
    document: { getElementById: id => ({
      agentIabsFile: { files: [file] }, agentIabsStatus: status, agentIabsUploadButton: button
    })[id] || null },
    console: { error() {} },
    window: { hofCustomerActionError: (_error, fallback) => fallback, confirm: () => true }
  });
  context.root = context;
  context.window = context;
  vm.runInNewContext(source, context);
  return { context, status, button, events };
}

test('a successful response without matching IABS metadata does not confirm the upload', async () => {
  const {context,status,events,button} = failureSetup({metadataPayload: null});
  assert.equal(await context.uploadAgentIabsDocument(null, { onStorageConfirmed: () => events.push('storage-confirmed') }),false);
  assert.deepEqual(events,['prepare','storage','storage-confirmed','metadata']);
  assert.equal(context.hofAuth.agentIabsDocument,null);
  assert.match(status.textContent,/couldn’t confirm the profile save/);
  assert.equal(button.disabled,false);
});

test('IABS upload uses the Supabase Storage cache lifetime contract and saves metadata', async () => {
  const events = [];
  const status = { className: '', textContent: '' };
  const button = fakeButton();
  const auth = { session: { user: { id: 'agent-1', access_token: 'test-token' } }, role: 'agent', agentIabsDocument: null };
  const file = { name: 'Brokerage IABS.pdf', type: 'application/pdf', size: 2048,
    slice: () => ({ arrayBuffer: async () => Uint8Array.from([37, 80, 68, 70]).buffer }) };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: auth,
    __hofAccountProfileEpoch: 4,
    getSupabaseClient: () => ({
      storage: { from: bucket => ({ uploadToSignedUrl: async (objectPath, token, body, options) => {
        events.push({ kind: 'storage', bucket, objectPath, body, options });
        assert.equal(token, 'signed-token');
        return { error: null };
      } }) },
    }),
    callIabsProfileApi: async (_method, body) => {
      if (body.action === 'prepare_agent_iabs_upload') {
        events.push({ kind: 'prepare', body });
        return { upload: { bucket: 'agent-documents', path: 'agent-1/iabs.pdf', token: 'signed-token' } };
      }
      events.push({ kind: 'metadata', body });
      return { document: { id: 'iabs-row', user_id: 'agent-1', document_type: 'iabs', storage_bucket: 'agent-documents',
        storage_path: 'agent-1/iabs.pdf', original_filename: body.original_filename,
        mime_type: 'application/pdf', byte_size: body.byte_size, updated_at: '2026-10-29T12:00:00Z' } };
    },
    document: { getElementById: id => ({
      agentIabsFile: { files: [file] }, agentIabsStatus: status,
      agentIabsUploadButton: button,
      agentIabsProfileCard: { remove() { events.push({ kind: 'remove-card' }); } }
    })[id] || null },
    loadAgentIabsDocument: async () => { events.push({ kind: 'profile-check' }); return null; },
    renderProfileIabsCard() { events.push({ kind: 'render-card', document: auth.agentIabsDocument }); },
    mountIabsOfferOption() { events.push({ kind: 'mount-offer-option' }); },
    console: { error() {} },
    window: { hofCustomerActionError: (_error, fallback) => fallback, confirm: () => true }
  });
  context.root = context;
  context.window = context;
  vm.runInContext(source, context);

  await context.uploadAgentIabsDocument();

  const upload = events.find(event => event.kind === 'storage');
  assert.equal(upload.bucket, 'agent-documents');
  assert.equal(upload.objectPath, 'agent-1/iabs.pdf');
  assert.equal(upload.options.contentType, 'application/pdf');
  assert.equal(upload.options.cacheControl, '0');
  assert.equal(events.find(event => event.kind === 'prepare').body.action, 'prepare_agent_iabs_upload');
  assert.equal(events.find(event => event.kind === 'prepare').body.size_bytes, file.size);
  assert.ok(events.findIndex(event => event.kind === 'prepare') < events.findIndex(event => event.kind === 'storage'));
  assert.equal(events.find(event => event.kind === 'metadata').body.action, 'save_agent_iabs_metadata');
  assert.equal(auth.agentIabsDocument.original_filename, file.name);
  assert.equal(auth.agentIabsDocument.user_id, 'agent-1');
  assert.equal(events.some(event => event.kind === 'profile-check'), true);
  assert.equal(events.find(event => event.kind === 'render-card').document.original_filename, file.name);
  assert.equal(events.at(-1).kind, 'mount-offer-option');
  assert.equal(button.disabled, false);
  assert.equal(button.attributes['aria-busy'], undefined);
});

test('the Uploaded Documents action saves its selected IABS privately without attaching it', async () => {
  const events = [], messages = [];
  let status = {textContent: ''};
  const originalStatus = status;
  const auth = { session: { user: { id: 'agent-1', access_token: 'test-token' } }, role: 'agent', agentIabsDocument: null };
  const file = { name: 'Brokerage IABS.pdf', type: 'application/pdf', size: 3 * 1024 * 1024,
    slice: () => ({ arrayBuffer: async () => Uint8Array.from([37, 80, 68, 70]).buffer }) };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: auth,
    __hofAccountProfileEpoch: 1,
    loadAgentIabsDocument: async () => null,
    getSupabaseClient: () => ({
      storage: { from: bucket => ({ uploadToSignedUrl: async (objectPath, token, body, options) => {
        events.push({ kind: 'storage', bucket, objectPath, body, options });
        assert.equal(token, 'signed-token');
        return { error: null };
      } }) },
    }),
    callIabsProfileApi: async (_method, body) => body.action === 'prepare_agent_iabs_upload'
      ? { upload: { bucket: 'agent-documents', path: 'agent-1/iabs.pdf', token: 'signed-token' } }
      : ({ document: {
        id: 'iabs-row', user_id: 'agent-1', document_type: 'iabs', storage_bucket: 'agent-documents', storage_path: 'agent-1/iabs.pdf',
        original_filename: body.original_filename, mime_type: 'application/pdf', byte_size: body.byte_size,
        updated_at: '2026-10-29T12:00:00Z'
      } }),
    document: { getElementById: id => id === 'agentIabsStatus' ? status : null },
    renderProfileIabsCard() { status = {textContent: ''}; events.push({ kind: 'render-profile' }); },
    mountIabsOfferOption() { events.push({ kind: 'mount-offer-option' }); },
    console: { error() {} },
    window: { hofCustomerActionError: (_error, fallback) => fallback, confirm: () => true }
  });
  context.root = context;
  context.window = context;
  vm.runInContext(source, context);

  const saved = await context.uploadAgentIabsDocument(file, {
    onStatus: (message, type) => messages.push({ message, type })
  });

  assert.equal(saved, true);
  assert.equal(events.find(event => event.kind === 'storage').objectPath, 'agent-1/iabs.pdf');
  assert.equal(auth.agentIabsDocument.user_id, 'agent-1');
  assert.equal(auth.agentIabsDocument.original_filename, file.name);
  assert.equal(messages[0].message, 'Uploading your private IABS PDF…');
  assert.match(messages.at(-1).message, /Saved privately to your profile.*not added to this offer/i);
  assert.match(originalStatus.textContent, /Uploading/);
  assert.equal(status.textContent, messages.at(-1).message);
  assert.match(status.textContent, /Brokerage IABS\.pdf/);
  assert.equal(messages.at(-1).type, 'ok');
  assert.equal(events.some(event => event.kind === 'mount-offer-option'), true);
  assert.equal(context.__hofIabsUploadInProgress, false);
});

test('storage failure gives a retry hint and releases the upload control without a metadata write', async () => {
  const { context, status, button, events } = failureSetup();
  await context.uploadAgentIabsDocument();
  assert.deepEqual(events, ['prepare', 'storage']);
  assert.equal(status.className, 'hof-iabs-status error');
  assert.match(status.textContent, /couldn’t upload this PDF.*Check your connection and try again/i);
  assert.equal(button.disabled, false);
  assert.equal(button.attributes['aria-busy'], undefined);
});

test('signed-upload preparation failure stops before Storage and metadata writes', async () => {
  const { context, status, events } = failureSetup({
    prepareError: Object.assign(new Error('private server detail'), { status: 503 })
  });
  await context.uploadAgentIabsDocument();
  assert.deepEqual(events, ['prepare']);
  assert.match(status.textContent, /temporarily unavailable.*try the upload again/i);
  assert.doesNotMatch(status.textContent, /private server detail|service.role/i);
});

test('an upload token for a different bucket or path is rejected before Storage writes', async () => {
  for (const upload of [
    { bucket: 'public-files', path: 'agent-1/iabs.pdf', token: 'signed-token' },
    { bucket: 'agent-documents', path: 'another-agent/iabs.pdf', token: 'signed-token' },
    { bucket: 'agent-documents', path: 'agent-1/iabs.pdf', token: '' }
  ]) {
    const { context, status, events } = failureSetup({ uploadPayload: upload });
    await context.uploadAgentIabsDocument();
    assert.deepEqual(events, ['prepare']);
    assert.equal(status.className, 'hof-iabs-status error');
  }
});

test('known storage failures explain the recovery step without exposing provider details', async t => {
  const cases = [
    ['401', 'Your sign-in expired before the IABS upload finished. Sign in again, then upload it from your profile.'],
    ['403', 'Your account couldn’t save this file to private document storage. Refresh your sign-in and retry; if it continues, contact support.'],
    ['413', 'This IABS PDF is larger than the 10 MB upload limit. Choose a smaller PDF and try again.'],
    ['415', 'Private document storage accepts PDF files only. Choose the brokerage-approved IABS PDF and try again.'],
    ['503', 'Private document storage is temporarily unavailable. Wait a moment, then try the upload again.']
  ];
  for (const [statusCode, expected] of cases) {
    await t.test(`HTTP ${statusCode}`, async () => {
      const { context, status, events } = failureSetup({ storageError: Object.assign(new Error('provider internal detail'), { statusCode }) });
      await context.uploadAgentIabsDocument();
      assert.deepEqual(events, ['prepare', 'storage']);
      assert.equal(status.textContent, expected);
      assert.doesNotMatch(status.textContent, /provider internal detail|supabase|storage unreachable/i);
    });
  }
});

test('metadata failure explains that the private file uploaded and retry is idempotent', async () => {
  const { context, status, button, events } = failureSetup({ metadataFailure: true });
  await context.uploadAgentIabsDocument();
  assert.deepEqual(events, ['prepare', 'storage', 'metadata']);
  assert.equal(status.className, 'hof-iabs-status error');
  assert.match(status.textContent, /couldn’t confirm the profile save.*same private file/i);
  assert.equal(button.disabled, false);
  assert.equal(button.attributes['aria-busy'], undefined);
});

test('a failed profile preflight stops before changing the existing IABS', async () => {
  const { context, status, button, events } = failureSetup();
  context.loadAgentIabsDocument = async () => {
    context.hofAuth.agentIabsDocumentLoadFailed = true;
    return null;
  };
  await context.uploadAgentIabsDocument();
  assert.deepEqual(events, []);
  assert.match(status.textContent, /couldn’t check whether an IABS PDF is already saved.*no files were changed/i);
  assert.equal(button.disabled, true);
  assert.equal(button.attributes['aria-busy'], undefined);
});

test('an invalid replacement is rejected before checking the saved IABS or asking to replace it', async () => {
  const { context, status, button, events } = failureSetup();
  context.loadAgentIabsDocument = async () => assert.fail('Invalid input triggered a private profile lookup');
  context.window.confirm = () => assert.fail('Invalid input triggered replacement confirmation');
  const file = { name: 'Invalid.pdf', type: 'application/pdf', size: 6,
    slice: () => ({ arrayBuffer: async () => new Uint8Array(4).buffer }) };
  assert.equal(await context.uploadAgentIabsDocument(file), false);
  assert.match(status.textContent, /not a readable PDF/);
  assert.deepEqual(events, []);
  assert.equal(button.disabled, false);
});

test('replacing a saved IABS names the existing file and requires confirmation', async () => {
  const { context, status, button, events } = failureSetup();
  context.loadAgentIabsDocument = async () => ({ original_filename: 'Current brokerage IABS.pdf' });
  context.window.confirm = message => {
    assert.match(message, /Replace Current brokerage IABS\.pdf.*Existing packets will not change/);
    return false;
  };
  const saved = await context.uploadAgentIabsDocument();
  assert.equal(saved, false);
  assert.deepEqual(events, []);
  assert.equal(status.textContent, 'Your saved IABS was left unchanged.');
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
  const input = { files: [file], disabled: false };
  const context = vm.createContext({
    MAX_BYTES: 10 * 1024 * 1024,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`,
    hofAuth: auth,
    __hofAccountProfileEpoch: 4,
    getSupabaseClient: () => ({
      storage: { from: bucket => ({ uploadToSignedUrl: async (objectPath, token, body, options) => {
        events.push({ kind: 'storage', bucket, objectPath, body, options });
        assert.equal(token, 'signed-token');
        await storageWrite.promise;
        return { error: null };
      } }) },
      from: table => ({ upsert: async payload => { events.push({ kind: 'metadata', table, payload }); return { error: null }; } })
    }),
    callIabsProfileApi: async (_method, body) => {
      if (body.action === 'prepare_agent_iabs_upload') {
        events.push({ kind: 'prepare', body });
        return { upload: { bucket: 'agent-documents', path: 'agent-1/iabs.pdf', token: 'signed-token' } };
      }
      events.push({ kind: 'metadata', body });
      return { document: { id: 'iabs-row', user_id: 'agent-1', original_filename: body.original_filename,
        byte_size: body.byte_size, storage_path: 'agent-1/iabs.pdf', storage_bucket: 'agent-documents',
        document_type: 'iabs', mime_type: 'application/pdf', updated_at: '2026-10-29T12:00:00Z' } };
    },
    document: { getElementById: id => ({
      agentIabsFile: input, agentIabsStatus: status,
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
  assert.equal(input.disabled, true);
  assert.equal(button.disabled, true);
  assert.equal(button.attributes['aria-busy'], 'true');
  await new Promise(setImmediate);
  await context.uploadAgentIabsDocument();
  assert.equal(events.filter(event => event.kind === 'storage').length, 1);
  storageWrite.resolve();
  await first;

  assert.equal(events.filter(event => event.kind === 'metadata').length, 1);
  assert.equal(input.disabled, false);
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
    loadAgentIabsDocument: async () => null,
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
      storage: { from: bucket => ({ uploadToSignedUrl: async (objectPath, token, body) => {
        events.push({ kind: 'storage', bucket, objectPath, body });
        assert.equal(token, 'signed-token');
        await storageWrite.promise;
        return { error: null };
      } }) },
      from: table => ({ upsert: async payload => { events.push({ kind: 'metadata', table, payload }); return { error: null }; } })
    }),
    callIabsProfileApi: async (_method, body) => {
      if (body.action === 'prepare_agent_iabs_upload') {
        events.push({ kind: 'prepare', body });
        return { upload: { bucket: 'agent-documents', path: 'agent-1/iabs.pdf', token: 'signed-token' } };
      }
      events.push({ kind: 'metadata', body });
      return { document: { id: 'iabs-row', user_id: 'agent-1', original_filename: body.original_filename,
        byte_size: body.byte_size, storage_path: 'agent-1/iabs.pdf', storage_bucket: 'agent-documents',
        document_type: 'iabs', mime_type: 'application/pdf', updated_at: '2026-10-29T12:00:00Z' } };
    },
    document: { getElementById: id => ({
      agentIabsFile: { files: [file] }, agentIabsStatus: status,
      agentIabsUploadButton: button,
      agentIabsProfileCard: { remove() { events.push({ kind: 'remove-card' }); } }
    })[id] || null },
    loadAgentIabsDocument: async () => { events.push({ kind: 'profile-check' }); return null; },
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
  assert.equal(events.find(event => event.kind === 'storage').kind, 'storage');
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
