import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


NODE_TEST = r"""
const Module = require('module');
const originalLoad = Module._load;
let createdSession = null;
Module._load = function(request, parent, isMain) {
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
    offerData: { address: '123 Test Lane' },
    successUrl: 'https://evil.example/success',
    cancelUrl: 'https://evil.example/cancel'
  });
  if (valid.status !== 200) throw new Error('valid checkout was rejected');
  if (!createdSession) throw new Error('Stripe session was not created');
  if (createdSession.line_items[0].price !== 'price_server_selected') throw new Error('server price was not used');
  if (createdSession.success_url !== 'https://www.homeofferflow.com/?payment=success&email=buyer%40example.com') throw new Error('success redirect was not anchored');
  if (createdSession.cancel_url !== 'https://www.homeofferflow.com/?payment=cancelled') throw new Error('cancel redirect was not anchored');
  if (createdSession.metadata.plan !== 'self') throw new Error('metadata plan was not normalized');

  const badOrigin = await call({ email: 'buyer@example.com', plan: 'self' }, 'https://evil.example');
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
