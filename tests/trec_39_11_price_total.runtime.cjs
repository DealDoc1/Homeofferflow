const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const asset = fs.readFileSync(path.join(__dirname, '..', 'assets', 'trec-39-11-amendment.js'), 'utf8');
const start = asset.indexOf('function moneyTotal(form) {');
const end = asset.indexOf('function bindConditionalFields(form)', start);
assert.ok(start >= 0 && end > start, 'The displayed amendment price calculator must be available');
const productionCalculator = asset.slice(start, end);

function displayedTotal(cash, financing) {
  const output = {textContent:''};
  const form = {
    elements: {priceCash:{value:cash}, priceFinancing:{value:financing}},
    querySelector: () => output,
  };
  vm.runInNewContext(`${productionCalculator}; moneyTotal(form);`, {form});
  return output.textContent;
}

test('unformatted amounts keep their correct displayed total', () => {
  assert.equal(displayedTotal('125000', '375000'), '$500,000.00');
});

test('accepted comma-formatted amounts show the same total', () => {
  assert.equal(displayedTotal('125,000', '375,000'), '$500,000.00');
});

test('comma-formatted cents are preserved in the displayed total', () => {
  assert.equal(displayedTotal('125,000.25', '374,999.75'), '$500,000.00');
});
