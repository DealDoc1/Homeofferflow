(function () {
  const root = window;
  const FORM_CODE = 'TREC-38-8';
  const profile = () => root.hofAuth?.authoritativeProfile || {};
  const activeAgent = () => Boolean(root.hofAuth?.session?.user) &&
    ['agent', 'broker', 'brokerage_admin', 'broker_admin', 'owner', 'team_lead'].includes(String(root.hofAuth?.role || profile().role || '').toLowerCase());
  const partyNames = (form, party) => [form.get(`${party}One`), form.get(`${party}Two`)]
    .map(value => String(value || '').trim()).filter(Boolean);
  const reasons = [
    ['option_period', 'Buyer is terminating during the unrestricted option period.'],
    ['buyer_approval', 'Buyer cannot obtain Buyer Approval under the Third Party Financing Addendum.'],
    ['property_approval', 'The property does not satisfy Property Approval under the Third Party Financing Addendum.'],
    ['hoa_documents', 'Buyer is terminating under the property-owners association addendum.'],
    ['seller_disclosure', 'Buyer is terminating because of the Seller’s Disclosure Notice provision.'],
    ['appraisal', 'Buyer is terminating under the lender-appraisal addendum.'],
    ['title_objections', 'Timely title objections were not cured by the end of the Cure Period.'],
    ['other', 'Another contract or addendum provision applies.'],
  ];

  async function source() {
    const approved = await root.hofLoadApprovedBrokerageSource?.(FORM_CODE);
    if (!approved) throw new Error('TREC 38-8 is not available in the HomeOfferFlow form library yet.');
    return approved;
  }

  async function openDraftDialog(preloadedSource) {
    const approved = preloadedSource || await source();
    document.getElementById('trec388AgreementDialog')?.remove();
    const modal = document.createElement('div');
    modal.id = 'trec388AgreementDialog';
    modal.className = 'hof-agreement-modal';
    modal.innerHTML = `<form class="hof-agreement-dialog" id="trec388AgreementForm">
      <p class="hof-agent-question-step">Buyer notice</p><h3>End a purchase contract</h3>
      <p>Choose the contract provision the Buyer is using. HomeOfferFlow prepares the notice; it does not decide whether a termination right exists.</p>
      <div class="hof-agreement-grid">
        <label class="hof-agreement-wide">Property street address and city<input name="propertyAddress" required maxlength="400" autocomplete="street-address" inputmode="text"></label>
        <label>Buyer 1 full name<input name="buyerOne" required maxlength="180" autocomplete="name"></label><label>Buyer 2 full name (optional)<input name="buyerTwo" maxlength="180" autocomplete="name"></label>
        <label>Seller 1 full name<input name="sellerOne" required maxlength="180" autocomplete="name"></label><label>Seller 2 full name (optional)<input name="sellerTwo" maxlength="180" autocomplete="name"></label>
        <fieldset class="hof-agreement-wide hof-agreement-services"><legend>Why is the Buyer terminating?</legend>${reasons.map(([value, label]) => `<label><input type="checkbox" name="terminationReason" value="${value}"> ${label}</label>`).join('')}</fieldset>
        <label class="hof-agreement-wide" id="trec388OtherWrap" hidden>Contract paragraph or addendum provision<textarea name="otherTerminationBasis" maxlength="1200" rows="3"></textarea></label>
        <label class="hof-agreement-wide hof-agreement-services"><input name="terminationAcknowledgment" type="checkbox" required> I confirm the Buyer has chosen the stated contract right, required supporting material will be delivered with this notice, and release of earnest money is handled separately under the contract.</label>
      </div>
      <div id="trec388DraftStatus" class="hof-iabs-status" role="status" aria-live="polite"></div>
      <div class="hof-agreement-footer"><button class="btn-secondary" type="button">Cancel</button><button class="btn-primary" type="submit">Prepare notice</button></div>
    </form>`;
    document.body.appendChild(modal);
    const form = modal.querySelector('form');
    const other = modal.querySelector('[value="other"]');
    const otherWrap = modal.querySelector('#trec388OtherWrap');
    const syncOther = () => { otherWrap.hidden = !other.checked; otherWrap.querySelector('textarea').required = other.checked; };
    other.addEventListener('change', syncOther); syncOther();
    modal.querySelector('button[type="button"]').onclick = () => modal.remove();
    modal.addEventListener('click', event => { if (event.target === modal) modal.remove(); });
    form.addEventListener('submit', async event => {
      event.preventDefault(); const values = new FormData(form); const button = form.querySelector('button[type="submit"]'); const status = modal.querySelector('#trec388DraftStatus');
      if (button.disabled) return; button.disabled = true; button.setAttribute('aria-busy', 'true'); button.textContent = 'Preparing notice…'; status.textContent = 'Preparing the Buyer notice…'; status.className = 'hof-iabs-status';
      try {
        const response = await fetch('/api/admin-dashboard', {method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${root.hofAuth?.session?.access_token || ''}`}, body:JSON.stringify({action:'create_trec_38_8_draft', formCode:FORM_CODE, formSourceId:approved.id, propertyAddress:values.get('propertyAddress'), buyerNames:partyNames(values,'buyer'), sellerNames:partyNames(values,'seller'), terminationReasons:values.getAll('terminationReason'), otherTerminationBasis:values.get('otherTerminationBasis'), terminationAcknowledgment:values.get('terminationAcknowledgment') === 'on'})});
        const result = await response.json().catch(() => ({})); if (!response.ok) throw new Error(result.error || 'Could not prepare the Buyer notice.');
        button.textContent = 'Notice ready'; status.className = 'hof-iabs-status ready'; status.innerHTML = 'Your notice is ready. <button type="button" class="btn-secondary">Review and send</button>'; status.querySelector('button').onclick = async () => { modal.remove(); await root.hofOpenPreparedAgreement?.(); };
      } catch (error) { status.className = 'hof-iabs-status error'; status.textContent = root.hofCustomerActionError?.(error, 'We couldn’t prepare the Buyer notice. Review your answers and try again.') || error.message; button.disabled = false; button.textContent = 'Prepare notice'; }
      finally { button.setAttribute('aria-busy', 'false'); }
    });
    modal.querySelector('[name="propertyAddress"]')?.focus();
  }

  root.hofOpenTrec388Draft = () => openDraftDialog().catch(error => root.announceWorkspaceStatus?.(root.hofApprovedSourceStatusCopy?.(error) || 'We couldn’t open that document. Please try again.'));
  async function renderCard() {
    const panel = document.getElementById('accountPanelRelationships'); if (!panel || !activeAgent() || document.getElementById('trec388AgreementCard')) return;
    const card = document.createElement('div'); card.id = 'trec388AgreementCard'; card.className = 'account-card hof-agreement-card'; card.innerHTML = '<h4>Buyer’s Notice of Termination</h4><p>Checking the HomeOfferFlow form library…</p>'; panel.appendChild(card);
    try { const approved = await source(); card.querySelector('p').textContent = 'Prepare the Buyer’s termination notice through a short interview, review it, and send both Buyers at the same time when two signatures are needed.'; const button = document.createElement('button'); button.type = 'button'; button.className = 'btn-secondary'; button.textContent = 'Start termination notice'; button.onclick = () => openDraftDialog(approved); card.appendChild(button); }
    catch (error) { card.querySelector('p').textContent = root.hofApprovedSourceStatusCopy?.(error) || 'We couldn’t open that document. Please try again.'; }
  }
  const prior = root.renderAccountDashboard; root.renderAccountDashboard = function () { if (typeof prior === 'function') prior.apply(this, arguments); renderCard(); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderCard, {once:true}); else renderCard();
})();
