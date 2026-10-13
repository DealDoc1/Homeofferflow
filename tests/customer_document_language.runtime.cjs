const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(require('node:path').join(__dirname, '..', 'index.html'), 'utf8');
const code = html.match(/<script id="hof-agent-document-language-v1">([\s\S]*?)<\/script>/)[1];

class Element {
  constructor(text, control = false) { this.textContent = text; this.control = control; }
  closest() { return this.control ? this : null; }
}
class Document extends Element {
  constructor() {
    super(''); this.body = {}; this.readyState = 'complete';
    this.submit = new Element('Save private draft');
    this.option = new Element('Choose the printed plan…'); this.option.value = '';
    this.checkbox = { checked: true, required: true, value: 'on' };
    this.open = new Element('Start seller-financing draft');
    this.parent = new Element('');
    this.copy = { textContent: 'Use the 06-15-26 TXR-1914 interview to prepare a private draft. Answer only the terms printed on the source.', parentElement: this.parent };
    this.label = { textContent: 'This is a private draft, not a loan document or signature request.', parentElement: this.parent };
    this.userText = { textContent: 'Answer only the terms printed on the source. This is a private draft, not a loan.', parentElement: new Element('', true) };
    this.statusText = { textContent: 'Your private draft is ready. ', parentElement: this.parent };
    this.action = new Element('Review and send'); this.action.handler = () => 'still works';
    this.groups = {
      '.hof-agreement-dialog button[type="submit"]': [this.submit],
      '.hof-agreement-card button, .hof-agreement-dialog button': [this.submit, this.open],
      '.hof-agreement-dialog p, .hof-agreement-card p, .hof-agreement-dialog label': [{ nodes: [this.copy, this.label, this.userText], checkbox: this.checkbox }],
      '.hof-agreement-dialog .hof-iabs-status': [{ nodes: [this.statusText], action: this.action }],
      '.hof-agreement-dialog option': [this.option],
    };
  }
  querySelectorAll(selector) { return this.groups[selector] || []; }
  createTreeWalker(el) { let i = -1; return { currentNode: null, nextNode() { this.currentNode = el.nodes[++i]; return !!this.currentNode; } }; }
}
function run() {
  const document = new Document();
  vm.runInNewContext(code, { document, window: {}, Element, Document, NodeFilter: { SHOW_TEXT: 4 }, MutationObserver: class { observe() {} } });
  return document;
}
test('guided copy uses plain questions rather than revision/source/private-draft language', () => {
  const d = run();
  assert.equal(d.copy.textContent, 'Answer the questions to prepare a document for review. Answer the questions needed for this document.');
});
test('payment-plan prompt is clear while its stored value is untouched', () => {
  const d = run(); assert.equal(d.option.textContent, 'Choose a payment plan…'); assert.equal(d.option.value, '');
});
test('checkboxes and legal-review labels remain intact', () => {
  const d = run(); assert.equal(d.checkbox.checked, true); assert.equal(d.checkbox.required, true);
  assert.equal(d.checkbox.value, 'on'); assert.match(d.label.textContent, /document for review, not a loan document or signature request/);
});
test('user-entered textarea text is never rewritten as interface copy', () => {
  const d = run(); assert.equal(d.userText.textContent, 'Answer only the terms printed on the source. This is a private draft, not a loan.');
});
test('next-step buttons and handlers survive normalization', () => {
  const d = run(); assert.equal(d.statusText.textContent, 'Your document is ready for review. ');
  assert.equal(d.action.textContent, 'Review and send'); assert.equal(d.action.handler(), 'still works');
  assert.equal(d.submit.textContent, 'Save for review');
});
test('review instructions retain sentence case without capitalizing inline wording', () => {
  const codeWithFixture = code.replace('  const run = () => normalize(document);', '  document.copy.textContent = "Review the draft. Review the completed draft, then review the draft again.";\n  const run = () => normalize(document);');
  const document = new Document();
  vm.runInNewContext(codeWithFixture, { document, window: {}, Element, Document, NodeFilter: { SHOW_TEXT: 4 }, MutationObserver: class { observe() {} } });
  assert.equal(document.copy.textContent, 'Review the document. Review the completed document, then review the document again.');
});
