const Stripe = require('stripe');

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const stripe = Stripe(process.env.STRIPE_SECRET_KEY);
  const { priceId, email, plan, offerData } = req.body;

  try {
   const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [{ price: priceId, quantity: 1 }],
      mode: 'payment',
      customer_email: email,
     allow_promotion_codes: true,
      metadata: {
        offer_data: JSON.stringify(offerData || {}),
        plan: plan
      },
      success_url: `${req.headers.origin}/?success=true&plan=${plan}`,
      cancel_url: req.headers.origin,
    });

    res.status(200).json({ url: session.url });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
