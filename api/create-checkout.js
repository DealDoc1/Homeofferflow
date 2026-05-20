const Stripe = require('stripe');

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const stripe = Stripe(process.env.STRIPE_SECRET_KEY);

  const { priceId, email, plan, offerData } = req.body;

  if (!priceId || !email || !plan || !offerData) {
    return res.status(400).json({
      error: 'Missing priceId, email, plan, or offerData'
    });
  }

  try {
    const offerDataString = JSON.stringify({
      ...offerData,
      _paymentEmail: email,
      _plan: plan
    });

    if (offerDataString.length > 4500) {
      return res.status(400).json({
        error: 'Offer data is too large for Stripe metadata. Need server-side storage.'
      });
    }

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [{ price: priceId, quantity: 1 }],
      mode: 'payment',
      customer_email: email,
      allow_promotion_codes: true,
      metadata: {
        offer_data: offerDataString,
        plan: plan
      },
      success_url: `${req.headers.origin}/?success=true&plan=${encodeURIComponent(plan)}`,
      cancel_url: req.headers.origin,
    });

    return res.status(200).json({ url: session.url });

  } catch (err) {
    console.error('Stripe checkout error:', err);
    return res.status(500).json({ error: err.message });
  }
};
