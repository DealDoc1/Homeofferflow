const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  root.loadAgentIabsDocument = async function loadAgentIabsDocument() {');
const end = html.indexOf('\n  root.uploadAgentIabsDocument =', start);
assert.ok(start >= 0 && end > start, 'IABS profile lookup and card renderer are present');
const source = html.slice(start, end);
const offerStart = html.indexOf('  root.getProfileIabsOfferDoc = async function getProfileIabsOfferDoc() {');
const offerEnd = html.indexOf('\n\n  const priorLoadProfile', offerStart);
assert.ok(offerStart >= 0 && offerEnd > offerStart, 'optional offer IABS retrieval is present');
const offerSource = html.slice(offerStart, offerEnd);

function setup(response, { deferredLookup = false } = {}) {
  let finishLookup;
  const status = { className: '', innerHTML: '' };
  const uploadButton = { textContent: '', disabled: false, attributes: {},
    setAttribute(name, value) { this.attributes[name] = value; },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener() {}
  };
  const actions = { removeButton: null, appendChild(node) { this.removeButton = node; } };
  const card = {
    id: '', className: '', innerHTML: '',
    querySelector: selector => selector === '#agentIabsStatus' ? status
      : (selector === '#agentIabsUploadButton' ? uploadButton
        : (selector === '.hof-iabs-actions' ? actions : actions.removeButton))
  };
  const profile = { appendChild(node) { this.card = node; } };
  const context = vm.createContext({
    hofAuth: { session: { user: { id: 'agent-1' }, access_token: 'test-token' }, role: 'agent', agentIabsDocument: null },
    __hofAccountProfileEpoch: 1,
    getSupabaseClient: () => ({}),
    callIabsProfileApi: async () => {
      const result = deferredLookup
        ? await new Promise(resolve => { finishLookup = resolve; })
        : response;
      if (result.error) throw new Error('profile lookup unavailable');
      if (result.incomplete) return {};
      return { document: result.data || null };
    },
    document: {
      getElementById: id => id === 'accountProfileForm' ? profile : (id === 'agentIabsProfileCard' ? profile.card : null),
      createElement: tag => tag === 'div' ? card : { addEventListener() {}, remove() { actions.removeButton = null; } }
    },
    console: { warn() {} },
    escape: value => String(value ?? ''),
    isAgentAccount: () => true
  });
  context.root = context;
  vm.runInContext(source, context);
  return { context, profile, status, uploadButton, actions, finishLookup: value => finishLookup(value) };
}

test('IABS profile lookup failure is not presented as an empty profile', async () => {
  const { context, profile, status, uploadButton } = setup({ data: null, error: new Error('profile lookup unavailable') });
  await context.loadAgentIabsDocument();
  context.renderProfileIabsCard();

  assert.equal(context.hofAuth.agentIabsDocumentLoadFailed, true);
  assert.match(status.innerHTML, /couldn’t check whether an IABS PDF is already saved/i);
  assert.match(profile.card.innerHTML, /id="agentIabsStatus"[^>]*role="status"[^>]*aria-live="polite"[^>]*aria-atomic="true"/);
  assert.equal(uploadButton.textContent, 'Upload or Replace IABS PDF');
  assert.doesNotMatch(status.innerHTML, /No IABS PDF saved yet/);
});

test('a successful empty IABS lookup keeps the accurate first-upload state', async () => {
  const { context, status, uploadButton } = setup({ data: null, error: null });
  await context.loadAgentIabsDocument();
  context.renderProfileIabsCard();

  assert.equal(context.hofAuth.agentIabsDocumentLoadFailed, false);
  assert.match(status.innerHTML, /No IABS PDF saved yet/);
  assert.equal(uploadButton.textContent, 'Upload IABS PDF');
});

test('an incomplete IABS response keeps upload gated and offers a retry', async () => {
  const {context,status,uploadButton} = setup({incomplete:true});
  await context.loadAgentIabsDocument();
  context.renderProfileIabsCard();
  assert.equal(context.hofAuth.agentIabsDocumentLoadFailed,true);
  assert.equal(uploadButton.disabled,true);
  assert.match(status.innerHTML,/Try again before uploading/);
});

test('an in-flight IABS check shows progress before the lookup finishes', async () => {
  const { context, profile, status, finishLookup } = setup(null, { deferredLookup: true });
  const lookup = context.loadAgentIabsDocument();

  assert.equal(context.hofAuth.agentIabsDocumentLoadPending, true);
  assert.match(profile.card.innerHTML, /Checking for a saved IABS PDF/);
  assert.match(profile.card.innerHTML, /Upload or Replace IABS PDF/);
  assert.match(profile.card.innerHTML, /id="agentIabsUploadButton"[^>]*disabled/);
  finishLookup({ data: null, error: null });
  await lookup;

  assert.equal(context.hofAuth.agentIabsDocumentLoadPending, false);
  assert.match(status.innerHTML, /No IABS PDF saved yet/);
});

test('an obsolete IABS lookup releases its pending state without trusting its response', async () => {
  const { context, profile, status, finishLookup } = setup(null, { deferredLookup: true });
  const lookup = context.loadAgentIabsDocument();
  context.__hofAccountProfileEpoch = 2;
  finishLookup({ data: { document_type: 'iabs', original_filename: 'stale.pdf' }, error: null });
  await lookup;

  assert.equal(context.hofAuth.agentIabsDocument, null);
  assert.equal(context.hofAuth.agentIabsDocumentLoadPending, false);
  assert.equal(context.hofAuth.agentIabsDocumentLoadFailed, true);
  assert.match(status.innerHTML, /couldn’t check whether an IABS PDF is already saved/i);
  assert.equal(profile.card.id, 'agentIabsProfileCard');
});

test('a saved IABS found after initial render restores the replace and remove actions', async () => {
  const { context, status, uploadButton, actions, finishLookup } = setup(null, { deferredLookup: true });
  const lookup = context.loadAgentIabsDocument();
  finishLookup({ data: { document_type: 'iabs', storage_bucket: 'agent-documents', storage_path: 'agent-1/iabs.pdf', original_filename: 'Brokerage IABS.pdf', byte_size: 2048 }, error: null });
  await lookup;

  assert.match(status.innerHTML, /Saved privately: <strong>Brokerage IABS\.pdf<\/strong>/);
  assert.equal(uploadButton.textContent, 'Replace IABS PDF');
  assert.equal(actions.removeButton.id, 'agentIabsRemoveButton');
  assert.equal(actions.removeButton.textContent, 'Remove');
});

test('an unavailable IABS lookup stops offer submission with specific recovery guidance', async () => {
  const context = vm.createContext({
    hofAuth: { session: { user: { id: 'agent-1' } }, role: 'agent', agentIabsDocument: null, agentIabsDocumentLoadFailed: true },
    state: { data: { includeAgentIabs: true } },
    getSupabaseClient: () => ({}),
    loadAgentIabsDocument: async () => null,
    isAgentAccount: () => true,
    BUCKET: 'agent-documents',
    filePath: userId => `${userId}/iabs.pdf`
  });
  context.root = context;
  vm.runInContext(offerSource, context);

  await assert.rejects(context.getProfileIabsOfferDoc(), /couldn’t check your saved IABS PDF.*Refresh this page.*offer was not submitted/i);
});
