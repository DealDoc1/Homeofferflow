/* Verified seller flow. Credentials live in memory, never device storage. */
(function (root) {
  'use strict';
  const byId = id => document.getElementById(id);
  const interview = root.hofDisclosureInterview;
  function setPreviewSource(url) {
    for (const id of ['preview','openPreview','downloadPreview']) {
      const element=byId(id), attribute=id==='preview'?'src':'href';
      if (url) element.setAttribute(attribute,url); else element.removeAttribute(attribute);
    }
  }
  async function request(action, session, body) {
    const response = await fetch('/api/admin-dashboard?' + action + '=' + encodeURIComponent(session), {
      method:'POST', cache:'no-store', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw Error(data.error || 'We could not save your disclosure. Please try again.');
    return data;
  }
  function start(session, initial) {
    let data = initial, busy = false, previewRevision = '', previewUrl = '', signingButton;
    const card = byId('questionnaire'), status = byId('answerStatus');
    document.querySelector('h1').textContent = 'Your seller’s disclosure';
    document.querySelector('main > section p').textContent = 'Answer the property questions, review your disclosure, then sign through SignWell.';
    document.querySelector('main > section .warning').hidden = true;
    const details = byId('details'); details.hidden = false; details.replaceChildren();
    const title = document.createElement('h2'); title.textContent = data.propertyAddress; details.appendChild(title);
    const name = document.createElement('p'); name.textContent = 'Prepared for ' + data.sellerName; details.appendChild(name);
    byId('mainQuestions').innerHTML = interview.renderResponses();
    byId('mainQuestions').querySelector('.hof-seller-step-hint')?.remove();
    byId('waterQuestions').innerHTML = data.hasWaterRights ? '<h2>Water rights</h2>' + interview.renderWaterResponses() : '';
    byId('waterQuestions').hidden = !data.hasWaterRights;
    for (const kind of ['seller','water']) card.querySelectorAll('[data-' + kind + '-response]').forEach(field => {
      const value = (kind === 'seller' ? data.responseData : data.waterRightsData)?.[field.dataset[kind + 'Response']];
      field.value = value === true ? 'Y' : value === false ? 'N' : value == null ? '' : String(value);
    });
    card.hidden = false;
    card.querySelector('details')?.setAttribute('open','');
    interview.syncDisclosureDetails(card);
    function invalidatePreview() {
      previewRevision = ''; byId('previewCard').hidden = true; byId('attestationCard').hidden = true;
      setPreviewSource('');
      if (previewUrl) { URL.revokeObjectURL(previewUrl); previewUrl=''; }
      if (signingButton) signingButton.hidden = true;
      interview.syncDisclosureDetails(card);
    }
    card.addEventListener('input', invalidatePreview); card.addEventListener('change', invalidatePreview);
    function answers() {
      return {reviewContentRevision:data.reviewContentRevision,
        responseData:interview.collectDisclosureResponses(card, 'seller', data.responseData),
        waterRightsData:data.hasWaterRights ? interview.collectDisclosureResponses(card, 'water', data.waterRightsData) : {}};
    }
    async function save(review) {
      if (busy) return;
      if (review) {
        const missing = [...card.querySelectorAll('select[data-seller-response],select[data-water-response]')]
          .find(field => !field.closest('[hidden]') && !field.value);
        if (missing) {
          const section = missing.closest('details'); if (section) section.open = true;
          missing.focus(); status.textContent = 'Please answer each question before reviewing. Choose Unknown when you are not sure.'; return;
        }
      }
      busy = true; byId('saveAnswers').disabled = byId('reviewAnswers').disabled = true;
      status.textContent = review ? 'Preparing your disclosure…' : 'Saving your answers…';
      try {
        const body = answers(), result = await request('save_seller_questionnaire', session, body);
        data = {...data, ...body, reviewContentRevision:result.reviewContentRevision};
        invalidatePreview();
        status.textContent = 'Your answers are saved. You can return using the link in your email.';
        if (review) {
          const response = await fetch('/api/admin-dashboard?seller_review_pdf=' + encodeURIComponent(session) +
            '&revision=' + encodeURIComponent(data.reviewContentRevision), {cache:'no-store'});
          if (!response.ok) throw Error('The disclosure changed or the preview could not be loaded. Please save and review again.');
          const blob = await response.blob();
          if (!blob.type.includes('pdf')) throw Error('We could not load your completed disclosure. Please try again.');
          if (previewUrl) URL.revokeObjectURL(previewUrl);
          previewUrl = URL.createObjectURL(blob); setPreviewSource(previewUrl);
          previewRevision = data.reviewContentRevision;
          byId('previewCard').hidden = byId('attestationCard').hidden = false;
          byId('sellerName').value = data.sellerName; byId('confirm').checked = false;
          byId('attest').disabled = false; byId('status').textContent = '';
          byId('previewCard').scrollIntoView({behavior:'smooth',block:'start'});
          status.textContent = 'Review every page, then confirm your answers below.';
        }
      } catch (error) { status.textContent = error.message; }
      finally { busy = false; byId('saveAnswers').disabled = byId('reviewAnswers').disabled = false; }
    }
    byId('saveAnswers').onclick = () => save(false);
    byId('reviewAnswers').onclick = () => save(true);
    byId('attest').textContent = 'Confirm my disclosure';
    byId('attestationCard').querySelector('h2').textContent = 'Confirm your answers';
    byId('attestationCard').querySelector('p').textContent = 'Review every page before confirming. This confirmation is not your electronic signature.';
    byId('confirm').nextElementSibling.textContent = 'I reviewed every page and confirm these answers reflect my knowledge of the property.';
    byId('attest').onclick = async () => {
      if (busy) return;
      const message = byId('status');
      if (!previewRevision || !byId('confirm').checked || !byId('sellerName').value.trim()) {
        message.textContent = 'Review the completed disclosure, enter your name and confirm your answers first.'; return;
      }
      busy = true; byId('attest').disabled = true;
      try {
        const result = await request('attest_seller_review', session, {...answers(), reviewContentRevision:previewRevision,
          sellerName:byId('sellerName').value, confirmed:true});
        message.textContent = result.allSellersAttested
          ? 'Your disclosure is confirmed. Your agent can now prepare it for signature.'
          : 'Your answers are confirmed. The other seller must review the same completed disclosure before signing.';
        if (result.allSellersAttested && data.canSignSeparately) {
          if (!signingButton) {
            signingButton = document.createElement('button'); signingButton.type = 'button';
            signingButton.textContent = 'Send for signature'; byId('attestationCard').appendChild(signingButton);
            signingButton.onclick = async () => {
              if (busy) return; busy = true; signingButton.disabled = true;
              try {
                await request('sign_seller_questionnaire', session, {});
                message.textContent = 'Signature invitations sent through SignWell. Check your email to initial and sign.';
              } catch (error) { message.textContent = error.message; signingButton.disabled = false; }
              finally { busy = false; }
            };
          }
          signingButton.hidden = false;
          message.textContent = 'Your answers are confirmed. You can send for signature now or let your agent handle it.';
        }
      } catch (error) { message.textContent = error.message; byId('attest').disabled = false; }
      finally { busy = false; }
    };
  }
  root.hofSellerQuestionnaire = Object.freeze({start,setPreviewSource});
})(window);
