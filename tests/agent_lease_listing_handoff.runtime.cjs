const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  window.startAgentWorkflow = function startAgentWorkflow(kind) {');
const end = html.indexOf('\n  }\n\n  const HOF_OFFER_WORKSPACE_PAGE_SIZE', start);
assert.ok(start >= 0 && end > start, 'Agent transaction launcher must be present');
const source = html.slice(start, end + '\n  }'.length);

function setup() {
  const calls = [];
  const timers = [];
  const storage = new Map();
  const elements = new Map();
  const choices = ['sale_listing', 'purchase', 'lease_listing', 'lease_representation'].map(workflow => ({
    dataset: {agentWorkflowChoice: workflow},
    setAttribute(name, value) { this[name] = value; },
  }));
  const document = {
    getElementById: id => elements.get(id) || null,
    querySelectorAll: selector => selector === '[data-agent-workflow-choice]' ? choices : [],
  };
  const window = {
    document,
    navigator: {standalone: false},
    matchMedia: () => ({matches: false}),
    setTimeout: callback => { timers.push(callback); return timers.length; },
    logOfferEvent: (_id, event, status, message, data) => calls.push(['event', event, status, message, data]),
  };
  const context = vm.createContext({window, document, showAccountTab: tab => calls.push(['tab', tab]), sessionStorage: {
    setItem: (key, value) => storage.set(key, value),
    getItem: key => storage.get(key) || null,
  }});
  vm.runInContext(source, context);
  const flushOne = () => {
    assert.ok(timers.length, 'expected a scheduled workspace readiness check');
    timers.shift()();
  };
  return {window, calls, elements, choices, storage, flushOne, timers};
}

test('lease listing records a real workspace start only after the address question is ready', () => {
  const page = setup();

  page.window.startAgentWorkflow('lease_listing');
  assert.deepEqual(JSON.parse(JSON.stringify(page.calls)), [
    ['event', 'agent_workflow_lease_listing_selected', 'selected', 'Agent selected a transaction workflow from the workspace start.', {workflow: 'lease_listing'}],
    ['tab', 'seller'],
  ]);
  assert.equal(page.storage.get('hof_agent_workflow_choice'), 'lease_listing');
  assert.equal(page.window.hofAgentWorkflowContext, 'lease_listing');
  assert.equal(page.choices.find(choice => choice.dataset.agentWorkflowChoice === 'lease_listing')['aria-pressed'], 'true');

  // The workspace has not loaded yet, so it must not count as a completed handoff.
  page.flushOne();
  assert.equal(page.calls.filter(call => call[1] === 'agent_form_package_started').length, 0);

  const card = {scrollIntoView: options => { card.scrollOptions = options; }};
  const address = {focus: options => { address.focusOptions = options; }};
  page.elements.set('listingWorkspaceStartCard', card);
  page.elements.set('listingWorkspaceAddress', address);
  page.flushOne();

  assert.deepEqual(JSON.parse(JSON.stringify(card.scrollOptions)), {behavior: 'smooth', block: 'start'});
  assert.deepEqual(JSON.parse(JSON.stringify(address.focusOptions)), {preventScroll: true});
  assert.deepEqual(JSON.parse(JSON.stringify(page.calls.at(-1))), [
    'event', 'agent_form_package_started', 'started', 'Agent opened the selected guided package workspace.',
    {workflow: 'lease_listing', package: 'Lease listing workspace'},
  ]);
  assert.equal(page.calls.filter(call => call[1] === 'agent_form_package_started').length, 1);
});

for (const [workflow, expectedInterview] of [
  ['purchase', 'purchase'],
  ['sale_listing', 'sale_listing'],
  ['lease_representation', 'lease_representation'],
]) {
  test(`${workflow} opens Question 2 without also falling through to a workspace`, () => {
    const page = setup();
    const opened = [];
    page.window.hofOpenAgentPackageInterview = kind => {
      opened.push(kind);
      return true;
    };

    page.window.startAgentWorkflow(workflow);

    assert.deepEqual(opened, [expectedInterview]);
    assert.equal(page.calls.filter(call => call[0] === 'tab').length, 0);
    assert.equal(page.window.hofAgentWorkflowContext, workflow);
    assert.equal(page.storage.get('hof_agent_workflow_choice'), workflow);
  });
}
