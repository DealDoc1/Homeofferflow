// Backend-only packet storage. Stripe metadata contains no offer answers/PDFs.
const { randomUUID, createHash } = require('node:crypto');
const MAX_BYTES = 4 * 1024 * 1024;
const FAILURE = 'Your offer could not be saved for checkout. Please try again. No payment was started.';

function storage(env, fetcher) {
  const key = env.SUPABASE_SERVICE_ROLE_KEY || env.SUPABASE_SERVICE_ROLE || env.SUPABASE_SERVICE_KEY;
  const url = (env.SUPABASE_URL || '').replace(/\/$/, '');
  if (!key || !url) throw new Error(FAILURE);
  return async (method, query, body) => {
    try {
      const response = await fetcher(`${url}/rest/v1/hof_checkout_payloads?${query}`, {
        method, redirect: 'error', signal: AbortSignal.timeout(20000),
        headers: { apikey: key, Authorization: `Bearer ${key}`, 'Content-Type': 'application/json', Prefer: 'return=representation' },
        body: JSON.stringify(body)
      });
      if (!response.ok) throw new Error(FAILURE);
      const rows = await response.json();
      if (!Array.isArray(rows) || rows.length !== 1) throw new Error(FAILURE);
      return rows[0];
    } catch (_) { throw new Error(FAILURE); }
  };
}

async function saveCheckoutPayload(payload, { env = process.env, fetcher = globalThis.fetch } = {}) {
  if (Buffer.byteLength(payload, 'utf8') > MAX_BYTES) {
    const error = new Error('Your offer packet is too large. Reduce the attachment sizes and try again.');
    error.statusCode = 413;
    throw error;
  }
  const id = randomUUID(), fingerprint = createHash('sha256').update(payload, 'utf8').digest('hex');
  const request = storage(env, fetcher);
  const row = await request('POST', 'select=id,payload_sha256', { id, payload_text: payload, payload_sha256: fingerprint });
  if (row.id !== id || row.payload_sha256 !== fingerprint) throw new Error(FAILURE);
  return { id, fingerprint };
}

async function bindCheckoutPayload(reference, sessionId, { env = process.env, fetcher = globalThis.fetch } = {}) {
  if (!/^cs_[A-Za-z0-9_]+$/.test(sessionId || '')) throw new Error(FAILURE);
  const request = storage(env, fetcher);
  const query = new URLSearchParams({ id: `eq.${reference.id}`, payload_sha256: `eq.${reference.fingerprint}`,
    stripe_session_id: 'is.null', select: 'id,payload_sha256,stripe_session_id' });
  const row = await request('PATCH', query, { stripe_session_id: sessionId });
  if (row.id !== reference.id || row.payload_sha256 !== reference.fingerprint || row.stripe_session_id !== sessionId) {
    throw new Error(FAILURE);
  }
}

module.exports = { saveCheckoutPayload, bindCheckoutPayload, MAX_BYTES };
