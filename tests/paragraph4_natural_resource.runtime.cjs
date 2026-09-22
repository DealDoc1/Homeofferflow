const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const html = fs.readFileSync(path.resolve(__dirname, '..', 'index.html'), 'utf8');
const section = (start, end) => {
  const from = html.indexOf(start);
  const to = html.indexOf(end, from);
  assert.ok(from >= 0 && to > from, `source section ${start}`);
  return html.slice(from, to);
};

function element(value = '') {
  return { value, checked: false, style: {}, dataset: {}, trim() { return this.value.trim(); } };
}

function setup() {
  const ids = new Map([
    ['paragraph4LeaseFields', element()], ['paragraph4SellerFields', element()],
    ['paragraph4Seller1Name', element()], ['paragraph4Seller1Email', element()],
    ['paragraph4Seller2Name', element()], ['paragraph4Seller2Email', element()],
    ['seller1Name', element('Seller One')], ['seller1Email', element('seller@example.com')],
    ['seller2Name', element()], ['seller2Email', element()],
    ['leaseResidential', element()], ['leaseFixture', element()], ['leaseNaturalResource', element()],
    ['residentialLeaseInterview', element()], ['fixtureLeaseInterview', element()],
    ['naturalResourceLeaseInterview', element()], ['naturalResourceTerminationDaysField', element()],
    ['residentialLeaseStatus', element()], ['residentialLeaseAssignmentFields', element()],
    ['residentialLeaseDelivery', element()], ['residentialLeaseDeliveryDaysField', element()],
    ['residentialLeaseOralNoticeField', element()], ['leasedFixturesOtherField', element()],
    ['assumedFixtureLeasesOtherField', element()], ['fixtureLeaseOralNoticeField', element()],
    ['leaseNRDelivered', element('no')],
  ]);
  let leases = 'yes';
  let paymentStatus = '';
  const context = vm.createContext({
    document: {
      getElementById: id => ids.get(id) || null,
      querySelectorAll: () => [],
    },
    getRadio: group => group === 'leases' ? leases : '',
    getVal: id => ids.get(id)?.value || '',
    setInputIfEmpty: (id, value) => { const input = ids.get(id); if (input && !input.value) input.value = value || ''; },
    checkedValues: () => [],
    setPaymentStatus: value => { paymentStatus = value; },
  });
  vm.runInContext(section('  function updateParagraph4LeaseVisibility()', '  function selectCard('), context);
  vm.runInContext(section('  function controlledLaunchUnsupportedPaths(', '  function hydrostaticSigningSummary('), context);
  return { context, ids, setLeases(value) { leases = value; }, paymentStatus: () => paymentStatus };
}

test('natural-resource-only interview asks contract questions without seller addendum signers', () => {
  const x = setup();
  x.ids.get('leaseNaturalResource').checked = true;
  x.context.updateParagraph4LeaseVisibility();
  assert.equal(x.ids.get('paragraph4LeaseFields').style.display, 'block');
  assert.equal(x.ids.get('naturalResourceLeaseInterview').style.display, 'block');
  assert.equal(x.ids.get('naturalResourceTerminationDaysField').style.display, 'block');
  assert.equal(x.ids.get('paragraph4SellerFields').style.display, 'none');
});

test('residential or fixture addenda retain seller signature fields', () => {
  const x = setup();
  x.ids.get('leaseResidential').checked = true;
  x.context.updateParagraph4LeaseVisibility();
  assert.equal(x.ids.get('paragraph4SellerFields').style.display, 'block');
  assert.equal(x.ids.get('residentialLeaseInterview').style.display, 'block');
});

test('natural-resource-only validation accepts complete terms and rejects missing days', () => {
  const x = setup();
  const complete = {
    leases: 'yes', leaseNaturalResource: 'yes', leaseResidential: 'no', leaseFixture: 'no',
    leaseNRDelivered: 'no', naturalResourceTerminationDays: '7',
  };
  assert.equal(x.context.validateParagraph4LeaseInputs(complete), true);
  assert.equal(x.context.validateParagraph4LeaseInputs({...complete, naturalResourceTerminationDays: ''}), false);
  assert.match(x.paymentStatus(), /termination period from 1 to 999 days/);
});
