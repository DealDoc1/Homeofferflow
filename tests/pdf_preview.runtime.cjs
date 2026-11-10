const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  let pdfPreviewOpener;');
const end = html.indexOf('  async function loadPrivateDrafts()', start);
assert.ok(start >= 0 && end > start, 'Production PDF preview helpers must exist');
const source = html.slice(start, end);

function previewContext(pdfViewerEnabled) {
  let body;
  class Element {
    constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.listeners = {}; }
    append(...children) { children.forEach(child => this.appendChild(child)); }
    appendChild(child) { child.parent = this; this.children.push(child); }
    setAttribute(key, value) { this[key] = value; }
    addEventListener(event, handler) { this.listeners[event] = handler; }
    focus() { this.focused = true; }
    remove() { this.parent.children = this.parent.children.filter(child => child !== this); }
    querySelector(tag) { return this.children.find(child => child.tag === tag) || this.children.map(child => child.querySelector(tag)).find(Boolean); }
  }
  body = new Element('body');
  const revoked = [];
  let sequence = 0;
  const context = {
    root: {}, navigator: { pdfViewerEnabled },
    document: { body, createElement: tag => new Element(tag), getElementById: id => body.children.find(child => child.id === id) },
    URL: { createObjectURL: () => `blob:qa-${++sequence}`, revokeObjectURL: url => revoked.push(url) },
  };
  vm.runInNewContext(source, context);
  return { ...context, revoked };
}

test('PDF-capable browsers show the frame and a same-document download', () => {
  const context = previewContext(true);
  context.root.hofShowPdfPreview({}, 'TXR-1508');
  const modal = context.document.getElementById('hofPdfPreviewModal');
  assert.equal(modal.querySelector('iframe').src, 'blob:qa-1');
  const [open, download] = modal.querySelector('h4').parent.children[1].children;
  assert.equal(open.textContent, 'Open to print');
  assert.equal(open.href, 'blob:qa-1');
  assert.equal(open.target, '_blank');
  assert.equal(open.rel, 'noopener noreferrer');
  assert.equal(download.href, 'blob:qa-1');
  assert.equal(download.download, 'HomeOfferFlow-TXR-1508.pdf');
  assert.equal(modal.querySelector('button').focused, true);
});

test('Browsers without an inline PDF viewer get a useful download fallback', () => {
  const context = previewContext(false);
  context.root.hofShowPdfPreview({}, 'TXR-1508');
  const modal = context.document.getElementById('hofPdfPreviewModal');
  assert.equal(modal.querySelector('iframe'), undefined);
  assert.match(modal.querySelector('p').textContent, /Download a copy/);
  assert.equal(modal.querySelector('a').href, 'blob:qa-1');
});

test('Replacing and closing a preview releases its private object URLs', () => {
  const context = previewContext(true);
  context.root.hofShowPdfPreview({}, 'TXR-1508');
  context.root.hofShowPdfPreview({}, 'TXR-1506');
  assert.deepEqual(context.revoked, ['blob:qa-1']);
  assert.equal(context.document.body.children.length, 1);
  context.root.hofClosePdfPreview();
  assert.deepEqual(context.revoked, ['blob:qa-1', 'blob:qa-2']);
  assert.equal(context.document.body.children.length, 0);
});

test('Escape returns focus to the opener and account cleanup leaves focus alone', () => {
  const context = previewContext(false);
  let focusCount = 0;
  const opener = {isConnected:true, focus:()=>focusCount++};
  context.root.hofShowPdfPreview({}, 'TXR-1508', opener);
  const modal = context.document.getElementById('hofPdfPreviewModal');
  modal.listeners.keydown({key:'Escape', preventDefault(){}, stopPropagation(){}});
  assert.equal(focusCount,1);
  assert.equal(context.document.getElementById('hofPdfPreviewModal'),undefined);
  context.root.hofShowPdfPreview({}, 'TXR-1508', opener);
  context.root.hofClosePdfPreview(false);
  assert.equal(focusCount,1);
});

test('a stalled prepared document restores the Preview button for retry', async () => {
  const start = html.indexOf('  let latestAgreementPreview;');
  const end = html.indexOf('  function filterPreparedAgreementRows(', start);
  const root = { hofAuth: { session: {} } };
  const button = { isConnected: true, disabled: false, textContent: 'Preview' };
  const notices = [], previews = [];
  let expire, stall = true;
  root.announceWorkspaceStatus = message => notices.push(message);
  root.hofShowPdfPreview = blob => previews.push(blob);
  const preview = vm.runInNewContext(html.slice(start, end) + '\npreviewAgreementPdf;', {
    root, window: root, AbortController, token: () => 'fixture', console: { error() {} },
    setTimeout: (callback, ms) => { assert.equal(ms, 60000); expire = callback; return 1; },
    clearTimeout: id => { assert.equal(id, 1); expire = undefined; },
    fetch: async (_, { signal }) => ({
      ok: true,
      blob: () => stall
        ? new Promise((_, reject) => signal.addEventListener('abort', () => reject(signal.reason), { once: true }))
        : Promise.resolve('fictional-pdf'),
    }),
  });
  const agreement = { id: 'fictional', form_code: 'TXR-1507' };
  const pending = preview(agreement, button);
  assert.equal(button.textContent, 'Opening PDF…');
  await new Promise(setImmediate);
  expire();
  await pending;
  assert.match(notices[0], /took too long/);
  assert.deepEqual(previews, []);
  assert.equal(button.disabled, false);
  assert.equal(button.textContent, 'Preview');
  assert.equal(expire, undefined);
  stall = false;
  await preview(agreement, button);
  assert.deepEqual(previews, ['fictional-pdf']);
  assert.equal(expire, undefined);
});

test('a late prepared document cannot replace the newer preview or its print link', async () => {
  const start = html.indexOf('  let latestAgreementPreview;');
  const end = html.indexOf('  function filterPreparedAgreementRows(', start);
  const context = previewContext(true);
  const reads = new Map();
  const preview = vm.runInNewContext(html.slice(start, end) + '\npreviewAgreementPdf;', {
    ...context, window: context.root, AbortController, token: () => 'fixture',
    setTimeout, clearTimeout,
    fetch: url => new Promise(resolve => reads.set(url, resolve)),
  });
  const opener = () => ({ isConnected: true, disabled: false, textContent: 'Preview' });
  const older = preview({ id: 'older', form_code: 'TXR-1507' }, opener());
  const newer = preview({ id: 'newer', form_code: 'TXR-1506' }, opener());
  reads.get('/api/admin-dashboard?preview_agreement=newer')({ ok: true, blob: async () => ({}) });
  await newer;
  const modal = context.document.getElementById('hofPdfPreviewModal');
  reads.get('/api/admin-dashboard?preview_agreement=older')({ ok: true, blob: async () => ({}) });
  await older;
  assert.equal(context.document.getElementById('hofPdfPreviewModal'), modal);
  assert.equal(modal.querySelector('h4').textContent, 'TXR-1506 preview');
  assert.equal(modal.querySelector('a').href, modal.querySelector('iframe').src);
});
