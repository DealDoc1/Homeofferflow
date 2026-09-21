const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const helperStart = html.indexOf("    const setPackageHandoffStatus = (choice, state = 'opening')");
const helperEnd = html.indexOf('    // A selection should always lead to a visible next step.', helperStart);
const recordStart = html.indexOf('    const recordPackageWorkspaceStart = (choice)', helperEnd);
const recordEnd = html.indexOf('    const recordPrivateDraftWorkspaceStart =', recordStart);
assert.ok(helperStart >= 0 && helperEnd > helperStart && recordStart > helperEnd && recordEnd > recordStart);
const source = html.slice(helperStart, helperEnd) + html.slice(recordStart, recordEnd);

function setup() {
  const status = {
    textContent: '',
    attributes: {},
    setAttribute(name, value) { this.attributes[name] = value; },
  };
  const timers = [];
  const events = [];
  let recovered = 0;
  const document = {getElementById: id => id === 'agentWorkflowStartStatus' ? status : null};
  const window = {
    setTimeout(fn) { timers.push(fn); },
    logOfferEvent(...args) { events.push(args); },
  };
  const context = {document, window, kind: 'purchase', showPackageHandoffRecovery: () => { recovered += 1; }};
  vm.runInNewContext(source + '\nthis.setStatus=setPackageHandoffStatus;this.record=recordPackageWorkspaceStart;', context);
  return {status, timers, events, context, recovered: () => recovered};
}

test('direct package handoff immediately announces the selected workspace', () => {
  const page = setup();
  page.context.setStatus({label: 'Write a purchase offer'});
  assert.equal(page.status.textContent, 'Opening Write a purchase offer…');
  assert.equal(page.status.attributes.role, 'status');
  assert.equal(page.status.attributes['aria-live'], 'polite');
});

test('handoff confirms only after the destination is actually open', () => {
  const page = setup();
  let open = false;
  const choice = {label: 'Write a purchase offer', isWorkspaceOpen: () => open};
  page.context.setStatus(choice);
  page.context.record(choice);
  page.timers.shift()();
  assert.equal(page.status.textContent, 'Opening Write a purchase offer…');
  assert.equal(page.events.length, 0);
  open = true;
  page.timers.shift()();
  assert.equal(page.status.textContent, 'Write a purchase offer is open.');
  assert.equal(page.events.length, 1);
  assert.equal(page.events[0][1], 'agent_form_package_started');
});

test('a timed-out handoff gives one clear recovery direction', () => {
  const page = setup();
  const choice = {label: 'Start a listing workspace', isWorkspaceOpen: () => false};
  page.context.setStatus(choice);
  page.context.record(choice);
  while (page.timers.length) page.timers.shift()();
  assert.equal(page.status.textContent, 'We couldn’t open Start a listing workspace. Use Try again below.');
  assert.equal(page.events.length, 1);
  assert.equal(page.events[0][1], 'agent_form_package_start_timeout');
  assert.equal(page.recovered(), 1);
});
