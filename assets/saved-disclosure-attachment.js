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
      parties:['buyer1','buyerEmail','buyer2','buyer2Email','seller','seller1','seller1Name','seller2','seller2Name'].map(key=>String(data[key] || '').trim()),
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
  const selectionKeys=['purchaseSellerDisclosureId','purchaseSellerDisclosureRevision','purchaseSellerDisclosureFingerprint','purchaseSellerDisclosureSummary'];
  const offerData=()=>typeof state!=='undefined'?state.data:null;
  let previewCache=null;
  function clearSelection(){const data=offerData();if(data)selectionKeys.forEach(key=>delete data[key]);previewCache=null;}
  function eligible(draft,property){
    return Boolean(Array.isArray(draft.buyer_names)&&!draft.buyer_names.length&&matches(draft.property_address,property)
      &&(draft.status==='signed'&&draft.signwell_document_id||draft.status==='draft'&&draft.seller_review_attested===true
        &&!draft.signwell_document_id&&!draft.signature_offer_id&&!draft.signature_packet_id));
  }
  function validatePreview(data,id){
    if(!data||data.previewOnly!==true||data.signatureRequestCreated!==false||data.disclosureId!==id
      ||!/^[a-f0-9]{64}$/.test(data.contentFingerprint||'')||!data.reviewRevision||typeof data.pdfBase64!=='string'||!data.pdfBase64
      ||!Array.isArray(data.recipients)||!data.recipients.some(row=>row?.role==='Seller')||!data.recipients.some(row=>row?.role==='Buyer'))
      throw Error('The disclosure preview could not be confirmed. Please try again.');
  }
  function previewBlob(data){
    try{
      const decoded=atob(data.pdfBase64);
      if(!decoded.startsWith('%PDF-'))throw Error();
      return new Blob([Uint8Array.from(decoded,c=>c.charCodeAt(0))],{type:'application/pdf'});
    }catch(_){throw Error('The disclosure PDF could not be opened. Please try again.');}
  }
  async function fetchPreview(id,token,offer){
    const response=await root.fetch('/api/admin-dashboard',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},
      body:JSON.stringify({action:'preview_purchase_disclosure_execution',offerId:offer,draftId:id})});
    const data=await response.json();if(!response.ok)throw Error(data.error||'The disclosure is not ready. You can continue without it.');
    validatePreview(data,id);return data;
  }
  root.hofRenderPurchaseDisclosureSelection=function(){
    const data=offerData();
    ['purchaseDisclosureSelection','purchaseDisclosureReview'].forEach(id=>{
      const box=document.getElementById(id);if(!box)return;
      box.replaceChildren();box.hidden=!data?.purchaseSellerDisclosureId
        ||data.purchaseSellerDisclosureSummary?.ownerId&&data.purchaseSellerDisclosureSummary.ownerId!==context().user;if(box.hidden)return;
      const text=document.createElement('p');text.textContent="Seller's disclosure selected. Sellers sign; buyers acknowledge receipt.";box.appendChild(text);
      const preview=document.createElement('button');preview.type='button';preview.className='btn-secondary';preview.textContent='Review disclosure PDF';
      preview.style.marginRight='0.5rem';
      preview.addEventListener('click',async()=>{
        const initial=context(),selected=data.purchaseSellerDisclosureId,fingerprint=data.purchaseSellerDisclosureFingerprint;preview.disabled=true;
        try{
          let blob=previewCache?.key===selected+':'+fingerprint&&previewCache.context===JSON.stringify(initial)?previewCache.blob:null;
          if(!blob){
            const result=await fetchPreview(selected,root.hofAuth?.session?.access_token||'',initial.offer);
            if(JSON.stringify(context())!==JSON.stringify(initial)||offerData()!==data)return;
            if(result.contentFingerprint!==fingerprint)throw Error('The disclosure has changed. Choose the current disclosure before including it.');
            blob=previewBlob(result);
          }
          root.hofShowPdfPreview?.(blob,"Seller's disclosure");
        }catch(error){root.setUploadedDisclosureStatus?.(error.message||'The preview is unavailable. You can continue without it.');}
        finally{preview.disabled=false;}
      });
      const remove=document.createElement('button');remove.type='button';remove.className='btn-secondary';remove.textContent='Remove selection';
      remove.addEventListener('click',async()=>{
        const initial=context();clearSelection();root.hofRenderPurchaseDisclosureSelection();root.saveDraft?.();
        const saved=await root.saveOfferDraftToSupabase?.('Draft');
        if(JSON.stringify(context())===JSON.stringify(initial)&&!saved?.id)
          root.setUploadedDisclosureStatus?.('Selection removed on this device. Save your draft again to update the dashboard.');
      });
      box.appendChild(preview);box.appendChild(remove);
    });
  };
  root.hofChooseSavedDisclosure = async function (trigger) {
    try{root.collectAllData?.();}catch(_){}
    let initial=context(),initialData=offerData();
    const token=root.hofAuth?.session?.access_token;
    const report = text => root.setUploadedDisclosureStatus?.(text);
    if (!token || !initial.user) { report('Sign in to use a disclosure saved in your account. You can still upload a PDF.'); return; }
    if (!initial.property.address) { report('Enter the property address first so we can find the matching disclosure.'); return; }
    if (document.getElementById('savedDisclosureDialog')) return;
    const modal = document.createElement('div');
    modal.id = 'savedDisclosureDialog'; modal.className = 'hof-agreement-modal';
    modal.innerHTML = '<section class="hof-agreement-dialog" role="dialog" aria-modal="true" aria-labelledby="savedDisclosureTitle"><h3 id="savedDisclosureTitle">Choose a seller disclosure</h3><p>Include a seller-reviewed disclosure for signing, or reuse a signed copy. Buyer acknowledgments are added automatically.</p><div data-saved-disclosure-list></div><p role="status" aria-live="polite" data-saved-disclosure-status>Looking for available disclosures…</p><button type="button" class="btn-secondary" data-close-saved-disclosure>Cancel</button></section>';
    const status = modal.querySelector('[data-saved-disclosure-status]');
    const list=modal.querySelector('[data-saved-disclosure-list]');list.style.display='grid';list.style.gap='0.5rem';
    const current = () => modal.isConnected && offerData()===initialData && JSON.stringify(context()) === JSON.stringify(initial);
    const close = () => { const connected=modal.isConnected;modal.remove();if(connected)trigger?.focus(); };
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
      const drafts=(result.drafts||[]).filter(d=>eligible(d,initial.property));
      status.textContent=drafts.length?'Choose the disclosure to include in this offer.':'No completed seller review or signed disclosure is saved for this property yet. Upload a PDF or continue without it.';
      drafts.forEach(draft => {
        const button = document.createElement('button'); button.type='button'; button.className='btn-secondary';
        button.textContent=[draft.property_address,(draft.seller_names||[]).join(', '),draft.status==='signed'?'Seller-signed':'Seller-reviewed'].filter(Boolean).join(' — ');
        modal.querySelector('[data-saved-disclosure-list]').appendChild(button);
        button.addEventListener('click', async () => {
          if (!current() || button.disabled) return;
          modal.querySelectorAll('[data-saved-disclosure-list] button').forEach(b=>b.disabled=true);
          status.textContent='Adding your signed disclosure…';
          try {
            if(draft.status!=='signed'){
              if((root.hofUploadedDisclosureDocs||[]).some(doc=>doc.type==='seller_disclosure'))throw Error('Remove the attached seller disclosure before choosing another.');
              status.textContent='Preparing your disclosure preview…';
              const before=initial,saved=await root.saveOfferDraftToSupabase?.('Draft'),now=context();
              if(!modal.isConnected||now.user!==before.user||JSON.stringify(now.property)!==JSON.stringify(before.property)
                ||JSON.stringify(now.parties)!==JSON.stringify(before.parties)||before.offer&&now.offer!==before.offer){close();return;}
              if(!saved?.id||saved.id!==now.offer||saved.user_id!==now.user)throw Error('Save this offer to your dashboard before including the reviewed disclosure. You can still continue without it.');
              initial=now;initialData=offerData();
              const prepared=await fetchPreview(draft.id,token,initial.offer);if(!current()){close();return;}
              const blob=previewBlob(prepared);
              const data=offerData();data.purchaseSellerDisclosureId=draft.id;data.purchaseSellerDisclosureRevision=prepared.reviewRevision;
              data.purchaseSellerDisclosureFingerprint=prepared.contentFingerprint;
              data.purchaseSellerDisclosureSummary={ownerId:initial.user,propertyAddress:draft.property_address,sellerNames:draft.seller_names||[],recipients:prepared.recipients};
              previewCache={key:draft.id+':'+prepared.contentFingerprint,context:JSON.stringify(initial),blob};
              root.hofRenderPurchaseDisclosureSelection();root.saveDraft?.();
              const persisted=await root.saveOfferDraftToSupabase?.('Draft');
              if(!current()){close();return;}
              if(!persisted?.id){root.setUploadedDisclosureStatus?.('Disclosure selected on this device. Dashboard save could not be confirmed; keep this page open or try saving again.');close();return;}
              root.setUploadedDisclosureStatus?.('Disclosure selected.','ok');close();return;
            }
            const r = await root.fetch('/api/signwell-status',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},
              body:JSON.stringify({action:'prepare_purchase_disclosure',sellerDisclosureId:draft.id,property:initial.property})});
            const data = await r.json();
            if (!current()) {close();return;}
            if (!r.ok) throw Error(data.error || 'This signed disclosure is not available yet.');
            const docs = root.hofUploadedDisclosureDocs || [];
            validateAddition(docs,data.attachment);
            clearSelection();root.hofRenderPurchaseDisclosureSelection();
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
  root.hofSavedDisclosureAttachment = Object.freeze({matches,validateAddition,eligible,validatePreview});
})(window);
