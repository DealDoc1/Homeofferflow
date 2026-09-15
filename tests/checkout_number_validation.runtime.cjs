const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const { test } = require('node:test');
const repo = path.resolve(__dirname, '..');
const source = process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git', ['show', `${process.env.HOF_TEST_SOURCE_REF}:api/create-checkout.js`], { cwd: repo, encoding: 'utf8' })
  : fs.readFileSync(path.join(repo, 'api/create-checkout.js'), 'utf8');
const cash = { price: '500000', earnest: '0', optionFee: '0', optionDays: '0', financing: 'cash' };
const financed = { ...cash, financing: 'conventional', loanAmount: '450000', loanYears: '30', interestRateCap: '0',
  interestFirstYears: '30', originationCap: '0', buyerApprovalDays: '21', appraisalAddendum: 'none' };
async function call(offerData, email = 'buyer@example.test', extra = {}) {
  const requests = [], initializations = [], saved = [];
  const module = { exports: {} };
  vm.runInNewContext(source, { module, URL, console: { error() {} },
    process: { env: { STRIPE_SECRET_KEY: 'fake-key', STRIPE_BUYER_OFFER_PRICE_ID: 'price-server' } },
    require(name) {
      if (name === '../lib/checkout_payload') return {
        saveCheckoutPayload: async payload => { saved.push(payload); return { id: 'private-ref', fingerprint: 'hash' }; },
        bindCheckoutPayload: async () => {}
      };
      assert.equal(name, 'stripe');
      return key => { initializations.push(key); return { checkout: { sessions: { create: async payload => {
        requests.push(payload); return { url: 'https://checkout.example.test/session' };
      } } } }; };
    },
  });
  const result = {};
  const res = { status(code) { result.status = code; return this; }, json(body) { result.body = body; return this; } };
  await module.exports({ method: 'POST', headers: { origin: 'https://www.homeofferflow.com' }, body: { email, plan: 'self', offerData, ...extra } }, res);
  return { ...result, requests, initializations, saved };
}
async function rejected(offer, email) {
  const result = await call(offer, email);
  assert.equal(result.status, 400);
  assert.equal(result.requests.length, 0, 'no Stripe checkout for invalid offer');
  assert.equal(result.initializations.length, 0, 'validation precedes provider initialization');
  return result;
}
for (const value of [undefined, null, [], 'not an offer', 3, false, {}]) test(`invalid offer shape ${JSON.stringify(value)} is rejected before Stripe`, async () => {
  await rejected(value);
});
for (const id of ['price', 'earnest', 'optionFee', 'optionDays']) {
  for (const value of ['-1', '', null, false, [], {}, '1e309', 'NaN', '0x10']) test(`${id} invalid value ${JSON.stringify(value)} cannot open checkout`, async () => {
    await rejected({ ...cash, [id]: value });
  });
  test(`missing ${id} cannot open checkout`, async () => { const offer = { ...cash }; delete offer[id]; await rejected(offer); });
}
for (const id of ['loanAmount', 'loanYears', 'interestRateCap', 'interestFirstYears', 'originationCap', 'buyerApprovalDays']) {
  for (const value of ['-1', '', null]) test(`financing ${id} ${JSON.stringify(value)} cannot open checkout`, async () => {
    await rejected({ ...financed, [id]: value });
  });
}
for (const id of ['price', 'loanAmount', 'loanYears']) test(`${id} zero is not valid for a financed purchase`, async () => {
  await rejected({ ...financed, [id]: 0 });
});
for (const id of ['optionDays', 'buyerApprovalDays']) for (const value of [1.5, '9007199254740992']) test(`${id} requires safe whole days: ${value}`, async () => {
  await rejected({ ...financed, [id]: value });
});
for (const type of ['partial', 'additional']) test(`${type} appraisal numbers are required when selected`, async () => {
  await rejected({ ...financed, appraisalAddendum: type });
});
for (const [key, value] of [['appraisalPartialValue', -1], ['appraisalTerminateValue', -1], ['appraisalTerminateDays', 0.5]]) test(`invalid appraisal ${key} rejected`, async () => {
  await rejected({ ...financed, appraisalAddendum: key === 'appraisalPartialValue' ? 'partial' : 'additional',
    appraisalPartialValue: 0, appraisalTerminateValue: 0, appraisalTerminateDays: 0, [key]: value });
});
for (const type of ['cash', 'conventional', 'fha', 'va', 'usda']) test(`${type} retains valid zero fees and server-owned price`, async () => {
  const offer = { ...financed, financing: type };
  const result = await call(offer);
  assert.equal(result.status, 200);
  assert.equal(result.requests.length, 1);
  const request = result.requests[0];
  assert.equal(request.line_items[0].price, 'price-server');
  const recovered = JSON.parse(result.saved[0]);
  for (const key of Object.keys(offer)) assert.equal(recovered[key], offer[key]);
  assert.equal(recovered._paymentEmail, 'buyer@example.test');
});
test('cash ignores stale hidden financing fields', async () => {
  const result = await call({ ...financed, financing: 'cash', loanAmount: -1, loanYears: '', interestRateCap: -1 });
  assert.equal(result.status, 200); assert.equal(result.requests.length, 1);
});
test('legacy price and earnest field aliases remain supported', async () => {
  const offer = { ...cash, offerPrice: cash.price, earnestMoney: cash.earnest };
  delete offer.price; delete offer.earnest;
  assert.equal((await call(offer)).status, 200);
});
test('invalid primary field is not hidden by a valid legacy alias', async () => {
  await rejected({ ...cash, price: -1, offerPrice: 500000 });
});
for (const financing of ['', 'unknown', 'seller_financing', null, {}, []]) test(`unsupported financing ${JSON.stringify(financing)} is rejected before payment`, async () => {
  await rejected({ ...cash, financing });
});
for (const email of [null, 123, [], {}, 'a@', '@example.test', 'a b@example.test', 'buyer@example.test\nother']) test(`invalid receipt email ${JSON.stringify(email)} is rejected`, async () => {
  await rejected(cash, email);
});
test('receipt email is trimmed consistently in provider and metadata', async () => {
  const result = await call(cash, ' buyer@example.test ');
  assert.equal(result.status, 200);
  assert.equal(result.requests[0].customer_email, 'buyer@example.test');
  assert.equal(result.requests[0].metadata.payment_email, 'buyer@example.test');
});
test('errors do not reflect arbitrary offer contents', async () => {
  const result = await rejected({ ...cash, price: '<script>private-value</script>' });
  assert.equal(JSON.stringify(result.body).includes('private-value'), false);
  assert.match(result.body.error, /Check your price and financing/);
});
for (const text of ['Before\u2028After', 'Before\u2029After', 'Name: José 李 🏡', 'a\r\nb\nc', 'e\u0301']) test(`checkout preserves text ${JSON.stringify(text)}`, async () => {
  const offer = { ...cash, repairsText: text, legalDescription: text.repeat(100) };
  const result = await call(offer);
  assert.equal(result.status, 200);
  assert.ok(Object.values(result.requests[0].metadata).every(value => value.length <= 500));
  const recovered = JSON.parse(result.saved[0]);
  assert.equal(recovered.repairsText, offer.repairsText);
  assert.equal(recovered.legalDescription, offer.legalDescription);
});
test('a non-BMP character on the former metadata boundary is preserved', async () => {
  const prefixLength = JSON.stringify({ ...cash, repairsText: '' }).slice(0, -2).length;
  const offer = { ...cash, repairsText: 'x'.repeat(449 - prefixLength) + '🏡' + 'end' };
  const result = await call(offer);
  assert.equal(result.status, 200);
  assert.equal(JSON.parse(result.saved[0]).repairsText, offer.repairsText);
});
