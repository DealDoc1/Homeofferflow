const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  async function nextStep() {');
const end = html.indexOf('\n  function prevStep()', start);
assert.ok(start >= 0 && end > start, 'Buyer Continue handler must be present');
const source = html.slice(start, end);

function setup({throwDuringRefresh = false} = {}) {
  const calls = [];
  const state = {step: 0, termsOK: true, data: {userType: 'homebuyer'}};
  const context = vm.createContext({
    state,
    getCurrentSteps: () => ['step3', 'step5'],
    wireSmartCalculations: () => calls.push('wire'),
    syncFinancingFieldsFromPrice: () => {
      calls.push('sync');
      if (throwDuringRefresh) throw new Error('calculation unavailable');
    },
    updateAppraisalAddendumVisibility: () => calls.push('appraisal'),
    updatePaymentCalculator: () => calls.push('payment'),
    collectData: () => calls.push('collect'),
    validateCurrentStep: () => { calls.push('validate'); return true; },
    showStep: step => calls.push(['show', step]),
    setValidationStatus: message => calls.push(['status', message]),
    console: {error: () => calls.push('error')},
  });
  vm.runInContext(source, context);
  return {calls, context};
}

test('financing Continue refreshes defaults and advances the interview', async () => {
  const page = setup();
  await page.context.nextStep();
  assert.deepEqual(JSON.parse(JSON.stringify(page.calls)), [
    'wire', 'sync', 'appraisal', 'payment', 'collect', 'validate', ['show', 1],
  ]);
});

test('a calculator refresh error does not strand the buyer on Step 3', async () => {
  const page = setup({throwDuringRefresh: true});
  await page.context.nextStep();
  assert.deepEqual(JSON.parse(JSON.stringify(page.calls)), [
    'wire', 'sync', 'error',
    ['status', 'Some suggested financing amounts could not be refreshed. Check the terms below and continue when they are complete.'],
    'collect', 'validate', ['show', 1],
  ]);
});
