(function () {
  const root = window;
  const FORM_CODE = 'TREC-62-0';
  const escape = value => String(value ?? '').replace(/[&<>\"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;'
  }[char]));
  const profile = () => root.hofAuth?.authoritativeProfile || {};
  const activeAgent = () => {
    const role = String(root.hofAuth?.role || profile().role || '').toLowerCase();
    return Boolean(root.hofAuth?.session?.user) &&
      ['agent', 'broker', 'brokerage_admin', 'broker_admin', 'owner', 'team_lead'].includes(role);
  };

  function names(form, party) {
    return [form.get(`${party}One`), form.get(`${party}Two`)]
      .map(value => String(value || '').trim()).filter(Boolean);
  }

  async function source() {
    const approved = await root.hofLoadApprovedBrokerageSource?.(FORM_CODE);
    if (!approved) throw new Error('TREC 62-0 is not available in the HomeOfferFlow form library yet.');
    return approved;
  }

  async function openDraftDialog(preloadedSource) {
    const approved = preloadedSource || await source();
    document.getElementById('trec620AgreementDialog')?.remove();
    const modal = document.createElement('div');
    modal.id = 'trec620AgreementDialog';
    modal.className = 'hof-agreement-modal';
    modal.innerHTML = `<form class="hof-agreement-dialog" id="trec620AgreementForm">
      <p class="hof-agent-question-step">Seller notice</p>
      <h3>Remove the backup-contract contingency</h3>
      <p>Use this after the first contract has ended and Seller is notifying the backup Buyer that the contingency is removed.</p>
      <div class="hof-agreement-grid">
        <label class="hof-agreement-wide">Property street address and city<input name="propertyAddress" required maxlength="400" autocomplete="street-address" inputmode="text" placeholder="1438 Whitaker Road, Van Alstyne, TX"></label>
        <label>Buyer 1 full name<input name="buyerOne" required maxlength="180" autocomplete="name"></label>
        <label>Buyer 2 full name (optional)<input name="buyerTwo" maxlength="180" autocomplete="name"></label>
        <label>Seller 1 full name<input name="sellerOne" required maxlength="180" autocomplete="name"></label>
        <label>Seller 2 full name (optional)<input name="sellerTwo" maxlength="180" autocomplete="name"></label>
        <label class="hof-agreement-wide">Date this notice will be delivered to Buyer<input name="deliveryDate" type="date" required></label>
        <p class="hof-agreement-wide" style="color:var(--gray-light);line-height:1.5">Do not send for signature until the delivery date is known. If delivery changes, prepare a new copy. The optional fee and earnest-money receipt sections remain blank for the escrow agent.</p>
        <label class="hof-agreement-wide hof-agreement-services"><input name="sellerNoticeAcknowledgment" type="checkbox" required> I confirm the first contract has terminated, the backup contingency is removed, the delivery date comes from the transaction record, and the completed notice will be delivered to Buyer under the contract.</label>
      </div>
      <div id="trec620DraftStatus" class="hof-iabs-status" role="status" aria-live="polite"></div>
      <div class="hof-agreement-footer"><button class="btn-secondary" type="button" id="trec620Cancel">Cancel</button><button class="btn-primary" type="submit">Prepare document</button></div>
    </form>`;
    document.body.appendChild(modal);
    modal.querySelector('#trec620Cancel').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', event => { if (event.target === modal) modal.remove(); });
    modal.querySelector('form').addEventListener('submit', async event => {
      event.preventDefault();
      const values = new FormData(event.currentTarget);
      const button = event.currentTarget.querySelector('button[type="submit"]');
      const status = modal.querySelector('#trec620DraftStatus');
      if (button.disabled) return;
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      button.textContent = 'Preparing document…';
      status.className = 'hof-iabs-status';
      status.textContent = 'Preparing the Seller notice…';
      try {
        const response = await fetch('/api/admin-dashboard', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${root.hofAuth?.session?.access_token || ''}` },
          body: JSON.stringify({
            action: 'create_trec_62_0_draft', formCode: FORM_CODE, formSourceId: approved.id,
            propertyAddress: values.get('propertyAddress'), buyerNames: names(values, 'buyer'), sellerNames: names(values, 'seller'),
            deliveryDate: values.get('deliveryDate'), sellerNoticeAcknowledgment: values.get('sellerNoticeAcknowledgment') === 'on'
          })
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.error || 'Could not prepare the Seller notice.');
        button.setAttribute('aria-busy', 'false');
        button.textContent = 'Document ready';
        status.className = 'hof-iabs-status ready';
        status.innerHTML = 'Your notice is ready. <button type="button" class="btn-secondary">Review and send</button>';
        status.querySelector('button').addEventListener('click', async () => {
          modal.remove();
          await root.hofOpenPreparedAgreement?.();
        });
      } catch (error) {
        console.error('TREC 62-0 preparation failed:', error);
        status.className = 'hof-iabs-status error';
        status.textContent = root.hofCustomerActionError?.(error, 'We couldn’t prepare the Seller notice. Review your answers and try again.') || 'We couldn’t prepare the Seller notice. Review your answers and try again.';
        button.disabled = false;
        button.setAttribute('aria-busy', 'false');
        button.textContent = 'Prepare document';
      }
    });
    modal.querySelector('[name="propertyAddress"]')?.focus();
  }

  root.hofOpenTrec620Draft = () => openDraftDialog().catch(error => {
    console.error('TREC 62-0 source check failed:', error);
    root.announceWorkspaceStatus?.(root.hofApprovedSourceStatusCopy?.(error) || 'We couldn’t open that document. Please try again.');
  });

  async function renderCard() {
    const panel = document.getElementById('accountPanelRelationships');
    if (!panel || !activeAgent() || document.getElementById('trec620AgreementCard')) return;
    const card = document.createElement('div');
    card.id = 'trec620AgreementCard';
    card.className = 'account-card hof-agreement-card';
    card.innerHTML = '<h4>Remove a Backup-Contract Contingency</h4><p>Checking the HomeOfferFlow form library…</p>';
    panel.appendChild(card);
    try {
      const approved = await source();
      card.querySelector('p').textContent = 'Prepare the Seller notice through a short interview, review it, and send both Sellers at the same time when two signatures are needed.';
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn-secondary';
      button.textContent = 'Start Seller notice';
      button.addEventListener('click', () => openDraftDialog(approved));
      card.appendChild(button);
    } catch (error) {
      card.querySelector('p').textContent = root.hofApprovedSourceStatusCopy?.(error) || 'We couldn’t open that document. Please try again.';
    }
  }

  const priorDashboard = root.renderAccountDashboard;
  root.renderAccountDashboard = function renderAccountDashboardWithTrec620() {
    if (typeof priorDashboard === 'function') priorDashboard.apply(this, arguments);
    renderCard();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderCard, { once: true });
  else renderCard();
})();
