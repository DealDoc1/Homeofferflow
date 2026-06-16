const Stripe = require('stripe');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || process.env.ADMIN_ORDER_EMAIL || 'andrewchri@gmail.com,support@homeofferflow.com,andrew@ondemanddfw.com')
  .split(',')
  .map((e) => e.trim().toLowerCase())
  .filter(Boolean);

function json(res, status, payload) {
  res.status(status).json(payload);
}

async function verifyAdmin(req) {
  const auth = req.headers.authorization || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  if (!token) throw new Error('Missing auth token.');
  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) throw new Error('Missing Supabase admin environment variables.');

  const response = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: {
      Authorization: `Bearer ${token}`,
      apikey: SUPABASE_SERVICE_ROLE_KEY
    }
  });

  const user = await response.json().catch(() => ({}));
  if (!response.ok || !user.email) throw new Error('Could not verify signed-in user.');

  const email = String(user.email || '').toLowerCase();
  if (!ADMIN_EMAILS.includes(email)) throw new Error('Admin access denied for this account.');

  return { id: user.id, email };
}

async function supabaseSelect(table, query = '') {
  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) return [];
  const url = `${SUPABASE_URL}/rest/v1/${table}${query}`;
  const response = await fetch(url, {
    headers: {
      apikey: SUPABASE_SERVICE_ROLE_KEY,
      Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    console.warn(`Admin dashboard query failed for ${table}:`, response.status, text);
    return [];
  }

  return response.json().catch(() => []);
}

async function selectRecent(table, orderCandidates = ['created_at', 'updated_at', 'last_updated'], limit = 50) {
  for (const order of orderCandidates) {
    const rows = await supabaseSelect(table, `?select=*&order=${encodeURIComponent(order)}.desc&limit=${limit}`);
    if (Array.isArray(rows) && rows.length) return rows;
  }
  return supabaseSelect(table, `?select=*&limit=${limit}`);
}

function parseJsonObject(value) {
  if (!value) return {};
  if (typeof value === 'object') return value;
  if (typeof value !== 'string') return {};
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch (err) {
    return {};
  }
}

function parseMetadataObject(metadata = {}) {
  const count = Number(metadata.offer_parts || 0);
  if (!count) return {};

  let raw = '';
  for (let i = 0; i < count; i++) raw += metadata[`offer_${i}`] || '';

  if (!raw) return {};

  try {
    return JSON.parse(raw);
  } catch (err) {
    console.warn('Could not parse checkout metadata offer payload:', err?.message || err);
    return {};
  }
}

function cleanStatusLabel(status) {
  const raw = String(status || '').trim();
  const compact = raw.toLowerCase().replace(/[_\s-]+/g, ' ');

  if (!compact) return '';
  if (compact.includes('awaiting')) return 'Awaiting Signature';
  if (compact.includes('viewed')) return 'Viewed';
  if (compact.includes('signed') || compact.includes('completed') || compact === 'complete') return 'Signed';
  if (compact.includes('declined')) return 'Declined';
  if (compact.includes('expired')) return 'Expired';
  if (compact.includes('sent')) return 'Awaiting Signature';
  if (compact.includes('created') || compact.includes('generated')) return 'Created';
  if (compact.includes('draft')) return 'Draft';
  if (compact.includes('delete')) return 'Deleted';

  return raw;
}

function getNestedSignWellStatus(offerData = {}) {
  return (
    offerData.signwellStatus ||
    offerData.signwell_status ||
    offerData.signwell?.status ||
    offerData.signwell?.response?.status ||
    offerData.signwell?.response?.document_status ||
    offerData.signwell?.response?.data?.status ||
    ''
  );
}

function getNestedSignWellDocumentId(offerData = {}) {
  return (
    offerData.signwellDocumentId ||
    offerData.signwell_document_id ||
    offerData.signwell?.document_id ||
    offerData.signwell?.id ||
    offerData.signwell?.response?.id ||
    offerData.signwell?.response?.document_id ||
    offerData.signwell?.response?.data?.id ||
    ''
  );
}

function normalizeOfferForAdmin(offer = {}) {
  const offerData = parseJsonObject(offer.offer_data);

  const documentId =
    offer.signwell_document_id ||
    getNestedSignWellDocumentId(offerData) ||
    '';

  const directSignwellStatus =
    offer.signwell_status ||
    getNestedSignWellStatus(offerData) ||
    '';

  let normalizedSignwellStatus = cleanStatusLabel(directSignwellStatus);
  const normalStatus = cleanStatusLabel(offer.status || '');

  // SignWell often returns a document id with status "Created" before later webhook events.
  // If a SignWell document exists and the current status is only created/generated/sent,
  // treat it as awaiting buyer signature.
  if (documentId && ['Created', 'Generated', 'Sent'].includes(normalizedSignwellStatus || normalStatus)) {
    normalizedSignwellStatus = 'Awaiting Signature';
  }

  const displayStatus = normalizedSignwellStatus || normalStatus || 'Draft';

  return {
    ...offer,
    offer_data: offerData,
    signwell_document_id: documentId || offer.signwell_document_id || null,
    signwell_status: normalizedSignwellStatus || offer.signwell_status || null,
    display_status: displayStatus,
    status: offer.status || displayStatus
  };
}

function buildStatusMetrics(offers = []) {
  return offers.reduce((acc, offer) => {
    const status = cleanStatusLabel(offer.signwell_status || offer.display_status || offer.status || '');
    const lower = status.toLowerCase();

    if (lower.includes('awaiting')) acc.awaitingSignature += 1;
    else if (lower.includes('viewed')) acc.viewed += 1;
    else if (lower.includes('signed')) acc.signed += 1;
    else if (lower.includes('declined')) acc.declined += 1;
    else if (lower.includes('expired')) acc.expired += 1;

    return acc;
  }, {
    awaitingSignature: 0,
    viewed: 0,
    signed: 0,
    declined: 0,
    expired: 0
  });
}

async function getStripeSessions() {
  if (!process.env.STRIPE_SECRET_KEY) return [];

  try {
    const stripe = Stripe(process.env.STRIPE_SECRET_KEY);
    const sessions = await stripe.checkout.sessions.list({ limit: 50 });
    return sessions.data || [];
  } catch (err) {
    console.warn('Stripe sessions unavailable for admin dashboard:', err?.message || err);
    return [];
  }
}

function normalizeShowingSession(session) {
  const metadata = session.metadata || {};
  const payload = parseMetadataObject(metadata);

  return {
    id: session.id,
    created_at: session.created ? new Date(session.created * 1000).toISOString() : null,
    payment_status: session.payment_status,
    amount_total: session.amount_total ? session.amount_total / 100 : 0,
    email: session.customer_email || metadata.payment_email || payload.buyerEmail || payload.showingEmail || '',
    metadata: {
      showingAddress: payload.showingAddress || payload.address || '',
      showingName: payload.buyerName || payload.showingName || payload.buyer1 || '',
      showingEmail: payload.buyerEmail || payload.showingEmail || session.customer_email || '',
      showingPhone: payload.showingPhone || payload.buyerPhone || '',
      showingDate: payload.showingDate || '',
      showingTime: payload.showingTime || '',
      showingNotes: payload.showingNotes || ''
    }
  };
}

module.exports = async (req, res) => {
  if (req.method !== 'GET') return json(res, 405, { error: 'Method not allowed' });

  try {
    const admin = await verifyAdmin(req);

    const [rawOffers, feedback, subscriptions, sessions] = await Promise.all([
      selectRecent('hof_offers', ['last_updated', 'generated_at', 'created_at'], 50),
      selectRecent('hof_feedback', ['created_at', 'updated_at'], 50),
      selectRecent('hof_subscriptions', ['updated_at', 'created_at'], 50),
      getStripeSessions()
    ]);

    const offers = (rawOffers || []).map(normalizeOfferForAdmin);
    const signwellMetrics = buildStatusMetrics(offers);

    const paidSessions = sessions.filter((s) => s.payment_status === 'paid');

    const showings = paidSessions
      .filter((s) => (s.metadata || {}).plan === 'showing-booking')
      .map(normalizeShowingSession);

    const offerCheckoutRevenue = paidSessions
      .filter((s) => (s.metadata || {}).plan !== 'showing-booking')
      .reduce((sum, s) => sum + (Number(s.amount_total || 0) / 100), 0);

    const showingRevenue = showings.reduce((sum, s) => sum + Number(s.amount_total || 0), 0);

    const offerVolume = offers.reduce((sum, o) => {
      return sum + (Number(o.offer_price || 0) || 0);
    }, 0);

    return json(res, 200, {
      ok: true,
      admin: { email: admin.email },
      metrics: {
        offerCount: offers.length,
        showingCount: showings.length,
        subscriptionCount: subscriptions.length,
        feedbackCount: feedback.length,
        offerVolume,
        offerCheckoutRevenue,
        showingRevenue,
        signwell: signwellMetrics,
        awaitingSignatureCount: signwellMetrics.awaitingSignature,
        viewedCount: signwellMetrics.viewed,
        signedCount: signwellMetrics.signed,
        declinedCount: signwellMetrics.declined,
        expiredCount: signwellMetrics.expired
      },
      offers,
      showings,
      subscriptions,
      feedback
    });
  } catch (err) {
    console.error('Admin dashboard error:', err);
    return json(res, 403, { error: err?.message || 'Admin dashboard failed.' });
  }
};
