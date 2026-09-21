const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const html = fs.readFileSync(path.resolve(__dirname, '..', 'index.html'), 'utf8');
const marker = '<script id="hof-modal-isolation-v1">';
const start = html.indexOf(marker);
const end = html.indexOf('</script>', start);
assert.ok(start >= 0 && end > start, 'modal isolation script is present');
const source = html.slice(start + marker.length, end);

function element(tagName, attrs = {}) {
  const values = new Map(Object.entries(attrs));
  return {
    tagName,
    parentElement: null,
    inert: false,
    isConnected: true,
    hasAttribute(name) { return values.has(name); },
    getAttribute(name) { return values.has(name) ? values.get(name) : null; },
    setAttribute(name, value) { values.set(name, String(value)); },
    removeAttribute(name) { values.delete(name); },
  };
}

function setup() {
  const body = element('BODY');
  const page = element('MAIN');
  const preserved = element('ASIDE', { 'aria-hidden': 'true' });
  preserved.inert = true;
  const modalA = element('DIV', { 'aria-hidden': 'true' });
  const modalB = element('DIV', { 'aria-hidden': 'true' });
  const script = element('SCRIPT');
  body.children = [page, preserved, modalA, modalB, script];
  body.children.forEach(child => { child.parentElement = body; });
  const window = {};
  vm.runInNewContext(source, { window, document: { body }, Set, Map, Array });
  return { window, page, preserved, modalA, modalB, script };
}

test('isolates one active interview and restores the exact prior page state', () => {
  const x = setup();
  x.modalA.setAttribute('aria-hidden', 'false');
  x.window.setHofModalIsolation(x.modalA, true);
  assert.equal(x.page.inert, true);
  assert.equal(x.page.getAttribute('aria-hidden'), 'true');
  assert.equal(x.modalA.inert, false);
  assert.equal(x.modalB.inert, true);
  assert.equal(x.script.inert, false);

  x.modalA.setAttribute('aria-hidden', 'true');
  x.window.setHofModalIsolation(x.modalA, false);
  assert.equal(x.page.inert, false);
  assert.equal(x.page.hasAttribute('aria-hidden'), false);
  assert.equal(x.preserved.inert, true);
  assert.equal(x.preserved.getAttribute('aria-hidden'), 'true');
  assert.equal(x.modalB.inert, false);
  assert.equal(x.modalB.getAttribute('aria-hidden'), 'true');
});

test('nested dialogs restore the underlying interview instead of exposing the page', () => {
  const x = setup();
  x.modalA.setAttribute('aria-hidden', 'false');
  x.window.setHofModalIsolation(x.modalA, true);
  x.modalB.setAttribute('aria-hidden', 'false');
  x.window.setHofModalIsolation(x.modalB, true);

  assert.equal(x.modalA.inert, true);
  assert.equal(x.modalA.getAttribute('aria-hidden'), 'true');
  assert.equal(x.modalB.inert, false);

  x.modalB.setAttribute('aria-hidden', 'true');
  x.window.setHofModalIsolation(x.modalB, false);
  assert.equal(x.page.inert, true);
  assert.equal(x.modalA.inert, false);
  assert.equal(x.modalA.getAttribute('aria-hidden'), 'false');
  assert.equal(x.modalB.inert, true);

  x.modalA.setAttribute('aria-hidden', 'true');
  x.window.setHofModalIsolation(x.modalA, false);
  assert.equal(x.page.inert, false);
  assert.equal(x.modalB.inert, false);
});

test('closing an underlying dialog keeps the remaining top dialog isolated', () => {
  const x = setup();
  x.modalA.setAttribute('aria-hidden', 'false');
  x.window.setHofModalIsolation(x.modalA, true);
  x.modalB.setAttribute('aria-hidden', 'false');
  x.window.setHofModalIsolation(x.modalB, true);

  x.modalA.setAttribute('aria-hidden', 'true');
  x.window.setHofModalIsolation(x.modalA, false);
  assert.equal(x.page.inert, true);
  assert.equal(x.modalA.inert, true);
  assert.equal(x.modalB.inert, false);
  assert.equal(x.modalB.getAttribute('aria-hidden'), 'false');
});
