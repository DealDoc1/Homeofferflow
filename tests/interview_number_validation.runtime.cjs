const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const { test } = require('node:test');
const repo = path.resolve(__dirname, '..');
const html = process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git', ['show', `${process.env.HOF_TEST_SOURCE_REF}:index.html`], { cwd: repo, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 })
  : fs.readFileSync(path.join(repo, 'index.html'), 'utf8');
function source(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert.ok(a >= 0 && b > a, start);
  return html.slice(a, b);
}
const values = { offerPrice: '500000', earnestMoney: '5000', optionFee: '250', optionDays: '7', loanAmount: '450000', downPayment: '50000',
  loanYears: '30', interestRateCap: '6.375', interestFirstYears: '30', originationCap: '1', buyerApprovalDays: '21',
  appraisalPartialValue: '400000', appraisalTerminateDays: '10', appraisalTerminateValue: '400000' };
function setup(role = 'homebuyer', appraisal = 'partial') {
  class Element {
    constructor(id) { this.id = id; this.value = values[id] || ''; this.type = 'number'; this.style = {}; this.dataset = {}; this.attrs = {}; }
    setAttribute(key, value) { this.attrs[key] = value; }
    removeAttribute(key) { delete this.attrs[key]; }
    matches(selector) { return selector === 'input, select, textarea'; }
  }
  const nodes = new Map(), statuses = [], focuses = [];
  const get = id => { if (!nodes.has(id)) nodes.set(id, new Element(id)); return nodes.get(id); };
  get('step3').querySelector = () => [...nodes.values()].find(n => n.dataset.validationInvalid === 'true');
  const radios = { financing: 'conventional', appraisalAddendum: appraisal };
  const c = vm.createContext({ Element, state: { data: { userType: role }, step: 0 },
    document: { getElementById: get, querySelectorAll: () => [] },
    getCurrentSteps: () => ['step3'], getRadio: key => radios[key] || '',
    setValidationStatus: message => statuses.push(message), guideToFirstValidationAnswer: step => focuses.push(step),
    requireRadioSelection: (name, label, missing) => { if (!radios[name]) missing.push(label); },
    setAppraisalAddendumRequired() {}, markAssumptionInterviewIssues() {}, markSellerFinancingInterviewIssues() {},
  });
  const start = html.includes('  function interviewNumberValidationMessage(') ? '  function interviewNumberValidationMessage(' : '  function requireField(';
  vm.runInContext(source(start, '  function requireValidEmail('), c);
  vm.runInContext(source('  function clearValidationFeedbackFor(', '  function startHomebuyerOffer()'), c);
  return { c, get, radios, statuses, focuses };
}
for (const role of ['homebuyer', 'agent', 'investor']) test(`${role} valid price and financing step continues`, () => {
  const x = setup(role);
  assert.equal(x.c.validateCurrentStep(), true);
  assert.deepEqual(x.focuses, []);
});
for (const id of Object.keys(values)) test(`${id} rejects negative input with accessible guidance`, () => {
  const x = setup('agent', id.startsWith('appraisalTerminate') ? 'additional' : 'partial');
  x.get(id).value = '-1';
  assert.equal(x.c.validateCurrentStep(), false);
  assert.equal(x.get(id).dataset.validationInvalid, 'true');
  assert.equal(x.get(id).attrs['aria-invalid'], 'true');
  assert.ok(x.statuses.at(-1).includes('0'));
  assert.deepEqual(x.focuses, ['step3']);
});
for (const value of ['NaN', 'Infinity', '1e309', '0x10', 'not a number', '']) test(`offer price rejects malformed or empty value ${JSON.stringify(value)}`, () => {
  const x = setup(); x.get('offerPrice').value = value;
  assert.equal(x.c.validateCurrentStep(), false);
  assert.equal(x.get('offerPrice').attrs['aria-invalid'], 'true');
});
for (const id of ['optionDays', 'buyerApprovalDays', 'appraisalTerminateDays']) for (const value of ['1.5', '9007199254740992']) test(`${id} rejects fractional or unsafe whole days ${value}`, () => {
  const x = setup('investor', 'additional'); x.get(id).value = value;
  assert.equal(x.c.validateCurrentStep(), false);
  assert.match(x.statuses.at(-1), /whole number/);
});
for (const id of Object.keys(values).filter(id => !['offerPrice', 'loanAmount', 'loanYears'].includes(id))) test(`${id} accepts an explicit zero`, () => {
  const x = setup('homebuyer', id.startsWith('appraisalTerminate') ? 'additional' : 'partial'); x.get(id).value = '0';
  assert.equal(x.c.validateCurrentStep(), true);
});
for (const id of ['offerPrice', 'loanAmount', 'loanYears']) test(`${id} requires a positive value`, () => {
  const x = setup(); x.get(id).value = '0';
  assert.equal(x.c.validateCurrentStep(), false); assert.match(x.statuses.at(-1), /greater than 0/);
});
for (const value of ['0.50', '.75', '2.5e2']) test(`monetary decimal input ${value} is retained and accepted`, () => {
  const x = setup(); x.get('optionFee').value = value;
  assert.equal(x.c.validateCurrentStep(), true); assert.equal(x.get('optionFee').value, value);
});
test('cash financing does not validate hidden loan fields', () => {
  const x = setup(); x.radios.financing = 'cash'; x.radios.appraisalAddendum = '';
  x.get('appraisalAddendumBox').style.display = 'none';
  for (const id of ['loanAmount', 'loanYears', 'interestRateCap', 'interestFirstYears', 'originationCap', 'buyerApprovalDays']) x.get(id).value = '-1';
  assert.equal(x.c.validateCurrentStep(), true);
});
for (const id of ['offerPrice','earnestMoney','optionFee','loanAmount','downPayment','appraisalPartialValue','appraisalTerminateValue']) test(`${id} rejects fractions of a cent`, () => {
  const x=setup('agent',id==='appraisalTerminateValue'?'additional':'partial');x.get(id).value='1.005';
  assert.equal(x.c.validateCurrentStep(),false);assert.match(x.statuses.at(-1),/two decimal places/);
});
test('interest rates retain precision beyond two decimals',()=>{
  const x=setup();x.get('interestRateCap').value='6.125';x.get('originationCap').value='1.125';assert.equal(x.c.validateCurrentStep(),true);
});
test('invalid numeric edits retain the warning until corrected', () => {
  const x = setup(), field = x.get('optionDays');
  field.value = '-1'; assert.equal(x.c.validateCurrentStep(), false);
  field.value = '2.5'; x.c.clearValidationFeedbackFor(field);
  assert.equal(field.attrs['aria-invalid'], 'true'); assert.equal(field.dataset.validationInvalid, 'true');
  field.value = '0'; x.c.clearValidationFeedbackFor(field);
  assert.equal(field.attrs['aria-invalid'], undefined); assert.equal(field.dataset.validationInvalid, undefined);
  assert.equal(x.statuses.at(-1), '');
  assert.equal(x.c.validateCurrentStep(), true);
});
test('correcting one number does not hide another invalid answer', () => {
  const x = setup(); x.get('optionDays').value = '-1'; x.get('offerPrice').value = '-1';
  assert.equal(x.c.validateCurrentStep(), false);
  const last = x.statuses.at(-1); x.get('optionDays').value = '7'; x.c.clearValidationFeedbackFor(x.get('optionDays'));
  assert.equal(x.statuses.at(-1), last); assert.equal(x.get('offerPrice').attrs['aria-invalid'], 'true');
});
test('unlisted numeric and ordinary text fields retain required-field behavior', () => {
  const x = setup(), missing = []; x.get('unlistedField').value = 'non-numeric';
  x.c.requireField('unlistedField', 'answer', missing); assert.deepEqual(missing, []);
  x.get('unlistedField').value = ''; x.c.requireField('unlistedField', 'answer', missing);
  assert.deepEqual(missing, ['answer']);
});
