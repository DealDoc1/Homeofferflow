const Stripe = require('stripe');

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const stripe = Stripe(process.env.STRIPE_SECRET_KEY);
  const { priceId, email, plan, offerData, successUrl, cancelUrl } = req.body;

  if (!priceId || !email || !plan || !offerData) {
    return res.status(400).json({ error: 'Missing priceId, email, plan, or offerData' });
  }

  try {
    const origin =
      req.headers.origin ||
      (req.headers.host ? `https://${req.headers.host}` : 'https://www.homeofferflow.com');

    const safeSuccessUrl =
      successUrl && String(successUrl).startsWith('http')
        ? successUrl
        : `${origin}/?payment=success&plan=${encodeURIComponent(plan)}`;

    const safeCancelUrl =
      cancelUrl && String(cancelUrl).startsWith('http')
        ? cancelUrl
        : `${origin}/?payment=cancelled&plan=${encodeURIComponent(plan)}`;

    const offerDataString = JSON.stringify({
      ...offerData,
      _paymentEmail: email,
      _plan: plan
    });

    const chunks = offerDataString.match(/.{1,450}/g) || [];

    const metadata = {
      plan,
      payment_email: email,
      offer_parts: String(chunks.length)
    };

    chunks.forEach((chunk, i) => {
      metadata[`offer_${i}`] = chunk;
    });

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [{ price: priceId, quantity: 1 }],
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
    return res.status(500).json({ error: err.message });
  }
};
