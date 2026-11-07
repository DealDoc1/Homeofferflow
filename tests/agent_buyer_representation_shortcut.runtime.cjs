const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  window.startAgentBuyerRepresentation = function startAgentBuyerRepresentation() {');
const end = html.indexOf('\n  };', start);
assert.ok(start >= 0 && end > start, 'Direct buyer representation launcher must be present');
const source = html.slice(start, end + '\n  };'.length);

function setup({open = true} = {}) {
  const calls = [];
  const window = {
    logOfferEvent: (...args) => calls.push(['event', ...args]),
    hofOpenAgentPackageInterview: (...args) => {
      calls.push(['interview', ...args]);
      return open;
    },
  };
  const context = vm.createContext({window, showAccountTab: tab => calls.push(['tab', tab])});
  vm.runInContext(source, context);
  return {window, calls};
}

test('dashboard shortcut opens the existing direct short/long representation choice', () => {
  const page = setup();
  assert.equal(page.window.startAgentBuyerRepresentation(), true);
  assert.deepEqual(JSON.parse(JSON.stringify(page.calls.at(-1))), [
    'interview', 'purchase', {directPackage: 'representation'},
  ]);
  assert.equal(page.calls.filter(call => call[0] === 'tab').length, 0);
});

test('dashboard shortcut recovers to Guided Forms if the direct interview is unavailable', () => {
  const page = setup({open: false});
  assert.equal(page.window.startAgentBuyerRepresentation(), false);
  assert.deepEqual(JSON.parse(JSON.stringify(page.calls.at(-1))), ['tab', 'relationships']);
});
