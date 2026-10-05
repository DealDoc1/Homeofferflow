(function () {
  const root = window;
  const FORM_CODE = 'TREC-39-11';
  const profile = () => root.hofAuth?.authoritativeProfile || {};
  const activeAgent = () => Boolean(root.hofAuth?.session?.user) &&
    ['agent', 'broker', 'brokerage_admin', 'broker_admin', 'owner', 'team_lead']
      .includes(String(root.hofAuth?.role || profile().role || '').toLowerCase());
  const partyNames = (form, party) => [form.get(`${party}One`), form.get(`${party}Two`)]
    .map(value => String(value || '').trim()).filter(Boolean);
  const changeChoices = [
    ['sales_price', 'Change the sales price'],
    ['repairs', 'Add or change Seller repairs or treatments'],
    ['closing_date', 'Change the closing date'],
    ['seller_expense', 'Change the Seller expense amount in Paragraph 12A(1)(b)'],
    ['settlement_expenses', 'Change Seller or Buyer settlement expenses in Paragraph 12B'],
    ['lender_repairs', 'Allocate lender-required repair costs'],
    ['option_extension', 'Extend the option period for an additional fee'],
    ['option_waiver', 'Waive the unrestricted option-period termination right'],
    ['buyer_approval_date', 'Change the Buyer Approval notice deadline'],
    ['other', 'Add another modification entered by the agent'],
  ];

  async function source() {
    const approved = await root.hofLoadApprovedBrokerageSource?.(FORM_CODE);
    if (!approved) throw new Error('TREC 39-11 is not available in the HomeOfferFlow form library yet.');
    return approved;
  }

  function moneyTotal(form) {
    const cash = Number(form.elements.priceCash.value || 0);
    const financing = Number(form.elements.priceFinancing.value || 0);
    const output = form.querySelector('#trec3911PriceTotal');
    output.textContent = Number.isFinite(cash + financing)
      ? (cash + financing).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
      : '$0.00';
  }

  function bindConditionalFields(form) {
    const selected = key => form.querySelector(`[name="amendmentChange"][value="${key}"]`)?.checked;
    const sync = () => {
      form.querySelectorAll('[data-change-panel]').forEach(panel => {
        const visible = selected(panel.dataset.changePanel);
        panel.hidden = !visible;
        panel.querySelectorAll('[data-required-when-visible]').forEach(field => { field.required = visible; });
      });
      const extension = form.querySelector('[value="option_extension"]');
      const waiver = form.querySelector('[value="option_waiver"]');
      if (extension.checked) {
        waiver.checked = false;
        waiver.disabled = true;
        extension.disabled = false;
      } else if (waiver.checked) {
        extension.checked = false;
        extension.disabled = true;
        waiver.disabled = false;
      } else {
        extension.disabled = false;
        waiver.disabled = false;
      }
      ['seller', 'buyer'].forEach(party => {
        const included = form.elements[`${party}SettlementIncluded`].checked;
        const type = form.elements[`${party}SettlementType`];
        const value = form.elements[`${party}SettlementValue`];
        type.disabled = !included; value.disabled = !included;
        type.required = selected('settlement_expenses') && included;
        value.required = selected('settlement_expenses') && included;
      });
      moneyTotal(form);
    };
    form.addEventListener('change', sync);
    form.elements.priceCash.addEventListener('input', () => moneyTotal(form));
    form.elements.priceFinancing.addEventListener('input', () => moneyTotal(form));
    sync();
  }

  async function openDraftDialog(preloadedSource) {
    const approved = preloadedSource || await source();
    document.getElementById('trec3911AgreementDialog')?.remove();
    const modal = document.createElement('div');
    modal.id = 'trec3911AgreementDialog'; modal.className = 'hof-agreement-modal';
    modal.innerHTML = `<form class="hof-agreement-dialog" id="trec3911AgreementForm">
      <p class="hof-agent-question-step">Contract changes</p><h3>Amend an existing contract</h3>
      <p>Select only the changes the parties have agreed to consider. HomeOfferFlow copies your entries onto TREC 39-11; it does not choose or draft terms.</p>
      <div class="hof-agreement-grid">
        <label class="hof-agreement-wide">Property street address and city<input name="propertyAddress" required maxlength="400" autocomplete="street-address" inputmode="text"></label>
        <label>Buyer 1 full name<input name="buyerOne" required maxlength="180" autocomplete="name"></label><label>Buyer 2 full name (optional)<input name="buyerTwo" maxlength="180" autocomplete="name"></label>
        <label>Seller 1 full name<input name="sellerOne" required maxlength="180" autocomplete="name"></label><label>Seller 2 full name (optional)<input name="sellerTwo" maxlength="180" autocomplete="name"></label>
        <fieldset class="hof-agreement-wide hof-agreement-services"><legend>What needs to change?</legend>${changeChoices.map(([value, label]) => `<label><input type="checkbox" name="amendmentChange" value="${value}"> ${label}</label>`).join('')}</fieldset>

        <fieldset class="hof-agreement-wide" data-change-panel="sales_price" hidden><legend>Amended sales price</legend><div class="hof-agreement-grid">
          <label>Cash portion ($)<input name="priceCash" data-required-when-visible inputmode="decimal" pattern="[0-9,]+(\\.[0-9]{1,2})?"></label>
          <label>Financing portion ($)<input name="priceFinancing" data-required-when-visible inputmode="decimal" pattern="[0-9,]+(\\.[0-9]{1,2})?"></label>
          <p class="hof-agreement-wide">Total sales price: <strong id="trec3911PriceTotal">$0.00</strong></p>
        </div></fieldset>
        <label class="hof-agreement-wide" data-change-panel="repairs" hidden>Repairs and treatments Seller will complete<textarea name="repairsText" data-required-when-visible maxlength="3000" rows="4"></textarea></label>
        <label data-change-panel="closing_date" hidden>New closing date<input name="closingDate" type="date" data-required-when-visible></label>
        <label data-change-panel="seller_expense" hidden>Amended Seller expense amount ($)<input name="sellerExpense" data-required-when-visible inputmode="decimal" pattern="[0-9,]+(\\.[0-9]{1,2})?"></label>

        <fieldset class="hof-agreement-wide" data-change-panel="settlement_expenses" hidden><legend>Paragraph 12B settlement expenses</legend>
          <p>Include at least one party. Choose the exact dollar amount or percentage the parties selected.</p>
          <div class="hof-agreement-grid">
            <label><input type="checkbox" name="sellerSettlementIncluded"> Change Seller amount</label><label>Seller measure<select name="sellerSettlementType"><option value="">Choose one</option><option value="amount">Dollar amount</option><option value="percent">Percentage</option></select><input name="sellerSettlementValue" inputmode="decimal" placeholder="Value"></label>
            <label><input type="checkbox" name="buyerSettlementIncluded"> Change Buyer amount</label><label>Buyer measure<select name="buyerSettlementType"><option value="">Choose one</option><option value="amount">Dollar amount</option><option value="percent">Percentage</option></select><input name="buyerSettlementValue" inputmode="decimal" placeholder="Value"></label>
          </div>
        </fieldset>
        <fieldset class="hof-agreement-wide" data-change-panel="lender_repairs" hidden><legend>Lender-required repair costs</legend><div class="hof-agreement-grid">
          <label>Paid by Seller ($)<input name="lenderRepairSeller" data-required-when-visible inputmode="decimal" placeholder="Use 0 when none"></label>
          <label>Paid by Buyer ($)<input name="lenderRepairBuyer" data-required-when-visible inputmode="decimal" placeholder="Use 0 when none"></label>
        </div></fieldset>
        <fieldset class="hof-agreement-wide" data-change-panel="option_extension" hidden><legend>Option-period extension</legend><div class="hof-agreement-grid">
          <label>Additional option fee ($)<input name="optionFee" data-required-when-visible inputmode="decimal"></label><label>New deadline<input name="optionExtensionDate" type="date" data-required-when-visible></label>
          <fieldset class="hof-agreement-wide"><legend>Credit the additional option fee to the sales price?</legend><label><input type="radio" name="optionFeeCredited" value="yes" data-required-when-visible> Yes</label><label><input type="radio" name="optionFeeCredited" value="no" data-required-when-visible> No</label></fieldset>
        </div></fieldset>
        <label data-change-panel="buyer_approval_date" hidden>New Buyer Approval notice deadline<input name="buyerApprovalDate" type="date" data-required-when-visible></label>
        <label class="hof-agreement-wide" data-change-panel="other" hidden>Other modifications<textarea name="otherModifications" data-required-when-visible maxlength="3000" rows="4"></textarea><small>Enter the parties’ exact factual terms. Agents may not draft legal language.</small></label>
        <label class="hof-agreement-wide hof-agreement-services"><input name="amendmentReviewAcknowledgment" type="checkbox" required> I confirm the parties selected these changes and will review the completed amendment before signing. Legal advice or custom drafting should come from an attorney.</label>
      </div>
      <div id="trec3911DraftStatus" class="hof-iabs-status" role="status" aria-live="polite"></div>
      <div class="hof-agreement-footer"><button class="btn-secondary" type="button">Cancel</button><button class="btn-primary" type="submit">Prepare amendment</button></div>
    </form>`;
    document.body.appendChild(modal);
    const form = modal.querySelector('form'); bindConditionalFields(form);
    modal.querySelector('button[type="button"]').onclick = () => modal.remove();
    modal.addEventListener('click', event => { if (event.target === modal) modal.remove(); });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const values = new FormData(form); const changes = values.getAll('amendmentChange');
      const button = form.querySelector('button[type="submit"]'); const status = modal.querySelector('#trec3911DraftStatus');
      if (!changes.length) { status.className = 'hof-iabs-status error'; status.textContent = 'Choose at least one contract term to amend.'; return; }
      if (changes.includes('settlement_expenses') && !values.get('sellerSettlementIncluded') && !values.get('buyerSettlementIncluded')) { status.className = 'hof-iabs-status error'; status.textContent = 'Choose the Seller or Buyer settlement expense change.'; return; }
      if (button.disabled) return; button.disabled = true; button.setAttribute('aria-busy', 'true'); button.textContent = 'Preparing amendment…'; status.textContent = 'Preparing the amendment…'; status.className = 'hof-iabs-status';
      const settlement = party => values.get(`${party}SettlementIncluded`) ? { type: values.get(`${party}SettlementType`), value: values.get(`${party}SettlementValue`) } : { type: '', value: '' };
      try {
        const response = await fetch('/api/admin-dashboard', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${root.hofAuth?.session?.access_token || ''}` }, body: JSON.stringify({
          action: 'create_trec_39_11_draft', formCode: FORM_CODE, formSourceId: approved.id,
          propertyAddress: values.get('propertyAddress'), buyerNames: partyNames(values, 'buyer'), sellerNames: partyNames(values, 'seller'), changes,
          priceCash: values.get('priceCash'), priceFinancing: values.get('priceFinancing'), repairsText: values.get('repairsText'), closingDate: values.get('closingDate'), sellerExpense: values.get('sellerExpense'),
          settlementExpenses: { seller: settlement('seller'), buyer: settlement('buyer') }, lenderRepairSeller: values.get('lenderRepairSeller'), lenderRepairBuyer: values.get('lenderRepairBuyer'),
          optionFee: values.get('optionFee'), optionExtensionDate: values.get('optionExtensionDate'), optionFeeCredited: values.get('optionFeeCredited') === 'yes',
          buyerApprovalDate: values.get('buyerApprovalDate'), otherModifications: values.get('otherModifications'), amendmentReviewAcknowledgment: values.get('amendmentReviewAcknowledgment') === 'on'
        }) });
        const result = await response.json().catch(() => ({})); if (!response.ok) throw new Error(result.error || 'Could not prepare the contract amendment.');
        button.textContent = 'Amendment ready'; status.className = 'hof-iabs-status ready'; status.innerHTML = 'Your amendment is ready. <button type="button" class="btn-secondary">Review and send</button>'; status.querySelector('button').onclick = async () => { modal.remove(); await root.hofOpenPreparedAgreement?.(); };
      } catch (error) { status.className = 'hof-iabs-status error'; status.textContent = root.hofCustomerActionError?.(error, 'We couldn’t prepare the amendment. Review your answers and try again.') || error.message; button.disabled = false; button.textContent = 'Prepare amendment'; }
      finally { button.setAttribute('aria-busy', 'false'); }
    });
    form.querySelector('[name="propertyAddress"]')?.focus();
  }

  root.hofOpenTrec3911Draft = () => openDraftDialog().catch(error => root.announceWorkspaceStatus?.(root.hofApprovedSourceStatusCopy?.(error) || 'We couldn’t open that document. Please try again.'));
  async function renderCard() {
    const panel = document.getElementById('accountPanelRelationships'); if (!panel || !activeAgent() || document.getElementById('trec3911AgreementCard')) return;
    const card = document.createElement('div'); card.id = 'trec3911AgreementCard'; card.className = 'account-card hof-agreement-card'; card.innerHTML = '<h4>Amendment to Contract</h4><p>Checking the HomeOfferFlow form library…</p>'; panel.appendChild(card);
    try { const approved = await source(); card.querySelector('p').textContent = 'Choose the agreed contract changes through a short interview, review the completed amendment, and send all Buyers and Sellers at the same time.'; const button = document.createElement('button'); button.type = 'button'; button.className = 'btn-secondary'; button.textContent = 'Start contract amendment'; button.onclick = () => openDraftDialog(approved); card.appendChild(button); }
    catch (error) { card.querySelector('p').textContent = root.hofApprovedSourceStatusCopy?.(error) || 'We couldn’t open that document. Please try again.'; }
  }
  const prior = root.renderAccountDashboard; root.renderAccountDashboard = function () { if (typeof prior === 'function') prior.apply(this, arguments); renderCard(); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderCard, { once: true }); else renderCard();
})();
