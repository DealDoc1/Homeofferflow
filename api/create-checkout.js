const Stripe = require('stripe');
const { saveCheckoutPayload, bindCheckoutPayload } = require('../lib/checkout_payload');

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
  const requireNumber = (keys, label, { positive = false, integer = false, money = false } = {}) => {
    const raw = first(keys);
    let text = typeof raw === 'string' || typeof raw === 'number' ? String(raw).trim() : '';
    if (money && /^\d{1,3}(?:,\d{3})+(?:\.\d+)?$/.test(text)) text = text.replace(/,/g, '');
    const value = Number(text);
    const numeric = /^(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(text);
    if (!text || !numeric || !Number.isFinite(value) || value < 0 || (positive && value <= 0) ||
        (integer && !Number.isSafeInteger(value))) {
      issues.push(integer ? `${label} must be a whole number of 0 or more.`
        : `${label} must be ${positive ? 'greater than 0' : '0 or more'}.`);
    } else if (money && (value !== Number(value.toFixed(2)) || !Number.isSafeInteger(Math.round(value * 100)))) {
      issues.push(`${label} must be a valid dollar amount with no more than two decimal places.`);
    }
  };
  requireNumber(['price', 'offerPrice'], 'Offer price', { positive: true, money: true });
  requireNumber(['earnest', 'earnestMoney'], 'Earnest money', { money: true });
  requireNumber(['optionFee'], 'Option fee', { money: true });
  requireNumber(['optionDays'], 'Option days', { integer: true });
  const financing = String(first(['financing', 'financingType']) || '').trim().toLowerCase();
  if (!['cash', 'conventional', 'fha', 'va', 'usda'].includes(financing)) {
    issues.push('Choose a supported financing type before checkout.');
  } else if (financing !== 'cash') {
    requireNumber(['loanAmount'], 'Loan amount', { positive: true, money: true });
    if (offer.downPayment !== undefined && offer.downPayment !== null && offer.downPayment !== '') {
      requireNumber(['downPayment'], 'Down payment', { money: true });
    }
    requireNumber(['loanYears', 'loanTermYears'], 'Loan term years', { positive: true });
    requireNumber(['interestRateCap', 'loanInterestCap'], 'Max interest rate');
    requireNumber(['interestFirstYears'], 'Interest cap years');
    requireNumber(['originationCap'], 'Origination cap');
    requireNumber(['buyerApprovalDays'], 'Buyer approval days', { integer: true });
    if (offer.appraisalAddendum === 'partial') {
      requireNumber(['appraisalPartialValue'], 'Partial waiver appraisal value', { money: true });
    } else if (offer.appraisalAddendum === 'additional') {
      requireNumber(['appraisalTerminateDays'], 'Appraisal termination days', { integer: true });
      requireNumber(['appraisalTerminateValue'], 'Appraisal termination value', { money: true });
    }
  }
  // Check populated optional money before a payable session can be created.
  // Percentages and deadlines deliberately do not use currency precision.
  const optionalMoney = [
    ['additionalEarnest','Additional earnest money'],['additionalEarnestMoney','Additional earnest money'],
    ['concessionAmount','Seller contribution'],['sellerConcessions','Seller contribution'],['sellerCredit','Seller credit'],['buyerExpenseCredit','Buyer expense credit'],
    ['brokerFeeAmount','Broker fee'],['brokerCompAmount','Broker compensation'],['buyerBrokerFeeAmount','Buyer broker fee'],['sellerBrokerCompAmount','Seller broker compensation'],['sellerBrokerComp','Seller broker compensation'],['buyerBrokerCompAmount','Buyer broker compensation'],['buyerToSellerBrokerCompAmount','Buyer broker contribution'],
    ['residentialServiceAmount','Residential service contract'],['residentialServiceContractAmount','Residential service contract'],['homeWarrantyAmount','Home warranty'],
    ['hoaTransferFeeCap','HOA transfer cap'],['hoaReserves','HOA reserve and transfer cap'],
    ['saleAdditionalEarnest','Sale-contingency earnest money'],
    ['bkupAdditionalEarnest','Backup earnest money'],['backupAdditionalEarnest','Backup earnest money'],['backupAddlEarnest','Backup earnest money'],
    ['bkupAdditionalOption','Backup option fee'],['backupAdditionalOption','Backup option fee'],['backupAdditionalOptionFee','Backup option fee'],['backupAddlOption','Backup option fee'],['backupAddlOptionFee','Backup option fee'],
    ['nonRealtyAmount','Personal property amount'],['nonRealtyItemsAmount','Personal property amount'],['nonRealtyAdditionalSum','Personal property amount'],
    ['appraisedValue','Appraised value'],
  ];
  for (const prefix of ['buyerTemporaryLease','sellerTemporaryLease','temporaryLease']) {
    for (const suffix of ['RentPerDay','TotalRent','Deposit','HoldoverPerDay']) optionalMoney.push([prefix+suffix,'Temporary lease amount']);
  }
  for (const prefix of ['buyerTempLease','sellerTempLease']) {
    for (const suffix of ['DailyRent','TotalRent','Deposit','HoldoverPerDay']) optionalMoney.push([prefix+suffix,'Temporary lease amount']);
  }
  for (const [key,label] of optionalMoney) {
    if (offer[key] !== undefined && offer[key] !== null && offer[key] !== '') requireNumber([key],label,{money:true});
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

    // Save before creating a payable session. Metadata's 50-key limit cannot
    // hold the advertised uploaded PDFs; use a private immutable reference.
    const reference = await saveCheckoutPayload(offerDataString);
    const metadata = {
      plan: SELF_SERVE_PLAN,
      payment_email: email,
      offer_payload_id: reference.id,
      offer_payload_sha256: reference.fingerprint
    };

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

    try {
      await bindCheckoutPayload(reference, session.id);
    } catch (error) {
      // Never return an unbound payable URL. Expire the unused session if the
      // database acknowledgement is lost; retain the row for reconciliation.
      try { await stripe.checkout.sessions.expire(session.id); } catch (_) {}
      throw error;
    }

    return res.status(200).json({ url: session.url });
  } catch (err) {
    console.error('Checkout preparation failed');
    return res.status(err.statusCode === 413 ? 413 : 503).json({
      error: err.statusCode === 413 ? err.message : 'Checkout could not be prepared. Please try again. No payment was started.'
    });
  }
};
