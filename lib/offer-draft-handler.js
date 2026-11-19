const MAX_BODY_BYTES = 4 * 1024 * 1024;
const MAX_BUYER_NAME_LENGTH = 180;
const { normalizeOfferMoney } = require('./offer-money.cjs');
const DRAFT_FIELDS = [
  'role', 'property_address', 'property_city', 'property_state', 'property_zip',
  'property_county', 'buyer_name', 'buyer_email', 'buyer_phone', 'buyer2_name',
  'buyer2_email', 'seller_name', 'agent_name', 'agent_email', 'agent_phone',
  'agent_license', 'agent_brokerage', 'agent_broker_license', 'offer_price',
  'financing_type', 'loan_amount', 'down_payment', 'earnest_money', 'option_fee',
  'option_days', 'closing_date', 'title_company', 'escrow_agent', 'offer_data'
];
const PRIVATE_OFFER_DATA_KEYS = new Set([
  '_hof_signature_delivery', '_subscription_user_id', '_paragraph4_source_pdf_bytes',
  'backend_saved', 'signwell', 'signwellDocumentId', 'signwellStatus',
  'signwell_document_id', 'signwell_status', 'generatedAt', 'generated_at',
  'packetGeneratedAt', 'packetGenerationError', 'packetGenerationFailedAt',
  'packetGenerationFailureCategory', 'signwellLastStatusRefresh', 'signwellRecipientStatuses',
  'signingUrl', 'signing_url', 'embeddedSigningUrl', 'embedded_signing_url', 'recipients',
  '_hof_native_draft_request_id'
]);
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function send(res, status, payload) {
  return res.status(status).json(payload);
}

function parseBody(body) {
  if (typeof body === 'string') return JSON.parse(body || '{}');
  return body && typeof body === 'object' && !Array.isArray(body) ? body : {};
}

function preparedPacket(record) {
  let data = record?.offer_data || {};
  if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch (_) { data = {}; }
  }
  return Boolean(record?.generated_at || record?.signwell_document_id ||
    data.generatedAt || data.generated_at || data.signwellDocumentId || data.signwell_document_id ||
    data.signwell?.document_id || data.signwell?.response?.id ||
    Object.prototype.hasOwnProperty.call(data, '_hof_signature_delivery') ||
    !['draft', 'generation failed'].includes(String(record?.status || 'Draft').toLowerCase()));
}

function sanitizeDraft(input, userId, now) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    const error = new Error('Offer draft details are missing.');
    error.statusCode = 400;
    throw error;
  }
  const draft = {};
  for (const field of DRAFT_FIELDS) {
    if (!(field in input)) continue;
    const value = input[field];
    if (field === 'offer_data') {
      if (!value || typeof value !== 'object' || Array.isArray(value)) {
        const error = new Error('Offer draft details could not be saved.');
        error.statusCode = 400;
        throw error;
      }
      const safeData = JSON.parse(JSON.stringify(value));
      for (const key of PRIVATE_OFFER_DATA_KEYS) delete safeData[key];
      draft.offer_data = safeData;
    } else if (value === null || ['string', 'number'].includes(typeof value)) {
      draft[field] = value;
    } else {
      const error = new Error('Offer draft details could not be saved.');
      error.statusCode = 400;
      throw error;
    }
  }
  draft.user_id = userId;
  draft.last_updated = now;
  return draft;
}

function syncInterviewAnswers(draft, baseOfferData, quickDraft) {
  const offerData = baseOfferData && typeof baseOfferData === 'object' && !Array.isArray(baseOfferData)
    ? { ...baseOfferData }
    : {};
  if (quickDraft && Object.hasOwn(draft, 'buyer_name')) {
    offerData.buyer1 = String(draft.buyer_name || '').trim();
  }
  if (quickDraft && Object.hasOwn(draft, 'offer_price')) {
    // The interview uses price; existing offer readers may use either alias.
    offerData.price = draft.offer_price;
    offerData.offerPrice = draft.offer_price;
    delete offerData.offer_price;
  }
  if (Object.hasOwn(draft, 'buyer2_name')) {
    const coBuyerName = String(draft.buyer2_name || '').trim();
    if (coBuyerName) {
      offerData.buyer2 = coBuyerName;
      offerData.buyer2Name = coBuyerName;
    } else {
      delete offerData.buyer2;
      delete offerData.buyer2Name;
      delete offerData.buyer2Email;
      delete offerData.buyer2_email;
      // A removed co-buyer must not remain a potential signing recipient.
      draft.buyer2_email = null;
    }
  }
  draft.offer_data = offerData;
  return draft;
}

function makeError(statusCode, code, message) {
  const error = new Error(message);
  error.statusCode = statusCode;
  error.code = code;
  return error;
}

function normalizeOfferPrice(value) {
  const normalized = normalizeOfferMoney(value, { positive: true });
  return normalized.valid ? normalized.value : undefined;
}

function normalizeDraftOfferPrices(draft) {
  const offerData = draft.offer_data && typeof draft.offer_data === 'object' && !Array.isArray(draft.offer_data)
    ? draft.offer_data
    : null;
  const priceAnswerKeys = ['price', 'offerPrice', 'offer_price'];
  const answerKey = priceAnswerKeys.find(key => Object.prototype.hasOwnProperty.call(offerData || {}, key));
  const hasColumnPrice = Object.prototype.hasOwnProperty.call(draft, 'offer_price');
  if (!hasColumnPrice && !answerKey) return true;

  // Validate every supplied copy before propagating the canonical column
  // back into nested data. A zero in offer_data must not disappear just
  // because offer_price is blank.
  for (const key of priceAnswerKeys) {
    if (Object.prototype.hasOwnProperty.call(offerData || {}, key) &&
        normalizeOfferPrice(offerData[key]) === undefined) return false;
  }

  const rawPrice = hasColumnPrice ? draft.offer_price : offerData[answerKey];
  const normalizedPrice = normalizeOfferPrice(rawPrice);
  if (normalizedPrice === undefined) return false;

  draft.offer_price = normalizedPrice;
  if (offerData) {
    for (const key of priceAnswerKeys) {
      if (Object.prototype.hasOwnProperty.call(offerData, key)) offerData[key] = normalizedPrice;
    }
  }
  return true;
}

function createHandler({
  supabaseUrl = process.env.SUPABASE_URL,
  serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY,
  fetchImpl = globalThis.fetch,
  now = () => new Date().toISOString()
} = {}) {
  async function requestSupabase(path, options = {}) {
    const response = await fetchImpl(`${supabaseUrl}/rest/v1/${path}`, {
      ...options,
      headers: {
        apikey: serviceRoleKey,
        Authorization: `Bearer ${serviceRoleKey}`,
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    });
    const text = await response.text().catch(() => '');
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch (_) { data = null; }
    if (!response.ok) throw makeError(503, 'draft_storage_unavailable', 'We couldn’t save this draft. Try again.');
    return data;
  }

  return async function offerDraftHandler(req, res) {
    res.setHeader?.('Cache-Control', 'private, no-store');
    if (req.method !== 'POST') {
      res.setHeader?.('Allow', 'POST');
      return send(res, 405, { error: 'Method not allowed.' });
    }
    if (!supabaseUrl || !serviceRoleKey || typeof fetchImpl !== 'function') {
      return send(res, 503, { error: 'Draft saving is temporarily unavailable.' });
    }

    let body;
    try {
      const rawBody = typeof req.body === 'string' ? req.body : JSON.stringify(req.body || {});
      if (Buffer.byteLength(rawBody, 'utf8') > MAX_BODY_BYTES) {
        return send(res, 413, { error: 'This draft is too large to save. Remove an attachment and try again.' });
      }
      body = parseBody(req.body);
    } catch (_) {
      return send(res, 400, { error: 'Offer draft details could not be read.' });
    }
    if (Object.keys(body).some((key) => !['offerId', 'draft', 'clientRequestId', 'expectedLastUpdated'].includes(key))) {
      return send(res, 400, { error: 'Offer draft details could not be saved.' });
    }
    if (Object.prototype.hasOwnProperty.call(body, 'expectedLastUpdated') &&
        body.expectedLastUpdated !== null &&
        (typeof body.expectedLastUpdated !== 'string' || !body.expectedLastUpdated || body.expectedLastUpdated.length > 128)) {
      return send(res, 400, { error: 'Choose a valid draft version before saving.' });
    }

    const tokenMatch = String(req.headers?.authorization || '').match(/^Bearer\s+(.+)$/i);
    if (!tokenMatch) return send(res, 401, { error: 'Please sign in again to save this draft.' });

    let user;
    try {
      const authResponse = await fetchImpl(`${supabaseUrl}/auth/v1/user`, {
        headers: { apikey: serviceRoleKey, Authorization: `Bearer ${tokenMatch[1]}` }
      });
      user = authResponse.ok ? await authResponse.json() : null;
    } catch (_) {
      return send(res, 503, { error: 'We couldn’t confirm your sign-in. Try again.' });
    }
    if (!user?.id || !UUID_RE.test(String(user.id))) {
      return send(res, 401, { error: 'Please sign in again to save this draft.' });
    }

    try {
      const profiles = await requestSupabase(`hof_profiles?id=eq.${encodeURIComponent(user.id)}&select=role&limit=1`);
      const profileRole = Array.isArray(profiles) ? profiles[0]?.role : '';
      if (!['agent', 'brokerage_admin', 'investor'].includes(String(profileRole || '').toLowerCase())) {
        return send(res, 403, { error: 'Cloud offer drafts are available to signed-in agent accounts.' });
      }
      const draft = sanitizeDraft(body.draft, user.id, now());
      draft.role = String(profileRole).toLowerCase() === 'investor' ? 'investor' : 'agent';
      const quickDraft = !Object.hasOwn(body.draft, 'offer_data');
      if (!normalizeDraftOfferPrices(draft)) {
        return send(res, 422, {
          error: 'Enter an offer price greater than $0 with no more than two decimal places, or leave it blank.',
          code: 'invalid_draft'
        });
      }
      if (String(draft.buyer_name || '').length > MAX_BUYER_NAME_LENGTH) {
        return send(res, 422, {
          error: `Keep the buyer name to ${MAX_BUYER_NAME_LENGTH} characters or fewer.`,
          code: 'invalid_draft'
        });
      }
      if (String(draft.buyer2_name || '').length > MAX_BUYER_NAME_LENGTH) {
        return send(res, 422, {
          error: `Keep the co-buyer name to ${MAX_BUYER_NAME_LENGTH} characters or fewer.`,
          code: 'invalid_draft'
        });
      }
      const meaningful = Boolean(
        (String(draft.property_address || '').trim() && draft.property_address !== 'Untitled offer') ||
        (String(draft.buyer_name || '').trim() && draft.buyer_name !== 'Unnamed buyer') ||
        Number(draft.offer_price) > 0
      );
      if (!meaningful) return send(res, 422, { error: 'Add offer details before saving a cloud draft.', code: 'empty_draft' });

      if (body.offerId == null || body.offerId === '') {
        if (quickDraft || Object.hasOwn(draft, 'buyer2_name')) {
          syncInterviewAnswers(draft, draft.offer_data, quickDraft);
        }
        const clientRequestId = String(body.clientRequestId || '').trim().toLowerCase();
        if (clientRequestId && !UUID_RE.test(clientRequestId)) {
          return send(res, 400, { error: 'This draft request could not be confirmed.' });
        }
        if (clientRequestId) {
          const lookup = new URLSearchParams({
            user_id: `eq.${user.id}`,
            deleted_at: 'is.null',
            'offer_data->>_hof_native_draft_request_id': `eq.${clientRequestId}`,
            select: 'id,status,last_updated,buyer_name,buyer2_name,offer_price',
            limit: '1'
          });
          const existing = await requestSupabase(`hof_offers?${lookup}`);
          const saved = Array.isArray(existing) ? existing[0] : null;
          if (saved?.id) {
            if (String(saved.buyer_name || '').trim() !== String(draft.buyer_name || '').trim() ||
                String(saved.buyer2_name || '').trim() !== String(draft.buyer2_name || '').trim() ||
                Number(saved.offer_price || 0) !== Number(draft.offer_price || 0)) {
              return send(res, 409, {
                error: 'This save attempt already created a draft with different details. Refresh your offers and review it before starting another draft.',
                code: 'draft_request_conflict'
              });
            }
            return send(res, 200, {
              ok: true,
              draft: { id: saved.id, status: saved.status, last_updated: saved.last_updated },
              recovered: true
            });
          }
          draft.offer_data = { ...(draft.offer_data || {}), _hof_native_draft_request_id: clientRequestId };
          // The existing offer primary key serializes concurrent attempts with
          // this request key; one insert wins and the other can recover it.
          draft.id = clientRequestId;
        }
        draft.status = 'Draft';
        const recoverNativeCreate = async () => {
          const recoveryQuery = new URLSearchParams({
            id: `eq.${clientRequestId}`,
            user_id: `eq.${user.id}`,
            deleted_at: 'is.null',
            'offer_data->>_hof_native_draft_request_id': `eq.${clientRequestId}`,
            select: 'id,status,last_updated,buyer_name,buyer2_name,offer_price',
            limit: '1'
          });
          const rows = await requestSupabase(`hof_offers?${recoveryQuery}`);
          const existing = Array.isArray(rows) ? rows[0] : null;
          if (!existing?.id) return null;
          if (String(existing.buyer_name || '').trim() !== String(draft.buyer_name || '').trim() ||
              String(existing.buyer2_name || '').trim() !== String(draft.buyer2_name || '').trim() ||
              Number(existing.offer_price || 0) !== Number(draft.offer_price || 0)) {
            return {
              status: 409,
              payload: {
                error: 'This save attempt already created a draft with different details. Refresh your offers and review it before starting another draft.',
                code: 'draft_request_conflict'
              }
            };
          }
          return {
            status: 200,
            payload: {
              ok: true,
              draft: { id: existing.id, status: existing.status, last_updated: existing.last_updated },
              recovered: true
            }
          };
        };
        let inserted;
        try {
          inserted = await requestSupabase('hof_offers?select=id,status,last_updated', {
            method: 'POST', headers: { Prefer: 'return=representation' }, body: JSON.stringify(draft)
          });
        } catch (error) {
          if (clientRequestId) {
            const recovered = await recoverNativeCreate();
            if (recovered) return send(res, recovered.status, recovered.payload);
          }
          throw error;
        }
        const saved = Array.isArray(inserted) ? inserted[0] : null;
        if (!saved?.id) {
          const recovered = clientRequestId ? await recoverNativeCreate() : null;
          if (recovered) return send(res, recovered.status, recovered.payload);
          throw makeError(503, 'draft_storage_unavailable', 'We couldn’t save this draft. Try again.');
        }
        return send(res, 201, { ok: true, draft: saved });
      }

      const offerId = String(body.offerId);
      if (!UUID_RE.test(offerId)) return send(res, 400, { error: 'Choose a valid draft to save.' });
      const rows = await requestSupabase(`hof_offers?id=eq.${encodeURIComponent(offerId)}&user_id=eq.${encodeURIComponent(user.id)}&deleted_at=is.null&select=id,status,generated_at,signwell_document_id,offer_data,last_updated&limit=1`);
      const current = Array.isArray(rows) ? rows[0] : null;
      if (!current) return send(res, 404, { error: 'That offer is unavailable.' });
      if (preparedPacket(current)) {
        return send(res, 409, { error: 'This offer is already prepared. Save changes as a new draft.', code: 'offer_prepared' });
      }
      if (Object.prototype.hasOwnProperty.call(body, 'expectedLastUpdated') &&
          body.expectedLastUpdated !== (current.last_updated ?? null)) {
        return send(res, 409, {
          error: 'This draft changed after you opened it. Your changes were not saved. Refresh your offers and reopen the latest draft.',
          code: 'offer_draft_conflict'
        });
      }

      if (quickDraft || Object.hasOwn(draft, 'buyer2_name')) {
        let existingOfferData = current.offer_data;
        if (typeof existingOfferData === 'string') {
          try { existingOfferData = JSON.parse(existingOfferData); } catch (_) { existingOfferData = {}; }
        }
        syncInterviewAnswers(draft, quickDraft ? existingOfferData : draft.offer_data, quickDraft);
      }

      const version = current.last_updated == null ? 'is.null' : `eq.${current.last_updated}`;
      const query = new URLSearchParams({
        id: `eq.${offerId}`,
        user_id: `eq.${user.id}`,
        deleted_at: 'is.null',
        last_updated: version,
        status: current.status == null ? 'is.null' : `eq.${current.status}`,
        generated_at: 'is.null',
        signwell_document_id: current.signwell_document_id == null ? 'is.null' : `eq.${current.signwell_document_id}`,
        select: 'id,status,last_updated'
      });
      const updated = await requestSupabase(`hof_offers?${query}`, {
        method: 'PATCH', headers: { Prefer: 'return=representation' }, body: JSON.stringify(draft)
      });
      const saved = Array.isArray(updated) ? updated[0] : null;
      if (!saved?.id) return send(res, 409, { error: 'This draft changed while you were editing. Refresh and try again.', code: 'offer_draft_conflict' });
      return send(res, 200, { ok: true, draft: saved });
    } catch (error) {
      const status = [400, 401, 404, 409, 413, 422].includes(error?.statusCode) ? error.statusCode : 503;
      return send(res, status, {
        error: error?.message || 'We couldn’t save this draft. Try again.',
        ...(error?.code ? { code: error.code } : {})
      });
    }
  };
}

module.exports = createHandler();
module.exports.createHandler = createHandler;
module.exports.preparedPacket = preparedPacket;
module.exports.sanitizeDraft = sanitizeDraft;
module.exports.MAX_BUYER_NAME_LENGTH = MAX_BUYER_NAME_LENGTH;
