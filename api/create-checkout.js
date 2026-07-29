const Stripe = require('stripe');

const SELF_SERVE_PLAN = 'self';
const FALLBACK_ORIGIN = 'https://www.homeofferflow.com';

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
    const stripe = Stripe(process.env.STRIPE_SECRET_KEY);

    const {
      email,
      plan = SELF_SERVE_PLAN,
      offerData = {},
      priceId
    } = req.body || {};

    if (!email || !email.includes('@')) {
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

    const finalPriceId = process.env.STRIPE_BUYER_OFFER_PRICE_ID || 'price_1TYTYqAELe66ESXnhNQmydWn';

    const origin = safeOrigin(req);
    const safeSuccessUrl = `${origin}/?payment=success&email=${encodeURIComponent(email)}`;
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
