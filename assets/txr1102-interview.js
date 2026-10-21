(function(root){
  'use strict';
  // Lease-specific questions; saving, account isolation and navigation are shared.
  const textLimits={client_address:300,client_city_state_zip:180,client_phone:80,client_email:180,client_email_2:180,
    property_address:400,lot:150,block:150,subdivision:600,city:180,county:120,non_real_estate_items:2000,exclusions:2000,
    fee_other:2000,renewal_other:2000,sale_fee_other:2000,reimbursable_expenses:2000,payment_county:120,
    mls_delay_purpose:1500,scheduling_companies:800,make_ready_service_fee:1500,financial_exceptions:2000,liens:2000,
    common_area_fees:2000,health_safety_conditions:3000,special_provisions:4000,other_documents:2000};
  const preferenceTextLimits={rent_due_other:300,animal_restrictions:1500,utilities_exceptions:1500,yard_contractor:400,
    pool_contractor:400,pool_other:1000,repair_phone:100,unrepaired_items:2000,lease_special_provisions:3000,lease_other:2000};
  const preferenceIntegers=['late_after_days','guests_days','vehicle_count','keybox_last_days','inventory_days'];
  const preferenceAmounts=['initial_late_amount','daily_late_amount','animal_deposit','animal_monthly_rent','animal_one_time_fee',
    'animal_violation_initial','animal_violation_daily','security_deposit','trip_charge','keybox_withdrawal_fee','liability_insurance',
    'tenant_replacement_amount','landlord_replacement_amount'];
  const percentageChoices=[['month_percentage','Percentage of one month’s rent'],['total_percentage','Percentage of rent over the lease term'],['other','Other agreed terms']];
  const choices={
    hoa:[['yes','Yes'],['no','No']],fee_scope:[['with_other_broker','Listing and cooperating brokers'],['broker_only','Listing broker only']],
    fee_basis:percentageChoices,renewal_basis:percentageChoices,sale_fee_basis:[['percentage','Percentage of the sales price'],['other','Other agreed terms']],
    cobroker_basis:[...percentageChoices.slice(0,2),['flat','Dollar amount']],
    mls_filing:[['standard','Within the required MLS deadline'],['delayed','After an agreed delay'],['none','Do not file in the MLS']],
    internet_display:[['full','Show the listing and address'],['hide_address','Hide the property address'],['hide_listing','Do not display the listing online']],
    keybox:[['yes','Yes'],['no','No']],intermediary:[['authorized','Authorize intermediary representation'],['not_authorized','Do not authorize intermediary representation']],
    make_ready:[['not_authorized','No make-ready authority'],['landlord_pays','Authorize work paid directly by the landlord'],['broker_reimbursed','Authorize work paid by the broker and reimbursed by the landlord']],
    signer_plan:[['clients_and_associate','Landlord(s) and me as the broker’s associate'],['clients_and_broker','Landlord(s) and the broker']]
  };
  const preferenceChoices={rent_due:[['first','First day of the month'],['other','Another agreed day']],
    initial_late_basis:[['flat','Dollar amount'],['percentage','Percentage of monthly rent']],animals:[['not_permitted','Not permitted'],['permitted','Permitted, subject to agreed terms']],
    yard:[['landlord','Landlord'],['tenant','Tenant'],['tenant_contractor','Tenant arranges a contractor'],['named_contractor','Named contractor']],
    pool:[['landlord','Landlord'],['tenant','Tenant'],['tenant_contractor','Tenant arranges a contractor'],['named_contractor','Named contractor'],['other','Other agreed responsibility']],
    tenant_replacement_basis:[['flat','Dollar amount'],['percentage','Percentage of one month’s rent']],
    landlord_replacement_basis:[['flat','Dollar amount'],['percentage','Percentage of one month’s rent']]};
  const documentChoices=[['A','Information About Brokerage Services'],['B','Rental flood disclosure'],['C','Lead-based paint disclosure for a lease'],
    ['D','Owners’ association information request'],['E','Special flood hazard information'],['F','Condominium listing addendum'],
    ['G','Tenant keybox authorization'],['H','On-site sewer information'],['I','IRS Form W-9 or W-8'],
    ['J','Owner’s authorization for unescorted access'],['K','Assistance-animal information for landlords'],['L','Other related documents']];
  const noticeKeys=['address','city_state_zip','phone','email','email_2'];
  const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function collect(values){
    const get=key=>String(values.get(key)??'').trim(),a={};
    Object.keys(textLimits).forEach(key=>{a[key]=get(key);});
    Object.keys(choices).forEach(key=>{a[key]=get(key);});
    for(const key of ['term_start','term_end','listing_price','lease_min_months','lease_max_months','fee_amount','cobroker_amount',
      'renewal_amount','sale_fee_amount','protection_days','mls_delay_days','make_ready_limit'])a[key]=get(key);
    for(const key of ['listing_price','fee_amount','cobroker_amount','renewal_amount','sale_fee_amount','make_ready_limit'])a[key]=a[key].replace(/,/g,'');
    for(const prefix of ['fee','renewal','sale_fee']){
      if(a[prefix+'_basis']==='other')a[prefix+'_amount']='';else a[prefix+'_other']='';
    }
    if(a.fee_scope!=='with_other_broker'){a.cobroker_basis='';a.cobroker_amount='';}
    if(a.mls_filing!=='delayed'){a.mls_delay_days='';a.mls_delay_purpose='';}
    if(a.mls_filing==='none')a.internet_display='not_applicable';
    if(a.make_ready==='not_authorized'){a.make_ready_limit='';a.make_ready_service_fee='';}
    a.built_before_1978=get('built_before_1978')||'unanswered';
    a.addenda=[...new Set([...values.getAll('addenda'),'B'])];
    if(a.built_before_1978!=='no'&&!a.addenda.includes('C'))a.addenda.push('C');
    if(a.other_documents&&!a.addenda.includes('L'))a.addenda.push('L');
    a.addenda.sort();a.broker_notice_contacts=Object.fromEntries(noticeKeys.map(key=>[key,get('broker_notice_'+key)]));
    a.include_rental_preferences=values.get('include_rental_preferences')==='on';
    if(a.include_rental_preferences){
      for(const key of Object.keys(preferenceTextLimits))a[key]=get(key);
      for(const key of Object.keys(preferenceChoices))a[key]=get(key)||'unspecified';
      for(const key of [...preferenceIntegers,...preferenceAmounts])a[key]=get(key).replace(/,/g,'');
      if(a.rent_due!=='other')a.rent_due_other='';
      if(a.animals!=='permitted')for(const key of ['animal_restrictions','animal_deposit','animal_monthly_rent','animal_one_time_fee'])a[key]='';
      for(const prefix of ['initial_late','tenant_replacement','landlord_replacement'])if(a[prefix+'_basis']==='unspecified')a[prefix+'_amount']='';
      if(a.yard!=='named_contractor')a.yard_contractor='';
      if(a.pool!=='named_contractor')a.pool_contractor='';
      if(a.pool!=='other')a.pool_other='';
    }
    return {clientNames:[get('seller_one'),get('seller_two')].filter(Boolean),agreementData:a};
  }
  function prefill(workspace,saved,context){
    const initial=saved?{...saved.agreement_data,seller_one:saved.client_names?.[0]||'',seller_two:saved.client_names?.[1]||''}
      :{property_address:workspace?.property_address||'',seller_one:workspace?.seller_names?.[0]||'',seller_two:workspace?.seller_names?.[1]||'',addenda:['A','B']};
    const contacts=saved?.agreement_data?.broker_notice_contacts??context?.noticeContacts;
    if(contacts)for(const key of noticeKeys)initial['broker_notice_'+key]=String(contacts[key]||'');
    return initial;
  }
  function validateTerms(payload,step){
    const a=payload.agreementData,integer=value=>/^\d{1,4}$/.test(value);
    const at=index=>step===undefined||step===index;
    if(at(0)&&!payload.clientNames.length)return 'Enter the landlord’s full legal name.';
    if(at(1)){
    if(a.term_end<a.term_start)return 'The listing end date must be on or after its start date.';
    if(!/^\d+(?:\.\d{1,2})?$/.test(a.listing_price)||!(Number(a.listing_price)>0))return 'Enter a monthly rent greater than zero with no more than two decimal places.';
    if(!integer(a.lease_min_months)||!integer(a.lease_max_months)||Number(a.lease_min_months)<1||Number(a.lease_max_months)<Number(a.lease_min_months))return 'Enter valid minimum and maximum lease terms in months.';
    }
    if(at(2)){
    for(const prefix of ['fee','renewal','sale_fee']){
      if(a[prefix+'_basis']==='other'){if(!a[prefix+'_other'])return 'Describe the agreed compensation, including no compensation if applicable.';}
      else if(!/^\d+(?:\.\d{1,4})?$/.test(a[prefix+'_amount'])||Number(a[prefix+'_amount'])>9999.9999)return 'Check the agreed compensation percentage. Enter zero explicitly if applicable.';
    }
    if(a.fee_scope==='with_other_broker'){
      const decimals=a.cobroker_basis==='flat'?2:4;
      if(!new RegExp('^\\d+(?:\\.\\d{1,'+decimals+'})?$').test(a.cobroker_amount))return 'Enter the cooperating broker’s agreed compensation, including zero if applicable.';
      if(a.cobroker_basis===a.fee_basis&&Number(a.cobroker_amount)>Number(a.fee_amount))return 'The cooperating broker’s share cannot exceed the total compensation on the same basis.';
    }
    }
    if(at(3)){
    if(a.mls_filing==='delayed'&&(!integer(a.mls_delay_days)||Number(a.mls_delay_days)<1||!a.mls_delay_purpose))return 'Enter the agreed MLS delay and its purpose.';
    if(a.make_ready!=='not_authorized'&&(!/^\d+(?:\.\d{1,2})?$/.test(a.make_ready_limit)||!a.make_ready_service_fee))return 'Enter the authorized make-ready limit and agreed service fee, including zero if applicable.';
    }
    if(at(4)&&a.addenda.includes('L')&&!a.other_documents)return 'Describe the other related documents.';
    if(at(5)&&a.include_rental_preferences){
      for(const key of preferenceIntegers)if(a[key]&&!integer(a[key]))return 'Enter whole numbers for the rental preference periods and limits.';
      for(const key of preferenceAmounts){
        const prefix={initial_late_amount:'initial_late',tenant_replacement_amount:'tenant_replacement',landlord_replacement_amount:'landlord_replacement'}[key];
        const percent=prefix&&a[prefix+'_basis']==='percentage';
        if(a[key]&&(!new RegExp('^\\d+(?:\\.\\d{1,'+(percent?4:2)+'})?$').test(a[key])||(percent&&Number(a[key])>100)))return 'Check the rental preference amounts and percentages.';
        if(prefix&&a[prefix+'_basis']!=='unspecified'&&!a[key])return 'Enter the amount for each selected rental preference fee basis, including zero if applicable.';
      }
    }
    return '';
  }

  function markup({officeContext,officeIdentity,hasNoticeDetails}){
    const field=(name,label,options={})=>`<label${options.wide?' class="hof-agreement-wide"':''}>${label}<input name="${name}" ${options.required?'required':''} type="${options.type||'text'}" maxlength="${textLimits[name]||preferenceTextLimits[name]||options.max||80}" ${options.money?'inputmode="decimal"':''} ${options.integer?'inputmode="numeric" pattern="[0-9]+"':''} ${name.includes('address')?'autocomplete="street-address"':''}></label>`;
    const area=(name,label)=>`<label class="hof-agreement-wide">${label}<textarea name="${name}" maxlength="${textLimits[name]||preferenceTextLimits[name]}" rows="3"></textarea></label>`;
    const select=(name,label,optional=false)=>`<label class="hof-agreement-wide">${label}<select name="${name}" aria-label="${escape(label)}" ${optional?'':'required'}><option value="${optional?'unspecified':''}">${optional?'Not specified':'Choose one'}</option>${(choices[name]||preferenceChoices[name]).map(([value,title])=>`<option value="${value}">${title}</option>`).join('')}</select></label>`;
    const condition=(key,content)=>`<div class="hof-agreement-wide" data-condition="${key}"><div class="hof-agreement-grid">${content}</div></div>`;
    const step=(index,title,content)=>`<section data-step="${index}"><h4>${title}</h4><div class="hof-agreement-grid">${content}</div></section>`;
    const fee=(prefix,title)=>select(prefix+'_basis',title)+condition(prefix+'_amount',field(prefix+'_amount','Agreed percentage',{required:true,money:true}))+condition(prefix+'_other',area(prefix+'_other','Other agreed compensation'));
    const optionalAmount=(name,label)=>field(name,label,{money:true});
    return `<form id="txr1101InterviewForm" class="hof-agreement-dialog" novalidate>
      <div class="hof-listing-heading"><p class="hof-agent-question-step" id="txr1101Progress"></p><button type="button" data-close aria-label="Close listing interview">×</button></div>
      <h3 id="txr1101Title">Prepare a lease listing agreement</h3>
      ${step(0,'Who is the landlord, and which property?',field('seller_one','Landlord 1 full legal name',{required:true,max:300})+field('seller_two','Landlord 2 full legal name (optional)',{max:300})+
        field('client_email','Landlord 1 email (optional)',{type:'email'})+field('client_email_2','Landlord 2 email (optional)',{type:'email'})+field('property_address','Property address',{required:true,wide:true})+
        `<details class="hof-agreement-wide"><summary>Landlord contact and legal description</summary><div class="hof-agreement-grid">${field('client_address','Landlord mailing address')}${field('client_city_state_zip','Landlord city, state and ZIP')}${field('client_phone','Landlord phone',{type:'tel'})}${['lot','block','subdivision','city','county'].map(key=>field(key,key[0].toUpperCase()+key.slice(1))).join('')}</div></details>
        <details class="hof-agreement-wide" ${hasNoticeDetails?'':'open'}><summary>Brokerage contact details</summary><p>${escape(officeIdentity||'Check the brokerage name and license in your account profile.')}</p><p class="hof-listing-note">${officeContext?.unavailable?'Saved office details could not be loaded. Enter the details for this agreement here.':'Review the brokerage’s notice details. Changes here apply only to this agreement.'}</p><div class="hof-agreement-grid">
        ${field('broker_notice_address','Brokerage mailing address',{max:300,wide:true})}${field('broker_notice_city_state_zip','Brokerage city, state and ZIP',{max:180})}${field('broker_notice_phone','Brokerage phone',{type:'tel'})}${field('broker_notice_email','Brokerage notice email',{type:'email',max:180})}${field('broker_notice_email_2','Additional brokerage notice email (optional)',{type:'email',max:180})}</div>${officeContext?.unavailable?'':'<button type="button" class="btn-secondary" data-current-office>Use current office details</button>'}</details>`)}
      ${step(1,'What rent and listing dates are agreed?',field('listing_price','Monthly rent ($)',{required:true,money:true})+field('lease_min_months','Minimum lease term (months)',{required:true,integer:true,max:4})+field('lease_max_months','Maximum lease term (months)',{required:true,integer:true,max:4})+field('term_start','Listing starts',{required:true,type:'date'})+field('term_end','Listing ends',{required:true,type:'date'}))}
      ${step(2,'What compensation has the landlord agreed to?',select('fee_scope','How is compensation allocated?')+fee('fee','How is the listing broker’s compensation calculated?')+
        condition('cobroker',select('cobroker_basis','How is the cooperating broker’s share calculated?')+field('cobroker_amount','Cooperating broker’s agreed amount',{required:true,money:true}))+
        fee('renewal','What compensation applies to a renewal or extension?')+fee('sale_fee','What compensation applies if the tenant purchases the property?')+
        '<p class="hof-agreement-wide hof-listing-note">Compensation is negotiable. No rate is preselected. Enter only the terms agreed with the landlord.</p>'+
        `<details class="hof-agreement-wide"><summary>Reimbursable expenses and protection period</summary><div class="hof-agreement-grid">${area('reimbursable_expenses','Agreed reimbursable expenses (optional)')}${field('protection_days','Protection period (days)',{integer:true,max:4})}${field('payment_county','County where compensation is paid')}</div></details>`)}
      ${step(3,'How should the property be marketed and prepared?',select('mls_filing','When should the listing be filed in the MLS?')+
        condition('delay',field('mls_delay_days','Delay (days)',{required:true,integer:true,max:4})+area('mls_delay_purpose','Purpose of the delay'))+
        condition('internet',select('internet_display','What may be displayed online?'))+select('keybox','May a keybox be used?')+field('scheduling_companies','Showing service or scheduling company (optional)',{wide:true})+
        select('intermediary','If the broker also represents a tenant, what does the landlord authorize?')+select('make_ready','May the broker arrange make-ready work?')+
        condition('make_ready',field('make_ready_limit','Authorized spending limit ($)',{required:true,money:true})+field('make_ready_service_fee','Agreed make-ready service fee or terms',{required:true,wide:true})))}
      ${step(4,'What property details and related documents apply?',select('hoa','Is owners’ association membership mandatory?')+
        `<label class="hof-agreement-wide">Was the home built before 1978?<select name="built_before_1978"><option value="unanswered">Not yet confirmed</option><option value="yes">Yes</option><option value="no">No</option></select></label>`+
        area('non_real_estate_items','Included non-real-estate items (optional)')+area('exclusions','Excluded items (optional)')+
        `<details class="hof-agreement-wide"><summary>Known conditions and additional terms</summary><div class="hof-agreement-grid">${area('financial_exceptions','Exceptions to financial representations (optional)')}${area('liens','Known liens or encumbrances (optional)')}${area('common_area_fees','Common-area fees (optional)')}${area('health_safety_conditions','Known health or safety conditions (optional)')}${area('special_provisions','Special provisions supplied by the parties or their attorney (optional)')}</div></details>
        <details class="hof-agreement-wide"><summary>Review related documents</summary><fieldset class="hof-listing-checks"><legend>Documents that apply</legend>${documentChoices.map(([value,label])=>`<label><input type="checkbox" name="addenda" value="${value}"> ${label}</label>`).join('')}</fieldset></details>`+
        area('other_documents','Other related documents (optional)')+'<p class="hof-agreement-wide hof-listing-note">Related documents are a checklist, not confirmation that they are attached. Confirm the home’s age before deciding whether a lease lead disclosure is needed.</p>')}
      ${step(5,'Would you like to record rental preferences?',`<label class="hof-agreement-wide hof-listing-preference-toggle"><input type="checkbox" name="include_rental_preferences"> Add the landlord’s lease preferences</label><p class="hof-agreement-wide hof-listing-note">Optional instructions for marketing the rental—not a lease or a tenant-screening decision. Leave unconfirmed terms unspecified.</p>`+
        condition('preferences',`<details class="hof-agreement-wide"><summary>Rent, deposit and late charges</summary><div class="hof-agreement-grid">${select('rent_due','When is rent due?',true)}${condition('rent_due_other',field('rent_due_other','Agreed rent due date',{required:true}))}${optionalAmount('security_deposit','Security deposit ($)')}${field('late_after_days','Late after (days)',{integer:true,max:4})}${select('initial_late_basis','Initial late charge basis',true)}${condition('initial_late_amount',optionalAmount('initial_late_amount','Initial late charge amount'))}${optionalAmount('daily_late_amount','Daily late charge ($)')}</div></details>
        <details class="hof-agreement-wide"><summary>Animals</summary><div class="hof-agreement-grid">${select('animals','What are the agreed animal terms?',true)}${condition('animals',area('animal_restrictions','Agreed animal terms')+optionalAmount('animal_deposit','Animal deposit ($)')+optionalAmount('animal_monthly_rent','Monthly animal rent ($)')+optionalAmount('animal_one_time_fee','One-time animal fee ($)'))}${optionalAmount('animal_violation_initial','Initial unauthorized-animal charge ($)')}${optionalAmount('animal_violation_daily','Daily unauthorized-animal charge ($)')}</div></details><p class="hof-listing-note">Applicable assistance-animal protections remain in the source document.</p>
        <details class="hof-agreement-wide"><summary>Utilities, yard, pool and repairs</summary><div class="hof-agreement-grid">${area('utilities_exceptions','Utility payment exceptions')}${select('yard','Who maintains the yard?',true)}${condition('yard_contractor',field('yard_contractor','Named yard contractor',{required:true}))}${select('pool','Who maintains the pool?',true)}${condition('pool_contractor',field('pool_contractor','Named pool contractor',{required:true}))}${condition('pool_other',area('pool_other','Other pool maintenance terms'))}${field('repair_phone','Repair contact phone',{type:'tel'})}${area('unrepaired_items','Items the landlord will not repair')}${optionalAmount('liability_insurance','Required liability insurance ($)')}</div></details>
        <details class="hof-agreement-wide"><summary>Access, occupants’ guests and other agreed terms</summary><div class="hof-agreement-grid">${field('guests_days','Guest limit (days)',{integer:true,max:4})}${field('vehicle_count','Vehicle limit',{integer:true,max:4})}${optionalAmount('trip_charge','Trip charge ($)')}${field('keybox_last_days','Keybox permitted during final (days)',{integer:true,max:4})}${optionalAmount('keybox_withdrawal_fee','Keybox withdrawal fee ($)')}${field('inventory_days','Inventory submission period (days)',{integer:true,max:4})}${select('tenant_replacement_basis','Tenant-procured replacement tenant fee basis',true)}${condition('tenant_replacement_amount',optionalAmount('tenant_replacement_amount','Tenant-procured replacement fee amount'))}${select('landlord_replacement_basis','Landlord-procured replacement tenant fee basis',true)}${condition('landlord_replacement_amount',optionalAmount('landlord_replacement_amount','Landlord-procured replacement fee amount'))}${area('lease_special_provisions','Agreed lease special provisions')}${area('lease_other','Other agreed lease preferences')}</div></details>`))}
      ${step(6,'Review before preparing','<div id="txr1101Review" class="hof-agreement-wide"></div>'+select('signer_plan','Who will sign for the brokerage?')+'<p class="hof-agreement-wide hof-listing-note">Review the PDF and confirm recipients from Prepared documents. Nothing is sent from this interview.</p>')}
      <div id="txr1101Status" class="hof-iabs-status" role="status" aria-live="polite"></div><div class="hof-agreement-footer"><button type="button" class="btn-secondary" data-back>Back</button><button type="button" class="btn-primary" data-next>Continue</button><button type="submit" class="btn-primary" data-save>Prepare agreement</button></div></form>`;
  }
  function sync(form,get,{busy,uncertain}){
    const prefs=form.elements.namedItem('include_rental_preferences').checked;
    const conditions={cobroker:get('fee_scope')==='with_other_broker',delay:get('mls_filing')==='delayed',
      internet:Boolean(get('mls_filing'))&&get('mls_filing')!=='none',make_ready:Boolean(get('make_ready'))&&get('make_ready')!=='not_authorized',preferences:prefs,
      rent_due_other:prefs&&get('rent_due')==='other',animals:prefs&&get('animals')==='permitted',yard_contractor:prefs&&get('yard')==='named_contractor',
      pool_contractor:prefs&&get('pool')==='named_contractor',pool_other:prefs&&get('pool')==='other'};
    for(const prefix of ['fee','renewal','sale_fee']){conditions[prefix+'_amount']=Boolean(get(prefix+'_basis'))&&get(prefix+'_basis')!=='other';conditions[prefix+'_other']=get(prefix+'_basis')==='other';}
    for(const prefix of ['initial_late','tenant_replacement','landlord_replacement'])conditions[prefix+'_amount']=prefs&&Boolean(get(prefix+'_basis'))&&get(prefix+'_basis')!=='unspecified';
    for(const panel of form.querySelectorAll('[data-condition]')){
      const visible=Boolean(conditions[panel.dataset.condition]);panel.hidden=!visible;panel.style.display=visible?'':'none';
    }
    // Evaluate ancestors as well, so a nested preference cannot re-enable itself.
    for(const control of form.querySelectorAll('input,select,textarea'))control.disabled=busy||uncertain||Boolean(control.closest('[data-condition][hidden]'));
    form.querySelector('[name="addenda"][value="B"]').checked=true;
    const lead=form.querySelector('[name="addenda"][value="C"]');if(get('built_before_1978')!=='no')lead.checked=true;
    for(const name of ['mls_delay_purpose','fee_other','renewal_other','sale_fee_other','pool_other','initial_late_amount','tenant_replacement_amount','landlord_replacement_amount']){
      const control=form.elements.namedItem(name);control.required=!control.disabled;
    }
  }
  function review(payload,officeIdentity){
    const a=payload.agreementData,label=key=>(choices[key]||[]).find(([value])=>value===a[key])?.[1]||'Not selected';
    const fee=prefix=>a[prefix+'_basis']==='other'?a[prefix+'_other']:`${a[prefix+'_amount']}% · ${label(prefix+'_basis')}`;
    const date=value=>/^\d{4}-\d{2}-\d{2}$/.test(value)?new Date(value+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):value;
    const rows=[['Property',a.property_address],['Landlords',payload.clientNames.join(' · ')],['Monthly rent',Number(a.listing_price).toLocaleString('en-US',{style:'currency',currency:'USD'})],
      ['Lease term',`${a.lease_min_months}–${a.lease_max_months} months`],['Listing dates',`${date(a.term_start)} to ${date(a.term_end)}`],['Listing broker compensation',fee('fee')],
      ['Cooperating broker',a.fee_scope==='broker_only'?'Listing broker only':`${a.cobroker_amount}${a.cobroker_basis==='flat'?' dollars':'%'} · ${label('cobroker_basis')}`],
      ['Renewal compensation',fee('renewal')],['Tenant purchase compensation',fee('sale_fee')],['MLS filing',label('mls_filing')],['Make-ready authority',label('make_ready')],
      ['Brokerage',officeIdentity||'Check in the completed PDF'],['Rental preferences',a.include_rental_preferences?'Included as landlord instructions':'Not specified']];
    return `<dl>${rows.map(([key,value])=>`<div><dt>${key}</dt><dd>${escape(value)}</dd></div>`).join('')}</dl><p><strong>Related-document checklist:</strong> ${escape(a.addenda.map(code=>documentChoices.find(([value])=>value===code)?.[1]).filter(Boolean).join(' · ')||'None selected')}</p><p class="hof-listing-note">The checklist identifies related documents; it does not confirm attachments. Review the completed PDF and actual package contents before sending.</p>`;
  }
  const model={collect,prefill,validateTerms,validateStep:validateTerms,markup,sync,review,textLimits,preferenceTextLimits,preferenceChoices,preferenceIntegers,preferenceAmounts,choices,documentChoices,stepCount:7};
  if(typeof module!=='undefined'&&module.exports)module.exports=model;
  root.hofLeaseListingInterview=model;
})(typeof window!=='undefined'?window:{});
