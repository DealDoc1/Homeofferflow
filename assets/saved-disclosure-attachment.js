(function (root) {
  'use strict';
  const normalize = value => String(value || '').toLowerCase().replace(/[^\p{L}\p{N}_]+/gu, ' ').trim();
  function matches(saved, property) {
    return Boolean(property.address && normalize(saved) && [property.address,
      [property.address, property.city, property.state || 'TX', property.zip].filter(Boolean).join(' ')]
      .map(normalize).includes(normalize(saved)));
  }
  function context() {
    const data = typeof state !== 'undefined' ? state.data || {} : {};
    const read = (id, key) => document.getElementById(id)?.value?.trim() || data[key] || '';
    return {user:root.hofAuth?.session?.user?.id || '', offer:data._hofOfferId || '',
      property:{address:read('propAddress','address'),city:read('propCity','city'),
        state:read('propState','state') || 'TX',zip:read('propZip','zip')}};
  }
  function validateAddition(docs, attachment) {
    if (!attachment || attachment.type !== 'seller_disclosure' || typeof attachment.base64 !== 'string' || !attachment.base64
        || !attachment.homeOfferFlowDisclosureReceipt?.sourceDisclosureId || !Number.isFinite(attachment.size) || attachment.size <= 0)
      throw Error('The signed disclosure could not be prepared. Please try again.');
    if (docs.some(doc => doc.homeOfferFlowDisclosureReceipt?.sourceDisclosureId === attachment.homeOfferFlowDisclosureReceipt.sourceDisclosureId || doc.name === attachment.name))
      throw Error('This disclosure is already included in the offer.');
    if (docs.some(doc => doc.type === 'seller_disclosure'))
      throw Error('This offer already includes a seller disclosure. Remove that copy before choosing another.');
    if (docs.length >= 5 || attachment.size > 2 * 1024 * 1024 || docs.reduce((n,d)=>n+Number(d.size || 0),0) + attachment.size > 2.5 * 1024 * 1024)
      throw Error('This packet has reached its PDF size or file limit. Remove a file before adding this disclosure.');
  }
  root.hofChooseSavedDisclosure = async function (trigger) {
    const initial = context(), token = root.hofAuth?.session?.access_token;
    const report = text => root.setUploadedDisclosureStatus?.(text);
    if (!token || !initial.user) { report('Sign in to use a disclosure saved in your account. You can still upload a PDF.'); return; }
    if (!initial.property.address) { report('Enter the property address first so we can find the matching disclosure.'); return; }
    if (document.getElementById('savedDisclosureDialog')) return;
    const modal = document.createElement('div');
    modal.id = 'savedDisclosureDialog'; modal.className = 'hof-agreement-modal';
    modal.innerHTML = '<section class="hof-agreement-dialog" role="dialog" aria-modal="true" aria-labelledby="savedDisclosureTitle"><h3 id="savedDisclosureTitle">Choose a signed seller disclosure</h3><p>Use a seller-signed disclosure for this property. Buyer acknowledgments are added in the offer package; the original signed PDF stays unchanged.</p><div data-saved-disclosure-list></div><p role="status" aria-live="polite" data-saved-disclosure-status>Looking for completed disclosures…</p><button type="button" class="btn-secondary" data-close-saved-disclosure>Cancel</button></section>';
    const status = modal.querySelector('[data-saved-disclosure-status]');
    const current = () => modal.isConnected && JSON.stringify(context()) === JSON.stringify(initial);
    const close = () => { modal.remove(); trigger?.focus(); };
    const cancel = modal.querySelector('[data-close-saved-disclosure]');
    cancel.addEventListener('click', close);
    modal.addEventListener('keydown', e => {
      if (e.key === 'Escape') close();
      if (e.key === 'Tab') {
        const buttons = [...modal.querySelectorAll('button:not(:disabled)')];
        const first=buttons[0],last=buttons[buttons.length-1];
        if (e.shiftKey && document.activeElement === first) {e.preventDefault();last.focus();}
        if (!e.shiftKey && document.activeElement === last) {e.preventDefault();first.focus();}
      }
    });
    document.body.appendChild(modal); cancel.focus();
    try {
      const response = await root.fetch('/api/admin-dashboard?scope=seller_disclosure_drafts', {headers:{Authorization:'Bearer '+token}});
      const result = await response.json();
      if (!current()) { close(); return; }
      if (!response.ok) throw Error(result.error || 'Your saved disclosures could not be loaded.');
      const drafts = (result.drafts || []).filter(d=>d.status==='signed' && d.signwell_document_id && Array.isArray(d.buyer_names) && !d.buyer_names.length && matches(d.property_address, initial.property));
      status.textContent = drafts.length ? 'Choose the completed disclosure you want the buyer to acknowledge.' : 'No seller-only signed disclosure is saved for this property yet. Upload a PDF or continue the offer without one.';
      drafts.forEach(draft => {
        const button = document.createElement('button'); button.type='button'; button.className='btn-secondary';
        button.textContent = [draft.property_address, (draft.seller_names || []).join(', ')].filter(Boolean).join(' — ');
        modal.querySelector('[data-saved-disclosure-list]').appendChild(button);
        button.addEventListener('click', async () => {
          if (!current() || button.disabled) return;
          modal.querySelectorAll('[data-saved-disclosure-list] button').forEach(b=>b.disabled=true);
          status.textContent='Adding your signed disclosure…';
          try {
            const r = await root.fetch('/api/signwell-status',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},
              body:JSON.stringify({action:'prepare_purchase_disclosure',sellerDisclosureId:draft.id,property:initial.property})});
            const data = await r.json();
            if (!current()) {close();return;}
            if (!r.ok) throw Error(data.error || 'This signed disclosure is not available yet.');
            const docs = root.hofUploadedDisclosureDocs || [];
            validateAddition(docs,data.attachment);
            root.hofUploadedDisclosureDocs = [...docs,data.attachment];
            const offer = typeof state !== 'undefined' ? state.data : null;
            if (offer) offer.uploadedDocNames = [...new Set([...(offer.uploadedDocNames || []).map(d=>typeof d==='string'?d:d.name),data.attachment.name])];
            root.resetUploadedDisclosureAcknowledgement?.(); root.renderUploadedDocsList?.();
            root.setUploadedDisclosureStatus?.('Signed seller disclosure added. Review it with the offer before sending.','ok');
            try {root.saveDraft?.(); root.renderReview?.();} catch (_) {}
            close();
          } catch(error) {
            if (!current()) {close();return;}
            status.textContent=error.message || 'The disclosure could not be added. You can continue without it.';
            modal.querySelectorAll('[data-saved-disclosure-list] button').forEach(b=>b.disabled=false);
          }
        });
      });
    } catch(error) { if (current()) status.textContent=error.message || 'Your saved disclosures could not be loaded.'; else close(); }
  };
  // Pure helpers keep address, duplicate and allowance edge cases testable.
  root.hofSavedDisclosureAttachment = Object.freeze({matches,validateAddition});
})(window);
