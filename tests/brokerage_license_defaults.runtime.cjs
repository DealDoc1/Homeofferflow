const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict'), {test} = require('node:test');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  function brokerageLicenseDefault(');
const end = html.indexOf('  function applyProfileDefaultsToWizard(', start);
assert.ok(start > 0 && end > start);
const pairs = [['agentBrokerageQuick', 'agentBrokerLicenseQuick'], ['agentBrokerage', 'agentBrokerLicense'],
  ['profBrokerageName', 'profBrokerageLicense'], ['brandBrokerageName', 'brandLicense']];
function setup() {
  const nodes = new Map(), listeners = {};
  for (const pair of pairs) for (const id of pair) nodes.set(id, {id, value:''});
  const c = vm.createContext({document:{getElementById:id=>nodes.get(id),
    addEventListener:(event, fn)=>{listeners[event] = fn;}}});
  vm.runInContext(html.slice(start, end), c);
  c.wireBrokerageLicenseDefaults();
  return {c, nodes, input:id=>listeners.input({target:nodes.get(id)})};
}
test('every interview/profile/brokerage blank receives 9010832 without extra questions', () => {
  for (const [name, license] of pairs) {
    const x=setup(); x.nodes.get(name).value='On Demand Realty'; x.input(name);
    assert.equal(x.nodes.get(license).value, '9010832');
  }
});
test('explicit license entries are preserved for all four surfaces', () => {
  for (const [name, license] of pairs) {
    const x=setup(); x.nodes.get(name).value='OnDemand Realty'; x.nodes.get(license).value='1234567'; x.input(name);
    assert.equal(x.nodes.get(license).value, '1234567');
  }
});
test('switching brokerages clears only this automatic default, not an entered number', () => {
  const x=setup(), [name,license]=pairs[0];
  x.nodes.get(name).value='OnDemand Realty'; x.input(name);
  x.nodes.get(name).value='Other Realty'; x.input(name);
  assert.equal(x.nodes.get(license).value, '');
  x.nodes.get(name).value='OnDemand Realty'; x.input(name);
  x.nodes.get(license).value='1234567'; x.input(license);
  x.nodes.get(name).value='Other Realty'; x.input(name);
  assert.equal(x.nodes.get(license).value, '1234567');
});
test('unrelated names and unrelated inputs do not change licenses', () => {
  const x=setup(), [name,license]=pairs[0];
  x.nodes.get(name).value='OnDemand Realty Group'; x.input(name);
  assert.equal(x.nodes.get(license).value, '');
  assert.equal(x.c.brokerageLicenseDefault('Other Realty'), '');
});
