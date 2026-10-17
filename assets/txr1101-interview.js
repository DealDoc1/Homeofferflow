(function (root) {
  'use strict';
  const FORM_CODE = 'TXR-1101';
  const textLimits = {
    client_address:300, client_city_state_zip:180, client_phone:80, client_email:180, client_email_2:180,
    property_address:400, lot:150, block:150, subdivision:600, city:180, county:120,
    exclusions:2000, other_compensation:2000, other_fees:2000, payment_county:120,
    mls_delay_purpose:1500, scheduling_companies:800, financial_exceptions:2000,
    liens:2000, relocation_entity:500, districts:2000, special_provisions:4000, other_documents:2000
  };
  const choices = {
    hoa:[['yes','Yes'],['no','No']],
    fee_basis:[['percentage','Percentage'],['flat','Dollar amount'],['none','Other compensation only']],
    additional_fee_basis:[['none','No additional amount'],['percentage','Additional percentage'],['flat','Additional dollar amount']],
    disclose_buyer_expenses:[['yes','Yes'],['no','No']],
    mls_filing:[['standard','Within the required MLS deadline'],['delayed','After an agreed delay'],['none','Do not file in the MLS']],
    internet_display:[['full','Show the listing and address'],['hide_address','Hide the property address'],['hide_listing','Do not display the listing online']],
    keybox:[['yes','Yes'],['no','No']],
    intermediary:[['authorized','Authorize intermediary representation'],['not_authorized','Do not authorize intermediary representation']],
    foreign_person:[['unanswered','Not yet confirmed'],['yes','Yes'],['no','No']],
    signer_plan:[['clients_and_associate','Seller(s) and me as the broker’s associate'],['clients_and_broker','Seller(s) and the broker']]
  };
  const financing = [['conventional','Conventional'],['va','VA'],['fha','FHA'],['cash','Cash'],
    ['texas_veterans','Texas Veterans Land Program'],['owner','Owner financing'],['other','Other']];
  // These selections identify Paragraph 19 documents, not attachments or seller answers.
  const documentChoices = [
    ['A','Information About Brokerage Services'], ['B','Seller’s Disclosure Notice'],
    ['C','Lead-based paint disclosure'], ['D','Existing survey affidavit or declaration'],
    ['E','Water or statutory tax district notice'], ['F','Public improvement district notice'],
    ['G','Owners’ association information request'], ['H','Mortgage information request'],
    ['I','Mineral clause information'], ['J','On-site sewer information'],
    ['K','Property insurance information'], ['L','Flood hazard information'],
    ['M','Condominium listing addendum'], ['N','Tenant keybox authorization'],
    ['O','Authorization to disclose and advertise information'], ['P','Groundwater and surface water rights disclosure']
  ];
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const capture = () => ({id:root.hofAuth?.session?.user?.id, epoch:root.__hofAccountProfileEpoch || 0});
  const current = actor => Boolean(actor.id) && actor.id === root.hofAuth?.session?.user?.id && actor.epoch === (root.__hofAccountProfileEpoch || 0);
  const activeAgent = () => Boolean(root.hofAuth?.session?.user) && ['agent','broker','brokerage_admin','broker_admin','owner','team_lead']
    .includes(String(root.hofAuth?.role || root.hofAuth?.authoritativeProfile?.role || '').toLowerCase());

  function collect(values) {
    const get = name => String(values.get(name) ?? '').trim();
    const answers = {};
    Object.keys(textLimits).forEach(key => { answers[key] = get(key); });
    Object.keys(choices).forEach(key => { answers[key] = get(key); });
    ['term_start','term_end','listing_price','fee_amount','additional_fee_amount','protection_days','mls_delay_days']
      .forEach(key => { answers[key] = get(key); });
    ['listing_price','fee_amount','additional_fee_amount'].forEach(key => { answers[key] = answers[key].replace(/,/g,''); });
    for (const prefix of ['fee','additional_fee']) if (answers[prefix+'_basis'] === 'none') answers[prefix+'_amount'] = '';
    if (answers.mls_filing !== 'delayed') { answers.mls_delay_days = ''; answers.mls_delay_purpose = ''; }
    if (answers.mls_filing === 'none') answers.internet_display = 'not_applicable';
    answers.financing = values.getAll('financing');
    answers.addenda = values.getAll('addenda');
    answers.built_before_1978 = get('built_before_1978') || 'unanswered';
    answers.request_hoa_information = get('request_hoa_information') || 'unanswered';
    // Do not mark a document based on unknown age, an unchecked box, or an inferred seller answer.
    if (get('built_before_1978') === 'yes' && !answers.addenda.includes('C')) answers.addenda.push('C');
    if (answers.hoa === 'yes' && get('request_hoa_information') === 'yes' && !answers.addenda.includes('G')) answers.addenda.push('G');
    answers.addenda.sort();
    return {clientNames:[get('seller_one'),get('seller_two')].filter(Boolean), agreementData:answers};
  }

  function prefill(workspace, saved) {
    if (saved) return {...saved.agreement_data, seller_one:saved.client_names?.[0] || '', seller_two:saved.client_names?.[1] || ''};
    return {property_address:workspace?.property_address || '', seller_one:workspace?.seller_names?.[0] || '',
      seller_two:workspace?.seller_names?.[1] || ''};
  }

  function validateTerms(payload) {
    const a = payload.agreementData;
    if (!payload.clientNames.length) return 'Enter the seller’s full name.';
    if (a.term_end < a.term_start) return 'The listing end date must be on or after its start date.';
    if (!/^\d+(?:\.\d{1,2})?$/.test(a.listing_price) || !(Number(a.listing_price) > 0)) return 'Enter a listing price greater than zero with no more than two decimal places.';
    for (const prefix of ['fee','additional_fee']) {
      if (a[prefix+'_basis'] !== 'none') {
        const amount = a[prefix+'_amount'], places = a[prefix+'_basis'] === 'percentage' ? 4 : 2;
        if (!new RegExp('^\\d+(?:\\.\\d{1,'+places+'})?$').test(amount) ||
            (a[prefix+'_basis'] === 'percentage' && Number(amount) > 100)) return 'Check the agreed compensation amount. Enter zero explicitly if applicable.';
      }
    }
    if (a.fee_basis === 'none' && a.additional_fee_basis === 'none' && !a.other_compensation) return 'Enter the agreed compensation, including zero if applicable.';
    if (a.mls_filing === 'delayed' && (!(Number(a.mls_delay_days) >= 1) || !a.mls_delay_purpose)) return 'Enter the MLS delay and its purpose.';
    return '';
  }

  // Pure answer mapping is shared with isolated runtime tests, not a browser data store.
  if (typeof module !== 'undefined' && module.exports) module.exports = {collect,prefill,validateTerms,choices,textLimits,documentChoices};
  const document = root.document;
  if (!document) return;
  let opening = false;
  const field = (name,label,options={}) => `<label${options.wide ? ' class="hof-agreement-wide"' : ''}>${label}<input name="${name}" ${options.required ? 'required' : ''} type="${options.type || 'text'}" maxlength="${textLimits[name] || options.max || 300}" ${options.type === 'email' ? 'autocomplete="email"' : ''} ${name.includes('address') ? 'autocomplete="street-address" inputmode="text"' : ''} ${options.money ? 'inputmode="decimal"' : ''}></label>`;
  const area = (name,label) => `<label class="hof-agreement-wide">${label}<textarea name="${name}" maxlength="${textLimits[name]}" rows="3"></textarea></label>`;
  const select = (name,label) => `<label class="hof-agreement-wide">${label}<select name="${name}" aria-label="${escape(label)}" required><option value="">Choose one</option>${choices[name].map(([value,title]) => `<option value="${value}">${title}</option>`).join('')}</select></label>`;
  const yesNo = (name,label) => `<label class="hof-agreement-wide">${label}<select name="${name}" aria-label="${escape(label)}"><option value="unanswered">Not yet confirmed</option><option value="yes">Yes</option><option value="no">No</option></select></label>`;

  async function openInterview(options={}) {
    if (opening) return;
    if (!activeAgent()) throw new Error('Sign in to your agent account to prepare a listing agreement.');
    const actor = capture();
    if (document.getElementById('txr1101Interview')) return;
    opening = true;
    let saved = null, approved;
    try {
      if (options.agreementId) {
        const response = await root.fetch(`/api/admin-dashboard?scope=txr1101_draft&agreement_id=${encodeURIComponent(options.agreementId)}`, {headers:{Authorization:`Bearer ${root.hofAuth.session.access_token}`},cache:'no-store'});
        const result = await response.json();
        if (!current(actor)) return;
        if (!response.ok) throw new Error(result.error || 'We couldn’t open that saved listing agreement.');
        saved = result.agreement;
      }
      approved = await root.hofLoadApprovedBrokerageSource?.(FORM_CODE);
      if (!current(actor)) return;
      if (!approved?.id) throw new Error('We couldn’t open the listing agreement. Please try again.');
    } finally { opening = false; }
    const initial = prefill(options.workspace, saved);
    const modal = document.createElement('div');
    modal.id = 'txr1101Interview'; modal.className = 'hof-agreement-modal';
    modal.setAttribute('role','dialog'); modal.setAttribute('aria-modal','true'); modal.setAttribute('aria-labelledby','txr1101Title');
    modal.innerHTML = `<form id="txr1101InterviewForm" class="hof-agreement-dialog" novalidate>
      <div class="hof-listing-heading"><p class="hof-agent-question-step" id="txr1101Progress"></p><button type="button" data-close aria-label="Close listing interview">×</button></div>
      <h3 id="txr1101Title">Prepare a sale listing agreement</h3>
      <section data-step="0"><h4>Who is selling, and which property?</h4><div class="hof-agreement-grid">
        ${field('seller_one','Seller 1 full legal name',{required:true})}${field('seller_two','Seller 2 full legal name (optional)')}
        ${field('client_email','Seller 1 email (optional)',{type:'email'})}${field('client_email_2','Seller 2 email (optional)',{type:'email'})}
        ${field('property_address','Property address',{required:true,wide:true})}
        <details class="hof-agreement-wide"><summary>Seller contact and legal description</summary><div class="hof-agreement-grid">
          ${field('client_address','Seller mailing address')}${field('client_city_state_zip','Seller city, state and ZIP')}${field('client_phone','Seller phone')}
          ${field('lot','Lot')}${field('block','Block')}${field('subdivision','Subdivision')}${field('city','City')}${field('county','County')}
        </div></details>
      </div></section>
      <section data-step="1"><h4>What are the agreed listing terms?</h4><div class="hof-agreement-grid">
        ${field('listing_price','Listing price ($)',{required:true,money:true})}${field('term_start','Listing starts',{required:true,type:'date'})}${field('term_end','Listing ends',{required:true,type:'date'})}
        ${select('fee_basis','How is the broker’s compensation calculated?')}
        <div class="hof-agreement-wide" data-condition="fee"><div class="hof-agreement-grid">${field('fee_amount','Agreed compensation amount',{required:true,money:true})}</div><small data-fee-unit></small></div>
        ${select('additional_fee_basis','Is additional compensation agreed if the buyer is unrepresented?')}
        <div class="hof-agreement-wide" data-condition="additional_fee">${field('additional_fee_amount','Additional compensation amount',{required:true,money:true})}</div>
        ${area('other_compensation','Other agreed compensation (optional)')}
        <p class="hof-agreement-wide hof-listing-note">Compensation is negotiable. Enter only the terms agreed with the seller; no amount is preselected.</p>
        <details class="hof-agreement-wide"><summary>Other fees and protection period</summary><div class="hof-agreement-grid">${area('other_fees','Other fees (optional)')}${field('protection_days','Protection period (days)',{max:4})}${field('payment_county','County where compensation is paid')}</div></details>
      </div></section>
      <section data-step="2"><h4>How should the property be marketed?</h4><div class="hof-agreement-grid">
        ${select('mls_filing','When should the listing be filed in the MLS?')}
        <div class="hof-agreement-wide" data-condition="delay"><div class="hof-agreement-grid">${field('mls_delay_days','Delay (days)',{required:true,max:4})}${area('mls_delay_purpose','Purpose of the delay')}</div></div>
        <div class="hof-agreement-wide" data-condition="internet">${select('internet_display','What may be displayed online?')}</div>
        ${select('keybox','May a keybox be used?')}${field('scheduling_companies','Showing service or scheduling company (optional)',{wide:true})}
        <fieldset class="hof-agreement-wide hof-listing-checks"><legend>Which financing options may be advertised?</legend>${financing.map(([value,label]) => `<label><input type="checkbox" name="financing" value="${value}"> ${label}</label>`).join('')}</fieldset>
        ${select('disclose_buyer_expenses','May the broker disclose that the seller will consider contributing to buyer expenses?')}
      </div></section>
      <section data-step="3"><h4>What should the agreement reflect?</h4><div class="hof-agreement-grid">
        ${select('hoa','Is the property subject to mandatory owners’ association membership?')}
        ${select('intermediary','If the broker also represents a buyer, what does the seller authorize?')}
        ${select('foreign_person','Has the seller confirmed foreign-person status for federal tax purposes?')}
        <p class="hof-agreement-wide hof-listing-note">Tax status must come from the seller. You can save now if it is not yet confirmed; it must be answered before sending.</p>
        ${area('exclusions','Items excluded from the sale (optional)')}
        <details class="hof-agreement-wide"><summary>Exceptions, liens and additional terms</summary><div class="hof-agreement-grid">
          ${area('financial_exceptions','Exceptions to the seller’s financial representations (optional)')}${area('liens','Known liens or encumbrances to identify (optional)')}
          ${area('relocation_entity','Employer, relocation company or other entity providing sale benefits (optional)')}${area('districts','Districts identified by the seller (optional)')}
          ${area('special_provisions','Special provisions supplied by the parties or their attorney (optional)')}
        </div></details>
      </div></section>
      <section data-step="4"><h4>Which related documents are needed?</h4><div class="hof-agreement-grid">
        ${yesNo('built_before_1978','Was the home built before 1978?')}
        <div class="hof-agreement-wide" data-condition="hoa">${yesNo('request_hoa_information','Is an owners’ association information request needed?')}</div>
        <p class="hof-agreement-wide hof-listing-note">These choices identify related documents in the listing agreement. They do not attach or complete those documents. A missing seller disclosure does not stop you from preparing this agreement.</p>
        <details class="hof-agreement-wide"><summary>Review the related-document checklist</summary><fieldset class="hof-listing-checks"><legend>Documents that apply</legend>${documentChoices.map(([value,label]) => `<label><input type="checkbox" name="addenda" value="${value}"> ${label}</label>`).join('')}</fieldset></details>
        ${area('other_documents','Other related documents (optional)')}
      </div></section>
      <section data-step="5"><h4>Review before preparing</h4><div id="txr1101Review"></div><div class="hof-agreement-grid">
        ${select('signer_plan','Who will sign for the brokerage?')}
      </div><p class="hof-listing-note">Review the completed PDF and confirm each recipient in your saved documents. Nothing is sent from this interview.</p></section>
      <div id="txr1101Status" class="hof-iabs-status" role="status" aria-live="polite"></div>
      <div class="hof-agreement-footer"><button type="button" class="btn-secondary" data-back>Back</button><button type="button" class="btn-primary" data-next>Continue</button><button type="submit" class="btn-primary" data-save>Prepare agreement</button></div>
    </form>`;
    document.body.appendChild(modal);
    const form = modal.querySelector('form'), status = modal.querySelector('#txr1101Status');
    const back = form.querySelector('[data-back]'), next = form.querySelector('[data-next]'), save = form.querySelector('[data-save]');
    let step = 0, busy = false, uncertain = false;
    for (const [name,value] of Object.entries(initial)) {
      if (Array.isArray(value)) form.querySelectorAll(`[name="${name}"]`).forEach(input => { input.checked = value.includes(input.value); });
      else if (form.elements.namedItem(name)) form.elements.namedItem(name).value = value;
    }
    const validActor = () => { if (current(actor) && activeAgent()) return true; modal.remove(); return false; };
    const get = name => form.elements.namedItem(name)?.value || '';
    const sync = () => {
      const conditions = {fee:get('fee_basis') && get('fee_basis') !== 'none', additional_fee:get('additional_fee_basis') && get('additional_fee_basis') !== 'none',
        delay:get('mls_filing') === 'delayed', internet:get('mls_filing') && get('mls_filing') !== 'none', hoa:get('hoa') === 'yes'};
      form.querySelectorAll('[data-condition]').forEach(panel => {
        const visible = Boolean(conditions[panel.dataset.condition]);
        panel.hidden = !visible; panel.style.display = visible ? '' : 'none';
        panel.querySelectorAll('input,select,textarea').forEach(control => { control.disabled = !visible || busy || uncertain; });
      });
      form.elements.namedItem('mls_delay_purpose').required = conditions.delay;
      form.querySelector('[data-fee-unit]').textContent = get('fee_basis') === 'percentage' ? 'Enter a percentage, such as 2.5. No compensation rate is suggested.' : 'Enter the agreed dollar amount, including zero if applicable.';
      // Pre-1978 age requires the lead disclosure selection; do not let an unchecked checklist erase it.
      const lead = form.querySelector('[name="addenda"][value="C"]');
      if (get('built_before_1978') === 'yes') lead.checked = true;
    };
    function showStep() {
      sync();
      form.querySelectorAll('[data-step]').forEach(panel => { panel.hidden = Number(panel.dataset.step) !== step; panel.style.display = panel.hidden ? 'none' : ''; });
      form.querySelector('#txr1101Progress').textContent = `Sale listing · ${step+1} of 6`;
      back.hidden = step === 0; next.hidden = step === 5; save.hidden = step !== 5;
      back.style.display = back.hidden ? 'none' : ''; next.style.display = next.hidden ? 'none' : ''; save.style.display = save.hidden ? 'none' : '';
      if (step === 5) renderReview();
      form.querySelector(`[data-step="${step}"] h4`)?.setAttribute('tabindex','-1');
      form.querySelector(`[data-step="${step}"] h4`)?.focus();
    }
    function invalidStep(index) {
      const panel = form.querySelector(`[data-step="${index}"]`);
      for (const control of panel.querySelectorAll('input,select,textarea')) {
        if (!control.disabled && !control.checkValidity()) {
          step = index; showStep(); control.closest('details')?.setAttribute('open',''); control.reportValidity(); return true;
        }
      }
      return false;
    }
    function renderReview() {
      const a = collect(new root.FormData(form)).agreementData;
      const label = key => choices[key]?.find(item => item[0] === a[key])?.[1] || 'Not selected';
      const displayDate = value => /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(value+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}) : value;
      const money = value => Number(value).toLocaleString('en-US',{style:'currency',currency:'USD'});
      const rows = [['Property',a.property_address],['Sellers',[get('seller_one'),get('seller_two')].filter(Boolean).join(' · ')],
        ['Listing price',a.listing_price ? money(a.listing_price) : ''],['Listing term',`${displayDate(a.term_start)} to ${displayDate(a.term_end)}`],
        ['Broker compensation',a.fee_basis === 'none' ? a.other_compensation : `${a.fee_amount}${a.fee_basis === 'percentage' ? '%' : ' dollars'}`],
        ['Additional compensation',a.additional_fee_basis === 'none' ? 'None' : `${a.additional_fee_amount}${a.additional_fee_basis === 'percentage' ? '%' : ' dollars'}`],
        ['MLS filing',label('mls_filing')],['Online display',a.mls_filing === 'none' ? 'Not applicable' : label('internet_display')],
        ['Keybox',label('keybox')],['Buyer expense disclosure',label('disclose_buyer_expenses')],
        ['Financing',a.financing.map(value => financing.find(item => item[0] === value)?.[1]).join(' · ') || 'None selected'],
        ['Intermediary',label('intermediary')],['Seller tax status',label('foreign_person')]];
      const list = collect(new root.FormData(form)).agreementData.addenda.map(code => documentChoices.find(([value]) => value === code)?.[1]).filter(Boolean);
      form.querySelector('#txr1101Review').innerHTML = `<dl>${rows.map(([key,value]) => `<div><dt>${key}</dt><dd>${escape(value || 'Not provided')}</dd></div>`).join('')}</dl><p><strong>Related-document checklist:</strong> ${escape(list.join(' · ') || 'None selected')}</p><p class="hof-listing-note">Your account supplies the brokerage and agent details. Check those details and all optional blanks in the completed PDF.</p>`;
    }
    const leave = () => { if (!busy) modal.remove(); };
    const reviewSaved = async () => {
      if (!validActor()) return;
      root.showAccountTab?.('dashboard');
      try {
        if (typeof root.hofOpenPreparedAgreement !== 'function') throw new Error('Document list is not available yet.');
        const opened = await root.hofOpenPreparedAgreement(saved?.id);
        if (opened === false) throw new Error('The account changed before the document list opened.');
        if (current(actor)) modal.remove();
      } catch (_) {
        if (!validActor()) return;
        status.className = 'hof-iabs-status error';
        status.textContent = 'Your answers are still here. Open Prepared documents from your account to check the saved agreement.';
      }
    };
    modal.querySelector('[data-close]').addEventListener('click',leave);
    modal.addEventListener('keydown',event => {
      if (event.key === 'Escape') { event.preventDefault(); leave(); }
      if (event.key === 'Tab') {
        const controls = [...form.querySelectorAll('button,input,select,textarea,summary')].filter(el => !el.disabled && el.getClientRects().length);
        if (!controls.length) return;
        if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls[controls.length-1].focus(); }
        else if (!event.shiftKey && document.activeElement === controls[controls.length-1]) { event.preventDefault(); controls[0].focus(); }
      }
    });
    form.addEventListener('change',sync);
    next.addEventListener('click',() => { if (!validActor() || busy || uncertain || invalidStep(step)) return; status.textContent = ''; step++; showStep(); });
    back.addEventListener('click',() => { if (!validActor() || busy || uncertain) return; status.textContent = ''; step = Math.max(0,step-1); showStep(); });
    form.addEventListener('submit',async event => {
      event.preventDefault();
      if (!validActor() || busy || uncertain) return;
      if (step !== 5) { next.click(); return; }
      for (let index=0;index<6;index++) if (invalidStep(index)) return;
      const payload = collect(new root.FormData(form)), error = validateTerms(payload);
      if (error) { status.className = 'hof-iabs-status error'; status.textContent = error; return; }
      busy = true; save.disabled = true; back.disabled = true; save.setAttribute('aria-busy','true');
      status.className = 'hof-iabs-status'; status.textContent = 'Preparing your agreement…';
      const body = {action:saved ? 'update_txr_1101_draft' : 'create_txr_1101_draft',formCode:FORM_CODE,formSourceId:approved.id,...payload};
      if (saved) { body.agreementId = saved.id; body.updatedAt = saved.updated_at; }
      // Freeze answers through readback so the saved-document confirmation always matches the screen.
      form.querySelectorAll('input,select,textarea').forEach(control => { control.disabled = true; });
      let response;
      try {
        response = await root.fetch('/api/admin-dashboard',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${root.hofAuth.session.access_token}`},body:JSON.stringify(body)});
        if (response.status >= 500 || response.status === 409) uncertain = true;
        const result = await response.json();
        if (!current(actor) || !modal.isConnected) { modal.remove(); return; }
        if (!response.ok) {
          uncertain = uncertain || result.refreshRequired === true || /changed in another window/i.test(String(result.error || ''));
          throw new Error(result.error || 'We couldn’t prepare the agreement. Check your answers and try again.');
        }
        if (!result.agreement?.id || !result.agreement.updated_at) { uncertain = true; throw new Error('The save could not be confirmed. Check your saved documents before trying again.'); }
        saved = result.agreement;
        status.className = 'hof-iabs-status ready';
        status.innerHTML = 'Your listing agreement is saved. <button type="button" class="btn-secondary" data-review-saved>Review and send</button>';
        status.querySelector('[data-review-saved]').addEventListener('click',reviewSaved);
        save.textContent = 'Save changes';
      } catch (problem) {
        if (!current(actor) || !modal.isConnected) { modal.remove(); return; }
        if (!response || response.ok) uncertain = true;
        status.className = 'hof-iabs-status error';
        status.textContent = uncertain ? 'The save could not be confirmed. Check your saved documents before trying again.'
          : (root.hofCustomerActionError?.(problem,'We couldn’t prepare the agreement. Check your answers and try again.') || problem.message);
        if (uncertain) {
          const review = document.createElement('button'); review.type = 'button'; review.className = 'btn-secondary'; review.textContent = 'Check saved documents';
          review.addEventListener('click',reviewSaved);
          status.appendChild(review);
        }
      } finally {
        busy = false;
        form.querySelectorAll('input,select,textarea').forEach(control => { control.disabled = uncertain; });
        back.disabled = uncertain; save.disabled = uncertain; save.setAttribute('aria-busy','false'); sync();
      }
    });
    showStep();
  }
  root.hofOpenTxr1101Draft = openInterview;
})(typeof window !== 'undefined' ? window : {});
