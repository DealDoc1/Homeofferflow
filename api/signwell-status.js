const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const SIGNWELL_API_KEY = process.env.SIGNWELL_API_KEY || '';
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || process.env.ADMIN_ORDER_EMAIL || 'andrewchri@gmail.com,support@homeofferflow.com,andrew@ondemanddfw.com')
  .split(',')
  .map((e) => e.trim().toLowerCase())
  .filter(Boolean);

function json(res, status, payload) {
  res.status(status).json(payload);
}

async function verifyUser(req) {
  const auth = req.headers.authorization || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';

  if (!token) throw new Error('Missing auth token.');
  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
    throw new Error('Missing Supabase environment variables.');
  }

  const response = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: {
      Authorization: `Bearer ${token}`,
      apikey: SUPABASE_SERVICE_ROLE_KEY
    }
  });

  const user = await response.json().catch(() => ({}));

  if (!response.ok || !user.id || !user.email) {
    throw new Error('Could not verify signed-in user.');
  }

  const email = String(user.email || '').toLowerCase();

  return {
    id: user.id,
    email,
    isAdmin: ADMIN_EMAILS.includes(email)
  };
}

async function supabaseRequest(path, options = {}) {
  const response = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...options,
    headers: {
      apikey: SUPABASE_SERVICE_ROLE_KEY,
      Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });

  const text = await response.text().catch(() => '');
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw new Error(`Supabase request failed ${response.status}: ${text.slice(0, 1000)}`);
  }

  return data;
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

function cleanStatusLabel(status) {
  const raw = String(status || '').trim();
  const compact = raw.toLowerCase().replace(/[_\s-]+/g, ' ');

  if (!compact) return '';

  if (compact.includes('buyer signatures complete')) return 'Buyer Signatures Complete';
  if (compact.includes('awaiting')) return 'Awaiting Buyer Signature';
  if (compact.includes('buyer signature')) return 'Awaiting Buyer Signature';
  if (compact.includes('viewed')) return 'Viewed';
  if (compact.includes('in progress')) return 'Partially Signed';
  if (compact.includes('partial')) return 'Partially Signed';
  if (compact.includes('completed') || compact === 'complete' || compact.includes('signed')) {
    return 'Buyer Signatures Complete';
  }
  if (compact.includes('declined')) return 'Declined';
  if (compact.includes('expired')) return 'Expired';
  if (compact.includes('sent')) return 'Awaiting Buyer Signature';
  if (compact.includes('created') || compact.includes('generated') || compact.includes('draft')) {
    return 'Awaiting Buyer Signature';
  }

  return raw;
}

function safeMainOfferStatus(signwellStatus) {
  const clean = cleanStatusLabel(signwellStatus);

  // IMPORTANT:
  // hof_offers.status has a database constraint.
  // Keep detailed signature status in signwell_status.
  // Keep status limited to safer existing workflow values.
  if (clean === 'Buyer Signatures Complete') return 'Signed';
  if (clean === 'Partially Signed') return 'Generated';
  if (clean === 'Awaiting Buyer Signature') return 'Generated';
  if (clean === 'Viewed') return 'Generated';
  if (clean === 'Declined') return 'Declined';
  if (clean === 'Expired') return 'Expired';

  return 'Generated';
}

function extractDocumentStatus(document = {}) {
  const rawStatus =
    document.status ||
    document.document_status ||
    document.state ||
    document.data?.status ||
    document.data?.document_status ||
    '';

  return cleanStatusLabel(rawStatus);
}

function extractRecipientStatuses(document = {}) {
  const recipientSources = [
    document.recipients,
    document.signers,
    document.participants,
    document.data?.recipients,
    document.data?.signers,
    document.data?.participants
  ];

  const recipients = recipientSources.find((arr) => Array.isArray(arr)) || [];

  return recipients.map((r) => ({
    name: r.name || r.recipient_name || r.full_name || r.first_name || '',
    email: r.email || r.recipient_email || '',
    role: r.role || r.recipient_type || '',
    status: r.status || r.signing_status || r.recipient_status || '',
    completed_at: r.completed_at || r.signed_at || r.finished_at || null,
    viewed_at: r.viewed_at || null
  }));
}

function deriveStatus(document = {}) {
  const docStatus = extractDocumentStatus(document);
  const recipients = extractRecipientStatuses(document);

  if (docStatus) return docStatus;

  if (recipients.length) {
    const signerRows = recipients.filter((r) => String(r.role || '').toLowerCase() !== 'cc');
    const rows = signerRows.length ? signerRows : recipients;
    const statuses = rows.map((r) => cleanStatusLabel(r.status)).filter(Boolean);

    if (statuses.length && statuses.every((s) => s === 'Buyer Signatures Complete')) {
      return 'Buyer Signatures Complete';
    }

    if (statuses.some((s) => s === 'Buyer Signatures Complete' || s === 'Partially Signed')) {
      return 'Partially Signed';
    }

    if (statuses.some((s) => s === 'Viewed')) {
      return 'Viewed';
    }
  }

  return 'Awaiting Buyer Signature';
}

async function getOfferForUser(offerId, user) {
  if (!offerId) throw new Error('Missing offerId.');

  const filters = [
    `id=eq.${encodeURIComponent(offerId)}`,
    'select=*'
  ];

  if (!user.isAdmin) {
    filters.push(`user_id=eq.${encodeURIComponent(user.id)}`);
  }

  const rows = await supabaseRequest(`hof_offers?${filters.join('&')}`, {
    method: 'GET'
  });

  const offer = Array.isArray(rows) ? rows[0] : null;

  if (!offer) {
    throw new Error('Offer not found or access denied.');
  }

  return offer;
}

async function getSignWellDocument(documentId) {
  if (!SIGNWELL_API_KEY) throw new Error('Missing SIGNWELL_API_KEY.');
  if (!documentId) throw new Error('Missing SignWell document id.');

  const response = await fetch(`https://www.signwell.com/api/v1/documents/${encodeURIComponent(documentId)}`, {
    method: 'GET',
    headers: {
      'X-Api-Key': SIGNWELL_API_KEY,
      'Content-Type': 'application/json'
    }
  });

  const text = await response.text().catch(() => '');
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    throw new Error(`SignWell status lookup failed ${response.status}: ${text.slice(0, 1000)}`);
  }

  return data;
}

async function updateOfferStatus(offer, status, documentId, document, user) {
  const now = new Date().toISOString();
  const offerData = parseJsonObject(offer.offer_data);
  const recipientStatuses = extractRecipientStatuses(document);
  const cleanSignwellStatus = cleanStatusLabel(status);
  const mainStatus = safeMainOfferStatus(cleanSignwellStatus);

  const updatedOfferData = {
    ...offerData,
    signwellStatus: cleanSignwellStatus,
    signwellDocumentId: documentId,
    signwellLastStatusRefresh: now,
    signwellRecipientStatuses: recipientStatuses
  };

  const updateRows = await supabaseRequest(
    `hof_offers?id=eq.${encodeURIComponent(offer.id)}&select=id,user_id,signwell_document_id,signwell_status,status,last_updated`,
    {
      method: 'PATCH',
      headers: { Prefer: 'return=representation' },
      body: JSON.stringify({
        signwell_status: cleanSignwellStatus,
        status: mainStatus,
        offer_data: updatedOfferData,
        last_updated: now
      })
    }
  );

  await supabaseRequest('hof_offer_events', {
    method: 'POST',
    headers: { Prefer: 'return=minimal' },
    body: JSON.stringify({
      offer_id: offer.id,
      user_id: offer.user_id || user.id,
      event_type: 'signwell_status_refresh',
      status: cleanSignwellStatus,
      message: 'SignWell status manually refreshed from API.',
      metadata: {
        signwell_document_id: documentId,
        refreshed_by: user.email,
        recipient_statuses: recipientStatuses,
        signwell_status: document.status || document.document_status || null,
        main_status_saved: mainStatus
      },
      created_at: now
    })
  });

  return Array.isArray(updateRows) ? updateRows[0] : updateRows;
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return json(res, 405, { error: 'Method not allowed' });
  }

  try {
    const user = await verifyUser(req);

    const body =
      typeof req.body === 'object' && req.body
        ? req.body
        : JSON.parse(req.body || '{}');

    const offerId = body.offerId || body.offer_id || '';

    const offer = await getOfferForUser(offerId, user);
    const offerData = parseJsonObject(offer.offer_data);

    const documentId =
      offer.signwell_document_id ||
      offerData.signwellDocumentId ||
      offerData.signwell_document_id ||
      offerData.signwell?.document_id ||
      offerData.signwell?.response?.id ||
      offerData.signwell?.response?.document_id ||
      '';

    if (!documentId) {
      throw new Error('This offer does not have a SignWell document ID.');
    }

    const document = await getSignWellDocument(documentId);
    const status = deriveStatus(document);
    const updatedOffer = await updateOfferStatus(offer, status, documentId, document, user);

    return json(res, 200, {
      ok: true,
      offerId: offer.id,
      documentId,
      status: cleanStatusLabel(status),
      updatedOffer,
      signwellStatusRaw: document.status || document.document_status || null,
      recipientStatuses: extractRecipientStatuses(document)
    });
  } catch (err) {
    console.error('SignWell status refresh failed:', err);
    return json(res, 400, {
      error: err?.message || 'SignWell status refresh failed.'
    });
  }
};
