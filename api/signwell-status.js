const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const SIGNWELL_API_KEY = process.env.SIGNWELL_API_KEY || '';
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

  return {
    id: user.id,
    email: String(user.email || '').toLowerCase()
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
  const compact = String(status || '').trim().toLowerCase().replace(/[_\s-]+/g, ' ')
    .replace(/^document /, '');
  // Exact aliases only: "unsigned", "not sent" and unknown future values
  // must never inherit a successful state from a substring match.
  if (['buyer signatures complete', 'completed', 'complete'].includes(compact)) return 'Buyer Signatures Complete';
  if (['sent', 'shared', 'awaiting buyer signature', 'awaiting signature', 'awaiting signatures'].includes(compact)) return 'Awaiting Buyer Signature';
  if (compact === 'viewed') return 'Viewed';
  // SignWell's document_signed event concerns one signer, not the packet.
  if (['signed', 'pending', 'in progress', 'partial', 'partially signed'].includes(compact)) return 'Partially Signed';
  if (compact === 'declined') return 'Declined';
  if (compact === 'expired') return 'Expired';
  if (['canceled', 'cancelled'].includes(compact)) return 'Cancelled';
  if (compact === 'bounced') return 'Bounced';
  if (compact === 'error') return 'Error';
  if (['draft', 'created', 'generated', 'saved', 'draft not sent'].includes(compact)) return 'Draft - not sent';
  return '';
}

function safeMainOfferStatus(signwellStatus) {
  const clean = cleanStatusLabel(signwellStatus);

  // IMPORTANT:
  // hof_offers.status has a database constraint.
  // Keep detailed signature status in signwell_status.
  // Keep status limited to safer existing workflow values.
  if (clean === 'Buyer Signatures Complete') return 'Signed';
  if (clean === 'Partially Signed') return 'Partially Signed';
  if (clean === 'Awaiting Buyer Signature') return 'Sent for Signature';
  if (clean === 'Viewed') return 'Buyer Viewed';
  if (clean === 'Declined' || clean === 'Cancelled') return 'Rejected';
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

  // A present but unrecognized document state is not permission to infer
  // completion from an incomplete recipient list or overwrite saved state.
  if (document.status || document.document_status || document.state || document.data?.status || document.data?.document_status) {
    throw new Error('The signing service returned an unrecognized status. Your saved status has not changed.');
  }

  if (recipients.length) {
    const rows = recipients.filter((r) => !['cc', 'copy', 'carbon copy'].includes(String(r.role || '').trim().toLowerCase()));
    const statuses = rows.map((r) => cleanStatusLabel(r.status));

    // Recipient progress is useful, but only a document-level completion
    // confirms finalization and permits downloading the completed packet.
    if (statuses.some((s) => s === 'Buyer Signatures Complete' || s === 'Partially Signed')) {
      return 'Partially Signed';
    }

    if (statuses.some((s) => s === 'Viewed')) {
      return 'Viewed';
    }
    if (statuses.some((s) => s === 'Awaiting Buyer Signature')) {
      return 'Awaiting Buyer Signature';
    }
  }

  throw new Error('The signing service did not confirm the document status. Your saved status has not changed.');
}

async function getOfferForUser(offerId, user) {
  if (!offerId) throw new Error('Missing offerId.');

  // Signing-status refresh is an agent workspace operation, never an admin
  // override. Restrict both the lookup and the later write to the verified
  // offer owner so an administrator cannot probe or update another account's
  // packet from a guessed ID.
  const filters = [
    `id=eq.${encodeURIComponent(offerId)}`,
    `user_id=eq.${encodeURIComponent(user.id)}`,
    'select=id,user_id,signwell_document_id,offer_data,status,last_updated'
  ];

  const rows = await supabaseRequest(`hof_offers?${filters.join('&')}`, {
    method: 'GET'
  });

  const offer = Array.isArray(rows) ? rows[0] : null;

  if (!offer) {
    throw new Error('Offer not found or access denied.');
  }

  return offer;
}

async function getStandaloneAgreementForUser(agreementId, user) {
  if (!agreementId) throw new Error('Missing agreement ID.');

  // Standalone TXR packets are owned by the preparing agent. Preserve that
  // boundary for a manual provider refresh just as we do for offer packets.
  const rows = await supabaseRequest(
    `hof_standalone_agreements?id=eq.${encodeURIComponent(agreementId)}&agent_user_id=eq.${encodeURIComponent(user.id)}&select=id,agent_user_id,signwell_document_id,agreement_data,status,updated_at,signed_at`,
    { method: 'GET' }
  );
  const agreement = Array.isArray(rows) ? rows[0] : null;
  if (!agreement) throw new Error('Agreement not found or access denied.');
  return agreement;
}

async function getSellerDisclosureForUser(draftId, user) {
  if (!draftId) throw new Error('Missing seller disclosure ID.');

  // A seller disclosure remains private to the agent who prepared it. Keep
  // status refreshes and signed-PDF downloads scoped to that same owner.
  const rows = await supabaseRequest(
    `hof_seller_disclosure_drafts?id=eq.${encodeURIComponent(draftId)}&agent_user_id=eq.${encodeURIComponent(user.id)}&select=id,agent_user_id,signwell_document_id,status,signwell_status,sent_at,signed_at,updated_at`,
    { method: 'GET' }
  );
  const draft = Array.isArray(rows) ? rows[0] : null;
  if (!draft) throw new Error('Seller disclosure not found or access denied.');
  return draft;
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

async function getCompletedSignWellPdf(documentId) {
  if (!SIGNWELL_API_KEY) throw new Error('Missing SIGNWELL_API_KEY.');
  const response = await fetch(
    `https://www.signwell.com/api/v1/documents/${encodeURIComponent(documentId)}/completed_pdf?audit_page=true&file_format=pdf`,
    { method: 'GET', headers: { 'X-Api-Key': SIGNWELL_API_KEY } }
  );
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`Completed PDF is not available yet (${response.status}): ${text.slice(0, 300)}`);
  }
  return Buffer.from(await response.arrayBuffer());
}

async function updateOfferStatus(offer, status, documentId, document, user) {
  const now = new Date().toISOString();
  const offerData = parseJsonObject(offer.offer_data);
  const recipientStatuses = extractRecipientStatuses(document);
  const cleanSignwellStatus = cleanStatusLabel(status);
  const providerMainStatus = safeMainOfferStatus(cleanSignwellStatus);
  const mainStatus = ['Submitted', 'Accepted', 'Deleted'].includes(offer.status)
    ? offer.status : providerMainStatus;

  const updatedOfferData = {
    ...offerData,
    signwellStatus: cleanSignwellStatus,
    signwellDocumentId: documentId,
    signwellLastStatusRefresh: now,
    signwellRecipientStatuses: recipientStatuses
  };

  const updateRows = await supabaseRequest(
    `hof_offers?id=eq.${encodeURIComponent(offer.id)}&user_id=eq.${encodeURIComponent(user.id)}${offerRefreshGuard(offer, providerMainStatus)}&select=id,user_id,signwell_document_id,signwell_status,status,last_updated`,
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

  const updated = confirmSignatureRefresh(updateRows, offer);
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

  return updated;
}

function offerRefreshGuard(offer, nextStatus) {
  if (!offer.status) throw new Error('Your offer needs a fresh status check.');
  if ((['Signed', 'Buyer Signed', 'Buyer Signatures Complete'].includes(offer.status) && nextStatus !== 'Signed') ||
      (['Rejected', 'Expired'].includes(offer.status) && nextStatus !== offer.status)) {
    throw new Error('This request needs a fresh status check. Your saved document has not changed.');
  }
  return '&status=eq.' + encodeURIComponent(offer.status) +
    (offer.last_updated ? '&last_updated=eq.' + encodeURIComponent(offer.last_updated) : '&last_updated=is.null') +
    (offer.signwell_document_id ? '&signwell_document_id=eq.' + encodeURIComponent(offer.signwell_document_id) : '&signwell_document_id=is.null');
}

function safeStandaloneStatus(signwellStatus) {
  const clean = cleanStatusLabel(signwellStatus);
  if (clean === 'Draft - not sent') return 'draft';
  if (clean === 'Buyer Signatures Complete') return 'signed';
  if (clean === 'Declined' || clean === 'Expired' || clean === 'Cancelled') return 'void';
  return 'sent';
}

function signatureRefreshGuard(packet, nextStatus) {
  if (!packet.updated_at || !packet.status || !packet.signwell_document_id ||
      (['signed', 'void'].includes(packet.status) && packet.status !== nextStatus)) {
    throw new Error('This request needs a fresh status check. Your saved document has not changed.');
  }
  return '&signwell_document_id=eq.' + encodeURIComponent(packet.signwell_document_id) +
    '&updated_at=eq.' + encodeURIComponent(packet.updated_at) +
    '&status=eq.' + encodeURIComponent(packet.status);
}

function confirmSignatureRefresh(rows, packet) {
  if (!Array.isArray(rows) || rows.length !== 1 || rows[0].id !== packet.id) {
    const error = new Error('This document changed while its status was being checked. Refresh again to see the latest status.');
    error.statusCode = 409;
    throw error;
  }
  return rows[0];
}

async function updateStandaloneAgreementStatus(agreement, status, documentId, document, user) {
  const now = new Date().toISOString();
  const cleanSignwellStatus = cleanStatusLabel(status);
  const agreementStatus = safeStandaloneStatus(cleanSignwellStatus);
  const agreementData = parseJsonObject(agreement.agreement_data);
  const updatedAgreementData = {
    ...agreementData,
    signwellStatus: cleanSignwellStatus,
    signwellDocumentId: documentId,
    signwellLastStatusRefresh: now
  };
  const updatePayload = {
    signwell_status: cleanSignwellStatus,
    status: agreementStatus,
    agreement_data: updatedAgreementData,
    updated_at: now
  };
  if (agreementStatus === 'signed' && !agreement.signed_at) updatePayload.signed_at = now;

  const updateRows = await supabaseRequest(
    `hof_standalone_agreements?id=eq.${encodeURIComponent(agreement.id)}&agent_user_id=eq.${encodeURIComponent(user.id)}${signatureRefreshGuard(agreement, agreementStatus)}&select=id,agent_user_id,signwell_document_id,signwell_status,status,updated_at,signed_at`,
    {
      method: 'PATCH',
      headers: { Prefer: 'return=representation' },
      body: JSON.stringify(updatePayload)
    }
  );

  const updated = confirmSignatureRefresh(updateRows, agreement);
  await supabaseRequest('hof_offer_events', {
    method: 'POST',
    headers: { Prefer: 'return=minimal' },
    body: JSON.stringify({
      offer_id: null,
      user_id: agreement.agent_user_id || user.id,
      event_type: 'signwell_standalone_status_refresh',
      status: cleanSignwellStatus,
      message: 'Standalone agreement SignWell status manually refreshed from API.',
      metadata: { signwell_document_id: documentId, signwell_status: document.status || document.document_status || null },
      created_at: now
    })
  });

  return updated;
}

function safeSellerDisclosureStatus(signwellStatus) {
  const clean = cleanStatusLabel(signwellStatus);
  if (clean === 'Draft - not sent') return 'draft';
  if (clean === 'Buyer Signatures Complete') return 'signed';
  if (clean === 'Declined' || clean === 'Expired' || clean === 'Cancelled') return 'void';
  return 'sent';
}

async function updateSellerDisclosureStatus(draft, status, documentId, user) {
  const now = new Date().toISOString();
  const cleanSignwellStatus = cleanStatusLabel(status);
  const draftStatus = safeSellerDisclosureStatus(cleanSignwellStatus);
  const updatePayload = {
    signwell_status: cleanSignwellStatus,
    status: draftStatus,
    updated_at: now
  };
  if (draftStatus === 'signed' && !draft.signed_at) updatePayload.signed_at = now;

  const updateRows = await supabaseRequest(
    `hof_seller_disclosure_drafts?id=eq.${encodeURIComponent(draft.id)}&agent_user_id=eq.${encodeURIComponent(user.id)}${signatureRefreshGuard(draft, draftStatus)}&select=id,agent_user_id,signwell_document_id,status,signwell_status,sent_at,signed_at,updated_at`,
    {
      method: 'PATCH',
      headers: { Prefer: 'return=representation' },
      body: JSON.stringify(updatePayload)
    }
  );

  return confirmSignatureRefresh(updateRows, draft);
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
    const agreementId = body.agreementId || body.agreement_id || '';
    const sellerDisclosureId = body.sellerDisclosureId || body.seller_disclosure_id || '';
    const downloadCompletedPdf = body.action === 'download_completed_pdf';
    const requestedPackets = [offerId, agreementId, sellerDisclosureId].filter(Boolean);
    if (!requestedPackets.length) throw new Error('Missing packet ID.');
    if (requestedPackets.length > 1) throw new Error('Choose one packet to refresh.');

    const isStandaloneAgreement = Boolean(agreementId);
    const isSellerDisclosure = Boolean(sellerDisclosureId);
    const packet = isSellerDisclosure
      ? await getSellerDisclosureForUser(sellerDisclosureId, user)
      : isStandaloneAgreement
        ? await getStandaloneAgreementForUser(agreementId, user)
        : await getOfferForUser(offerId, user);
    const packetData = isSellerDisclosure
      ? {}
      : parseJsonObject(isStandaloneAgreement ? packet.agreement_data : packet.offer_data);

    const documentId =
      packet.signwell_document_id ||
      packetData.signwellDocumentId ||
      packetData.signwell_document_id ||
      packetData.signwell?.document_id ||
      packetData.signwell?.response?.id ||
      packetData.signwell?.response?.document_id ||
      '';

    if (!documentId) {
      throw new Error('This packet does not have a SignWell document ID.');
    }

    const document = await getSignWellDocument(documentId);
    const status = deriveStatus(document);
    if (downloadCompletedPdf) {
      if (cleanStatusLabel(status) !== 'Buyer Signatures Complete') {
        throw new Error('The completed PDF is available after every recipient finishes signing.');
      }
      const pdf = await getCompletedSignWellPdf(documentId);
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', `attachment; filename="${isSellerDisclosure ? 'homeofferflow-signed-seller-disclosure.pdf' : 'homeofferflow-completed-signwell-packet.pdf'}"`);
      res.setHeader('Cache-Control', 'private, no-store');
      return res.status(200).send(pdf);
    }
    const updatedPacket = isSellerDisclosure
      ? await updateSellerDisclosureStatus(packet, status, documentId, user)
      : isStandaloneAgreement
        ? await updateStandaloneAgreementStatus(packet, status, documentId, document, user)
        : await updateOfferStatus(packet, status, documentId, document, user);

    return json(res, 200, {
      ok: true,
      offerId: isStandaloneAgreement || isSellerDisclosure ? null : packet.id,
      agreementId: isStandaloneAgreement ? packet.id : null,
      sellerDisclosureId: isSellerDisclosure ? packet.id : null,
      documentId,
      status: cleanStatusLabel(status),
      updatedOffer: isStandaloneAgreement || isSellerDisclosure ? null : updatedPacket,
      updatedAgreement: isStandaloneAgreement ? updatedPacket : null,
      updatedSellerDisclosure: isSellerDisclosure ? updatedPacket : null,
      signwellStatusRaw: document.status || document.document_status || null,
      recipientStatuses: extractRecipientStatuses(document)
    });
  } catch (err) {
    console.error('SignWell status refresh failed:', err);
    return json(res, err?.statusCode === 409 ? 409 : 400, {
      error: err?.message || 'SignWell status refresh failed.'
    });
  }
};
