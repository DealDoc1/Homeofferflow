import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


NODE_TEST = r"""
const Module = require('module');
const originalLoad = Module._load;
let createdSession = null;
let savedPayloads = 0;
Module._load = function(request, parent, isMain) {
  if (request === '../lib/checkout_payload') return {
    saveCheckoutPayload: async () => {
      savedPayloads++;
      return {id:'private-ref', fingerprint:'hash'};
    },
    bindCheckoutPayload: async () => {}
  };
  if (request === 'stripe') {
    return function() {
      return { checkout: { sessions: { create: async (payload) => {
        createdSession = payload;
        return { url: 'https://checkout.stripe.test/session' };
      } } } };
    };
  }
  return originalLoad.apply(this, arguments);
};

process.env.STRIPE_SECRET_KEY = 'sk_test_local';
process.env.STRIPE_BUYER_OFFER_PRICE_ID = 'price_server_selected';
const handler = require('./api/create-checkout.js');

function call(body, origin = 'https://www.homeofferflow.com') {
  return new Promise((resolve, reject) => {
    const req = { method: 'POST', body, headers: { origin } };
    const res = {
      statusCode: 200,
      status(code) { this.statusCode = code; return this; },
      json(payload) { resolve({ status: this.statusCode, payload }); }
    };
    Promise.resolve(handler(req, res)).catch(reject);
  });
}

(async () => {
  const unsupported = await call({ email: 'buyer@example.com', plan: 'attorney' });
  if (unsupported.status !== 400 || !/Self-Serve/.test(unsupported.payload.error || '')) throw new Error('unsupported plan was accepted');

  const clientPrice = await call({ email: 'buyer@example.com', plan: 'self', priceId: 'price_attacker' });
  if (clientPrice.status !== 400 || !/selected by HomeOfferFlow/.test(clientPrice.payload.error || '')) throw new Error('client price was accepted');

  const valid = await call({
    email: 'buyer@example.com',
    plan: 'self',
    offerData: { address: '123 Test Lane', price: '500000', earnest: '5000', optionFee: '250', optionDays: '7', financing: 'cash' },
    successUrl: 'https://evil.example/success',
    cancelUrl: 'https://evil.example/cancel'
  });
  if (valid.status !== 200) throw new Error('valid checkout was rejected');
  if (!createdSession) throw new Error('Stripe session was not created');
  if (createdSession.line_items[0].price !== 'price_server_selected') throw new Error('server price was not used');
  if (createdSession.success_url !== 'https://www.homeofferflow.com/?payment=success') throw new Error('success redirect was not anchored');
  if (createdSession.cancel_url !== 'https://www.homeofferflow.com/?payment=cancelled') throw new Error('cancel redirect was not anchored');
  if (createdSession.metadata.plan !== 'self') throw new Error('metadata plan was not normalized');

  const baseOffer = {price: '500000', earnest: '5000', optionFee: '250', optionDays: '7'};
  for (const financing of ['cash', 'conventional', 'fha', 'va', 'usda', 'assumption']) {
    const offer = {...baseOffer, financing, loanAmount:'400000', loanYears:'30',
      interestRateCap:'7', interestFirstYears:'30', originationCap:'1', buyerApprovalDays:'20'};
    for (const [water, paragraph] of [
      [{sellerWaterDisclosure:'exempt', sellerWaterProvider:'   '}, '7I(3)(e)'],
      [{waterDisclosure:'not_required', waterProvider:23}, '7I(3)(e)'],
      [{sellerWaterDisclosureStatus:'notRequired', waterDisclosureProvider:'X'.repeat(61)}, '7I(3)(e)'],
      [{sellerWaterDisclosure:'notReceived', waterDisclosureDays:'0'}, '7I(2)'],
      [{waterDisclosure:'no', sellerWaterDisclosureDays:'1.5'}, '7I(2)'],
    ]) {
      createdSession = null;
      const savedBefore = savedPayloads;
      const result = await call({email:'buyer@example.com', plan:'self', offerData:{...offer,...water}});
      if (result.status !== 400 || !result.payload.error.includes(paragraph) ||
          !result.payload.error.includes('No payment was started') || createdSession || savedPayloads !== savedBefore) {
        throw new Error('invalid water disclosure reached checkout or lost its correction message');
      }
    }
  }
  for (const water of [
    {},
    {sellerWaterDisclosure:'received', waterDisclosureDays:'0'},
    {waterDisclosure:'not_required', waterSourceProvider:'Distrito de Agua de San José'},
    {sellerWaterDisclosure:'exempt', sellerWaterProvider:'City of Sherman'},
    {sellerWaterDisclosure:'notReceived', waterDisclosureDays:'12'},
  ]) {
    const result = await call({email:'buyer@example.com', plan:'self', offerData:{...baseOffer,financing:'cash',...water}});
    if (result.status !== 200) throw new Error('valid water disclosure was rejected');
  }
  const terms = {sellerWaterDisclosure:"exempt", sellerWaterProvider:"City of Sherman", price: '500000', earnest: '5000', optionFee: '250', optionDays: '7', financing: 'cash'};
  for (const contribution of [
    {buyerBrokerCompType:'amount', buyerBrokerCompAmount:'0'},
    {buyerBrokerCompType:'amount'},
    {buyerBrokerCompType:'percent', buyerBrokerCompPercent:'101'},
  ]) {
    createdSession = null;
    const failure = await call({email:'buyer@example.com', plan:'self', offerData:{...terms,...contribution}});
    if (failure.status !== 400 || !failure.payload.error.includes('Buyer contribution') || createdSession) {
      throw new Error('invalid buyer contribution reached Stripe');
    }
  }

  const badOrigin = await call({ email: 'buyer@example.com', plan: 'self', offerData: {price: '500000', earnest: '5000', optionFee: '250', optionDays: '7', financing: 'cash'} }, 'https://evil.example');
  if (badOrigin.status !== 200 || createdSession.success_url.indexOf('https://www.homeofferflow.com/') !== 0) throw new Error('untrusted request origin was accepted');
  process.stdout.write('create-checkout runtime contract passed\n');
})().catch((error) => { console.error(error.stack || error); process.exit(1); });
"""


class CreateCheckoutRuntimeTests(unittest.TestCase):
    def test_server_enforces_fulfilled_plan_price_and_redirect_contract(self):
        result = subprocess.run(
            ["node", "-e", NODE_TEST],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("create-checkout runtime contract passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
