const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  root.hofClosePdfPreview = function');
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
  assert.equal(modal.querySelector('a').href, 'blob:qa-1');
  assert.equal(modal.querySelector('a').download, 'HomeOfferFlow-TXR-1508.pdf');
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
