// Server-only, non-delivering check using the same builder as paid fulfillment.
// Never send this signed request to a browser-selected host or follow redirects.
const { createHmac } = require('node:crypto');
const { Buffer } = require('node:buffer');
const FAILURE = 'Your document packet could not be checked. Please try again. No payment was started.';

function preflightOrigin(env) {
  if (!env.VERCEL_ENV || env.VERCEL_ENV === 'production') return 'https://www.homeofferflow.com';
  const host = String(env.VERCEL_URL || '');
  if (!/^homeofferflow-[a-z0-9-]+\.vercel\.app$/i.test(host)) throw new Error(FAILURE);
  return `https://${host}`;
}

function cleanCheckoutOffer(offer) {
  return Object.fromEntries(Object.entries(offer).filter(([key]) => !key.startsWith('_')
    && key !== 'paragraph4SourceRevisions'));
}

async function preflightAssumptionPacket(offer, { env = process.env, fetcher = globalThis.fetch, now = Date.now } = {}) {
  const clean = cleanCheckoutOffer(offer);
  const body = JSON.stringify({ action: 'checkout_packet_preflight', offerData: clean });
  if (Buffer.byteLength(body, 'utf8') > 4 * 1024 * 1024) {
    const error = new Error('Your offer packet is too large. Reduce the attachment sizes and try again.');
    error.statusCode = 413;
    throw error;
  }
  const secret = env.STRIPE_INTERNAL_CHECKOUT_FORWARD_SECRET || env.STRIPE_SUBSCRIPTION_WEBHOOK_SECRET;
  if (!secret) throw new Error(FAILURE);
  const origin = preflightOrigin(env);
  const timestamp = String(Math.floor(now() / 1000));
  // Domain separation: this signature cannot authorize a paid delivery event.
  const signature = createHmac('sha256', secret).update(`${timestamp}.checkout-preflight.`).update(body).digest('hex');
  let response, result;
  try {
    response = await fetcher(`${origin}/api/fill-pdf.py`, {
      method: 'POST', redirect: 'error', signal: AbortSignal.timeout(45000),
      headers: { 'Content-Type': 'application/json',
        'X-HomeOfferFlow-Preflight-Signature': `t=${timestamp},v1=${signature}` }, body
    });
    result = await response.json();
  } catch (_) { throw new Error(FAILURE); }
  if (!response.ok) {
    if ([400, 422].includes(response.status) && result?.code === 'checkout_answers_invalid'
        && typeof result.error === 'string' && result.error.length < 2000) {
      const error = new Error(result.error);
      error.statusCode = 422;
      throw error;
    }
    throw new Error(FAILURE);
  }
  const totals = result?.totals;
  if (result?.ok !== true || !Number.isInteger(result.pages) || result.pages < 14
      || !totals || !['price','loanAmount','downPayment'].every(key =>
        typeof totals[key] === 'string' && /^\d+(?:\.\d{1,2})?$/.test(totals[key]))) throw new Error(FAILURE);
  return { ...clean, ...totals, financing: 'assumption', loanAssumption: 'yes' };
}

module.exports = { preflightAssumptionPacket, preflightOrigin, cleanCheckoutOffer };
