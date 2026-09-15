const Stripe = require('stripe');

const SELF_SERVE_PLAN = 'self';
const FALLBACK_ORIGIN = 'https://www.homeofferflow.com';

function offerNumberIssues(offer) {
  if (!offer || typeof offer !== 'object' || Array.isArray(offer)) {
    return ['Review your offer before opening checkout.'];
  }
  const issues = [];
  const first = keys => {
    const key = keys.find(key => Object.prototype.hasOwnProperty.call(offer, key));
    return key === undefined ? undefined : offer[key];
  };
  const requireNumber = (keys, label, { positive = false, integer = false } = {}) => {
    const raw = first(keys);
    const text = typeof raw === 'string' || typeof raw === 'number' ? String(raw).trim() : '';
    const value = Number(text);
    const numeric = /^(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(text);
    if (!text || !numeric || !Number.isFinite(value) || value < 0 || (positive && value <= 0) ||
        (integer && !Number.isSafeInteger(value))) {
      issues.push(integer ? `${label} must be a whole number of 0 or more.`
        : `${label} must be ${positive ? 'greater than 0' : '0 or more'}.`);
    }
  };
  requireNumber(['price', 'offerPrice'], 'Offer price', { positive: true });
  requireNumber(['earnest', 'earnestMoney'], 'Earnest money');
  requireNumber(['optionFee'], 'Option fee');
  requireNumber(['optionDays'], 'Option days', { integer: true });
  const financing = String(first(['financing', 'financingType']) || '').trim().toLowerCase();
  if (!['cash', 'conventional', 'fha', 'va', 'usda'].includes(financing)) {
    issues.push('Choose a supported financing type before checkout.');
  } else if (financing !== 'cash') {
    requireNumber(['loanAmount'], 'Loan amount', { positive: true });
    requireNumber(['loanYears', 'loanTermYears'], 'Loan term years', { positive: true });
    requireNumber(['interestRateCap', 'loanInterestCap'], 'Max interest rate');
    requireNumber(['interestFirstYears'], 'Interest cap years');
    requireNumber(['originationCap'], 'Origination cap');
    requireNumber(['buyerApprovalDays'], 'Buyer approval days', { integer: true });
    if (offer.appraisalAddendum === 'partial') {
      requireNumber(['appraisalPartialValue'], 'Partial waiver appraisal value');
    } else if (offer.appraisalAddendum === 'additional') {
      requireNumber(['appraisalTerminateDays'], 'Appraisal termination days', { integer: true });
      requireNumber(['appraisalTerminateValue'], 'Appraisal termination value');
    }
  }
  return issues;
}

function safeOrigin(req) {
  const candidate = req.headers.origin || (req.headers.host ? `https://${req.headers.host}` : FALLBACK_ORIGIN);
  try {
    const parsed = new URL(candidate);
    const host = parsed.hostname.toLowerCase();
    const allowed = host === 'homeofferflow.com'
      || host === 'www.homeofferflow.com'
      || host === 'homeofferflow.vercel.app'
      || (host.startsWith('homeofferflow-') && host.endsWith('.vercel.app'));
    return parsed.protocol === 'https:' && allowed ? parsed.origin : FALLBACK_ORIGIN;
  } catch (_err) {
    return FALLBACK_ORIGIN;
  }
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const {
      email: rawEmail,
      plan = SELF_SERVE_PLAN,
      offerData = {},
      priceId
    } = req.body || {};

    const email = typeof rawEmail === 'string' ? rawEmail.trim() : '';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return res.status(400).json({ error: 'Missing or invalid email' });
    }

    // The browser must never be able to select an arbitrary Stripe Price or
    // claim an unfulfilled support tier. HomeOfferFlow currently fulfills one
    // consumer product: the $99 self-service buyer-offer packet.
    if (String(plan || '').trim().toLowerCase() !== SELF_SERVE_PLAN) {
      return res.status(400).json({
        error: 'Only the Self-Serve buyer offer packet is currently available for checkout.'
      });
    }
    if (priceId) {
      return res.status(400).json({ error: 'Checkout price is selected by HomeOfferFlow, not the browser.' });
    }

    const issues = offerNumberIssues(offerData);
    if (issues.length) {
      return res.status(400).json({
        error: 'Check your price and financing answers before checkout. ' + issues.slice(0, 4).join(' '),
        issues
      });
    }

    const stripe = Stripe(process.env.STRIPE_SECRET_KEY);
    const finalPriceId = process.env.STRIPE_BUYER_OFFER_PRICE_ID || 'price_1TYTYqAELe66ESXnhNQmydWn';

    const origin = safeOrigin(req);
    // The return URL is visible to browser history, analytics, and potential
    // referrers. The buyer email remains in Stripe's server-side Checkout
    // session and the saved local payment state; never place it in the URL.
    const safeSuccessUrl = `${origin}/?payment=success`;
    const safeCancelUrl = `${origin}/?payment=cancelled`;

    const offerDataString = JSON.stringify({
      ...offerData,
      _paymentEmail: email,
      _plan: SELF_SERVE_PLAN
    });

    const chunks = offerDataString.match(/.{1,450}/g) || [];

    const metadata = {
      plan: SELF_SERVE_PLAN,
      payment_email: email,
      offer_parts: String(chunks.length)
    };

    chunks.forEach((chunk, i) => {
      metadata[`offer_${i}`] = chunk;
    });

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [{ price: finalPriceId, quantity: 1 }],
      mode: 'payment',
      customer_email: email,
      allow_promotion_codes: true,
      metadata,
      success_url: safeSuccessUrl,
      cancel_url: safeCancelUrl
    });

    return res.status(200).json({ url: session.url });
  } catch (err) {
    console.error('Stripe checkout error:', err);
    return res.status(500).json({ error: err.message || 'Stripe checkout failed' });
  }
};
