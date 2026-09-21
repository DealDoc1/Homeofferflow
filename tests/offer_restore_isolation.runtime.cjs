const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const assert = require('node:assert/strict');
const {test} = require('node:test');
const root = path.join(__dirname, '..');
const html = process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git', ['show', process.env.HOF_TEST_SOURCE_REF + ':index.html'], {cwd:root, encoding:'utf8', maxBuffer:8*1024*1024})
  : fs.readFileSync(path.join(root, 'index.html'), 'utf8');
function source(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert.ok(a >= 0 && b > a, start);
  return html.slice(a,b);
}
function setup(offer = {id:'next', role:'agent', status:'Draft', offer_data:{}}) {
  const elements = new Map(), controls = [], cards = [], calls = [], recommendations=[];
  const wizardStart = html.indexOf('id="wizardOverlay"');
  const wizardEnd = html.indexOf('<script>', wizardStart);
  function node(id='') {
    const classes=new Set();
    return {id,value:'',checked:false,type:'text',style:{},dataset:{},
      classList:{add:k=>classes.add(k), remove:k=>classes.delete(k), contains:k=>classes.has(k), toggle:(k,on)=>on?classes.add(k):classes.delete(k)},
      setAttribute(){},removeAttribute(){},closest(){return this.card || null;}};
  }
  for (const match of html.matchAll(/<(input|textarea|select)\b([^>]*)>/g)) {
    const attrs=Object.fromEntries([...match[2].matchAll(/([\w-]+)="([^"]*)"/g)].map(m=>[m[1],m[2]]));
    if (!attrs.id && !attrs.name) continue;
    const el=Object.assign(node(attrs.id),attrs,{style:{cssText:attrs.style||''}});
    el.inWizard=match.index>wizardStart && match.index<wizardEnd;
    if (attrs.type === 'radio') {el.card=node(); cards.push(el.card);}
    controls.push(el);
    if(attrs.id) elements.set(attrs.id,el);
  }
  const get=id=>{if(!elements.has(id))elements.set(id,node(id)); return elements.get(id);};
  function all(selector) {
    if(selector==='input, textarea, select')return controls;
    if(selector==='.radio-card')return cards;
    if(selector==='input[type="radio"]:checked'||selector==='#wizardOverlay input[type="radio"]:checked')return controls.filter(el=>el.type==='radio'&&el.checked&&(!selector.startsWith('#wizardOverlay')||el.inWizard));
    if(selector==='#wizardOverlay input, #wizardOverlay textarea, #wizardOverlay select') return controls.filter(el=>el.inWizard);
    if(selector==='#wizardOverlay .radio-card') return controls.filter(el=>el.inWizard&&el.card).map(el=>el.card);
    if(selector==='#wizardOverlay .smart-recommendation')return recommendations;
    const name=selector.match(/\[name="([^"]+)"\]/)?.[1];
    if(name) {
      const value=selector.match(/\[value="([^"]+)"\]/)?.[1];
      return controls.filter(el=>el.name===name && (!selector.startsWith('#wizardOverlay')||el.inWizard) && (value===undefined || el.value===value) && (!selector.includes(':checked')||el.checked));
    }
    return [];
  }
  const ctx=vm.createContext({
    state:{data:{userType:'agent',buyer1:'Previous Client',buyerEmail:'previous@example.test',repairsText:'Previous repairs',_hofOfferId:'previous'},selectedPlan:'old',selectedPrice:99},
    hofAuth:{role:'agent',session:{user:{id:'owner',email:'account@example.test'}},accountProfile:{}},
    document:{getElementById:get,querySelectorAll:all,querySelector:s=>all(s)[0]||null},
    getVal:id=>String(get(id).value||'').trim(),getRadio:name=>all('input[name="'+name+'"]:checked')[0]?.value||'',
    updateParagraph4LeaseVisibility(){},toggleSellerTemporaryLeaseFields(){},updateHydrostaticVisibility(){},updateMineralVisibility(){},updateEnvironmentalVisibility(){},updateSurveyExistingDetails(){},
    restoreConditionalSections:()=>calls.push('conditions'),syncAgentQuickFields(){},
    getOfferById:async()=>offer,resetUploadedDisclosureDraftForOffer:data=>calls.push(['attachments',data]),
    setAudience:role=>{ctx.state.data.userType=role;calls.push(['audience',ctx.__hofRestoringDraft]);},
    closeAccountDashboard(){},renderUploadedDisclosureResumeNotice(){},
    openWizard:()=>{calls.push(['opened',get('buyer1First').value]);ctx.applyProfileDefaultsToWizard(false);},
    logOfferEvent:async()=>{},updateSaveStatus:message=>calls.push(['status',message]),
    __hofRestoringDraft:false,__hofCloudDraftSaveNeedsCopy:false,
    setTimeout:fn=>{calls.push('deferred');fn();},
    window:{announceWorkspaceStatus:message=>{throw new Error(message);},hofCustomerActionError:error=>error.message},
    console,
  });
  vm.runInContext(source('  function cleanOfferDraftData(', '  async function saveOfferDraftToSupabase('),ctx);
  vm.runInContext(source('  function setInputIfEmpty(', '  function resetWizardForFreshOffer('),ctx);
  vm.runInContext(source('  function setRadioValue(', '  function updateSurveyExistingDetails('),ctx);
  vm.runInContext(source('  function updateHoaFollowUpVisibility()', "  document.addEventListener('DOMContentLoaded'"),ctx);
  vm.runInContext(source('  function assumptionAnswerKeys(', '  function environmentalInterviewData(')
    +source('  function hydrostaticInterviewData(', '  function hydrostaticInterviewIssues('),ctx);
  const clearStart=html.includes('  function clearOfferInterviewFields(')?'  function clearOfferInterviewFields(':'  function applyOfferDataToFields(';
  vm.runInContext(source(clearStart,'  async function resumeOffer('),ctx);
  vm.runInContext(source('  async function resumeOffer(', '  async function duplicateOffer('),ctx);
  vm.runInContext(source('  async function reuseOfferTerms(', '  async function deleteOffer('),ctx);
  return {ctx,get,all,calls,recommendations,controls};
}

test('hydrating a sparse offer clears previous client, property, radios and conditional values',()=>{
  const {ctx:c,get,all}=setup();
  for(const id of ['buyer1First','buyer1Last','buyer2','buyerEmail','buyer2Email','propAddress','repairsText','listingNotes','appraisalPartialValue','salePropertyAddr','agentNameQuick','paymentEmail']) get(id).value='Previous value';
  c.setRadioValue('financing','fha'); c.setRadioValue('appraisalAddendum','partial'); c.setRadioValue('saleContingency','yes');
  get('termsAccepted').checked=true; get('oneTimePacketAck').checked=true;
  get('selectedPlanDisplay').style.display='block'; get('payBtn').disabled=false;
  get('propAddress').dataset.hofAddressSelected='true'; get('offerPrice')._userEdited=true;
  const outside=get('accountProfileEmail'); outside.value='Keep account profile';
  c.applyOfferDataToFields({buyer1:'New Client',buyerEmail:'',price:0});
  assert.equal(get('buyer1First').value,'New'); assert.equal(get('buyer1Last').value,'Client');
  for(const id of ['buyer2','buyerEmail','buyer2Email','propAddress','repairsText','listingNotes','appraisalPartialValue','salePropertyAddr','agentNameQuick','paymentEmail']) assert.equal(get(id).value,'',id);
  for(const name of ['financing','appraisalAddendum','saleContingency']) assert.equal(c.getRadio(name),'',name);
  assert.equal(get('offerPrice').value,'0'); assert.equal(get('termsAccepted').checked,true);
  assert.equal(get('oneTimePacketAck').checked,false); assert.equal(outside.value,'Keep account profile');
  assert.equal(get('propAddress').dataset.hofAddressSelected,undefined);
  assert.equal(get('selectedPlanDisplay').style.display,'none'); assert.equal(get('payBtn').disabled,true);
});

test('stored conditional answers and zero amounts restore instead of being lost',()=>{
  const {ctx:c,get}=setup();
  const data={buyer1:'Buyer One',buyer2:'Buyer Two',buyer2Email:'two@example.test',financing:'conventional',
    appraisalAddendum:'partial',appraisalPartialValue:450000,appraisalTerminateDays:5,appraisalTerminateValue:455000,
    listPrice:500000,originalListPrice:520000,daysOnMarket:45,priceReductionCount:1,listingStatus:'active',listingNotes:'Current notes',
    hoaSubdivisionInfo:'buyer',hoaTitleCost:'seller',surveyIfRejectedPaidBy:'buyer',mud:'no',brokerFeeAmount:0,brokerFeePercent:'2.5',
    agentName:'Saved Agent',agentEmail:'saved-agent@example.test',seenProperty:'yes'};
  c.applyOfferDataToFields(data);
  for(const key of ['appraisalPartialValue','appraisalTerminateDays','appraisalTerminateValue','listPrice','originalListPrice','daysOnMarket','priceReductionCount','listingStatus','listingNotes','hoaSubdivisionInfo','hoaTitleCost','surveyIfRejectedPaidBy','brokerFeeAmount','brokerFeePercent']) assert.equal(get(key).value,String(data[key]),key);
  assert.equal(get('mudDistrict').value,'no'); assert.equal(c.getRadio('appraisalAddendum'),'partial');
  assert.equal(get('agentNameQuick').value,'Saved Agent'); assert.equal(get('agentEmailQuick').value,'saved-agent@example.test');
  assert.equal(get('appraisalPartialValue')._userEdited,true);
});

test('account defaults fill blanks without overwriting an existing offer election',()=>{
  const {ctx:c,get}=setup();
  c.hofAuth.accountProfile={default_title_payer:'seller',default_survey_choice:'sellerExisting',preferred_title_company:'Preferred Title'};
  c.applyOfferDataToFields({titlePayer:'buyer',survey:'buyerNew',titleCompany:'Saved Title'});
  c.applyProfileDefaultsToWizard(false);
  assert.equal(c.getRadio('titlePayer'),'buyer'); assert.equal(c.getRadio('survey'),'buyerNew'); assert.equal(get('titleCompany').value,'Saved Title');
  c.applyOfferDataToFields({}); c.applyProfileDefaultsToWizard(false);
  assert.equal(c.getRadio('titlePayer'),'seller'); assert.equal(get('titleCompany').value,'Preferred Title');
  c.hofAuth.role='investor'; c.state.data.userType='investor'; c.hofAuth.accountProfile={default_offer_type:'cash'};
  c.setRadioValue('financing','conventional'); c.applyProfileDefaultsToWizard(false);
  assert.equal(c.getRadio('financing'),'conventional');
});

test('resume replaces transaction state rather than merging another offer into it',async()=>{
  const {ctx:c,get,calls}=setup({id:'next',role:'agent',status:'Draft',buyer_email:'old-row@example.test',offer_data:{buyer1:'Next Client',buyerEmail:''}});
  get('repairsText').value='Previous repair';
  await c.resumeOffer('next');
  assert.equal(c.state.data._hofOfferId,'next'); assert.equal(c.state.data.buyerEmail,'');
  assert.equal(c.state.data.repairsText,undefined); assert.equal(get('repairsText').value,'');
  assert.equal(calls.includes('deferred'),false); assert.equal(c.__hofRestoringDraft,false);
  assert.equal(c.state.selectedPlan,null); assert.ok(calls.some(v=>Array.isArray(v)&&v[0]==='audience'&&v[1]===true));
});

test('reuse terms clears prior DOM contacts and restores only allowed deal choices',async()=>{
  const {ctx:c,get}=setup({id:'source',role:'agent',offer_data:{financing:'cash',titlePayer:'buyer',buyer1:'Source Client',buyerEmail:'source@example.test',address:'Source property',price:999000}});
  for(const id of ['buyer1First','buyerEmail','propAddress','offerPrice','paymentEmail']) get(id).value='Old screen';
  await c.reuseOfferTerms('source');
  for(const id of ['buyer1First','buyerEmail','propAddress','offerPrice','paymentEmail']) assert.equal(get(id).value,'',id);
  assert.equal(c.state.data.buyer1,undefined); assert.equal(c.state.data._hofOfferId,null);
  assert.equal(c.getRadio('financing'),'cash'); assert.equal(c.getRadio('titlePayer'),'buyer');
});

function enableConditionalRestore(x) {
  x.ctx.updateUnrepresentedConcessionTip=()=>{};
  x.ctx.updateAppraisalAddendumVisibility=()=>{};
  vm.runInContext(source('  function restoreConditionalSections()', '  function clearSavedDraft()'),x.ctx);
}
const visibilityCases=[
  ['nonRealtyItems','yes','nonRealtyDetails','block'],
  ['nonRealtyItems','no','nonRealtyDetails','none'],
  ['nonRealtyItems','','nonRealtyDetails','none'],
  ['leadBuiltBefore1978','yes','leadDisclosureBox','block'],
  ['leadBuiltBefore1978','unknown','leadDisclosureBox','block'],
  ['leadBuiltBefore1978','no','leadDisclosureBox','none'],
  ['leadBuiltBefore1978','','leadDisclosureBox','none'],
  ['brokerFeeType','amount','brokerFeeAmountField','block'],
  ['brokerFeeType','amount','brokerFeePercentField','none'],
  ['brokerFeeType','percent','brokerFeeAmountField','none'],
  ['brokerFeeType','percent','brokerFeePercentField','block'],
  ['brokerFeeType','none','brokerFeeAmountField','none'],
  ['brokerFeeType','none','brokerFeePercentField','none'],
  ['brokerFeeType','','brokerFeeAmountField','none'],
  ['brokerFeeType','','brokerFeePercentField','none'],
];
for(const [group,value,id,expected] of visibilityCases) {
  test(`restoring ${group}=${JSON.stringify(value)} makes ${id} ${expected}`,()=>{
    const x=setup();enableConditionalRestore(x);
    x.get(id).style.display=expected==='none'?'block':'none';
    const data={[group]:value,nonRealtyAmount:0,nonRealtyDescription:'Kitchen refrigerator',brokerFeeAmount:4500,brokerFeePercent:'2.5',leadDisclosureStatus:'received'};
    x.ctx.applyOfferDataToFields(data);x.ctx.restoreConditionalSections();
    assert.equal(x.get(id).style.display,expected);
    assert.equal(x.get('nonRealtyAmount').value,'0');assert.equal(x.get('nonRealtyDescription').value,'Kitchen refrigerator');
    assert.equal(x.get('brokerFeeAmount').value,'4500');assert.equal(x.get('brokerFeePercent').value,'2.5');
    assert.equal(x.ctx.getRadio('leadDisclosureStatus'),'received');
  });
}
for(const role of ['homebuyer','investor','agent']) {
  test(`${role} resume opens saved follow-up questions and hides the preceding offer's sections`,async()=>{
    const offer={id:'saved',role,status:'Draft',offer_data:{nonRealtyItems:'yes',leadBuiltBefore1978:'yes',leadDisclosureStatus:'request',brokerFeeType:'amount',brokerFeeAmount:8500,hasBuyerAgent:'yes'}};
    const x=setup(offer);enableConditionalRestore(x);
    for(const id of ['nonRealtyDetails','leadDisclosureBox','brokerFeeAmountField','agentSoftNote'])x.get(id).style.display='none';
    x.get('brokerFeePercentField').style.display='block';
    await x.ctx.resumeOffer('saved');
    for(const id of ['nonRealtyDetails','leadDisclosureBox','brokerFeeAmountField','agentSoftNote'])assert.equal(x.get(id).style.display,'block',id);
    assert.equal(x.get('brokerFeePercentField').style.display,'none');
    offer.offer_data={nonRealtyItems:'no',leadBuiltBefore1978:'no',brokerFeeType:'none',hasBuyerAgent:'no'};
    await x.ctx.resumeOffer('saved');
    for(const id of ['nonRealtyDetails','leadDisclosureBox','brokerFeeAmountField','brokerFeePercentField'])assert.equal(x.get(id).style.display,'none',id);
    assert.equal(x.get('agentSoftNote').style.display,role==='agent'?'block':'none');
  });
}
test('unrelated existing follow-up sections still restore from saved answers',()=>{
  const x=setup();enableConditionalRestore(x);x.ctx.state.data.userType='homebuyer';
  x.ctx.applyOfferDataToFields({financing:'conventional',hoa:'unknown',saleContingency:'yes',backupOffer:'yes',asIs:'repairs',sellerDisclosure:'notReceived',wantsConcessions:'yes',homeWarranty:'yes',buyer2:'Second Buyer'});
  x.ctx.restoreConditionalSections();
  for(const id of ['hoaDetails','saleContingencyDetails','backupDetails','repairsField','discDaysField','concessionsField','homeWarrantyField'])assert.equal(x.get(id).style.display,'block',id);
  assert.equal(x.get('financingDetails').style.display,'flex');assert.equal(x.get('buyer2EmailField').style.display,'flex');
  x.ctx.applyOfferDataToFields({});x.ctx.restoreConditionalSections();
  for(const id of ['hoaDetails','saleContingencyDetails','backupDetails','repairsField','discDaysField','concessionsField','homeWarrantyField','financingDetails','buyer2EmailField'])assert.equal(x.get(id).style.display,'none',id);
});

const reusablePreferences={financing:'conventional',loanYears:'30',interestRateCap:'6.5',interestFirstYears:'5',originationCap:'1',buyerApprovalDays:'21',titlePayer:'buyer',titleAmendment:'ii_buyer',survey:'buyerNew',homeWarranty:'yes'};
const freshQuestions={hoa:'yes',sellerDisclosure:'received',leadBuiltBefore1978:'yes',leadDisclosureStatus:'received',saleContingency:'yes',backupOffer:'yes',appraisalAddendum:'partial',asIs:'repairs'};
for(const role of ['agent','investor','homebuyer']) {
  test(`${role} terms reuse asks property and contingency questions again without changing the source`,async()=>{
    const sourceData={...reusablePreferences,...freshQuestions,buyer1:'Source Buyer',buyerEmail:'source@example.test',address:'Source property',repairsText:'Remove source property shed',hoaName:'Source HOA',appraisalPartialValue:450000,closingDate:'2026-10-01',uploadedDocNames:['source-disclosure.pdf'],includeAgentIabs:true};
    const offer={id:'source',role,offer_data:sourceData};
    const snapshot=JSON.stringify(offer);const x=setup(offer);enableConditionalRestore(x);
    x.ctx.applyOfferDataToFields(sourceData);x.ctx.restoreConditionalSections();
    await x.ctx.reuseOfferTerms('source');
    for(const [key,value] of Object.entries(reusablePreferences))assert.equal(x.ctx.state.data[key],value,key);
    for(const key of Object.keys(freshQuestions)) {
      assert.equal(x.ctx.state.data[key],undefined,key);assert.equal(x.ctx.getRadio(key),'',key);
    }
    for(const id of ['buyer1First','buyerEmail','propAddress','repairsText','hoaName','appraisalPartialValue','closingDate'])assert.equal(x.get(id).value,'',id);
    for(const id of ['hoaDetails','leadDisclosureBox','saleContingencyDetails','backupDetails','repairsField'])assert.equal(x.get(id).style.display,'none',id);
    assert.equal(x.ctx.state.data.uploadedDocNames,undefined);assert.equal(x.ctx.state.data.includeAgentIabs,undefined);
    assert.equal(x.ctx.state.data._hofOfferId,null);assert.equal(JSON.stringify(offer),snapshot);
    assert.ok(x.calls.some(v=>Array.isArray(v)&&v[0]==='attachments'&&Object.keys(v[1]).length===0));
  });
  test(`${role} resume preserves source-specific answers rather than applying the reuse filter`,async()=>{
    const x=setup({id:'source',role,offer_data:{...freshQuestions,...reusablePreferences}});enableConditionalRestore(x);
    await x.ctx.resumeOffer('source');
    for(const [key,value] of Object.entries(freshQuestions))assert.equal(x.ctx.state.data[key],value,key);
    assert.equal(x.ctx.state.data._hofOfferId,'source');
  });
}

function enableFreshReset(x) {
  const removed=[];
  x.ctx.localStorage={removeItem:key=>removed.push(['local',key])};
  x.ctx.sessionStorage={removeItem:key=>removed.push(['session',key])};
  vm.runInContext(source('  function resetWizardForFreshOffer(', '  function startAccountOffer()'),x.ctx);
  vm.runInContext(source('  function numFromEl(', '  function showFieldRecommendation('),x.ctx);
  vm.runInContext(source('  function calculatePriceTermsOnly()', '  function wireSmartCalculations()'),x.ctx);
  x.ctx.showFieldRecommendation=()=>{};
  enableConditionalRestore(x);
  return removed;
}
const calculatedFields=['earnestMoney','optionFee','optionDays','downPayment','loanAmount','loanYears','interestRateCap','interestFirstYears','originationCap','buyerApprovalDays'];
for(const role of ['agent','investor','homebuyer']) {
  test(`${role} fresh offer clears prior edit flags so price and financing suggestions work again`,()=>{
    const x=setup();enableFreshReset(x);
    for(const id of calculatedFields){x.get(id).value='999';x.get(id)._userEdited=true;}
    x.ctx.resetWizardForFreshOffer(role);
    for(const id of calculatedFields){assert.equal(x.get(id).value,'',id);assert.equal(x.get(id)._userEdited,undefined,id);}
    x.get('offerPrice').value='500000';x.ctx.setRadioValue('financing','conventional');
    x.ctx.calculatePriceTermsOnly();x.ctx.calculateFinancingDefaults();
    const expected={earnestMoney:5000,optionFee:250,optionDays:7,downPayment:50000,loanAmount:450000,loanYears:30,interestRateCap:7,interestFirstYears:30,originationCap:1,buyerApprovalDays:21};
    for(const [id,value] of Object.entries(expected))assert.equal(Number(x.get(id).value),value,id);
  });
}
for(const checked of [true,false]) {
  test(`fresh reset preserves terms acceptance=${checked} and account preferences but clears transaction state`,()=>{
    const x=setup(),removed=enableFreshReset(x);
    const profile={default_option_fee:0,default_option_days:0,default_earnest_amount:10000,preferred_title_company:'My Title Office'};
    x.ctx.hofAuth.accountProfile=profile;const session=x.ctx.hofAuth.session;
    x.get('termsAccepted').checked=checked;x.get('oneTimePacketAck').checked=true;
    x.ctx.__hofCloudDraftSaveNeedsCopy=true;x.ctx.window.__hofSubscriptionPacketGenerated=true;
    x.ctx.resetWizardForFreshOffer('agent');
    assert.equal(x.ctx.hofAuth.accountProfile,profile);assert.equal(x.ctx.hofAuth.session,session);
    assert.equal(x.get('termsAccepted').checked,checked);assert.equal(x.ctx.state.termsOK,checked);
    assert.equal(x.get('oneTimePacketAck').checked,false);assert.equal(x.ctx.__hofCloudDraftSaveNeedsCopy,false);
    assert.equal(x.ctx.window.__hofSubscriptionPacketGenerated,false);assert.equal(x.ctx.state.data._hofOfferId,undefined);
    assert.equal(x.ctx.state.data.buyer1,undefined);assert.equal(x.ctx.state.selectedPlan,null);assert.equal(x.ctx.state.selectedPrice,0);
    assert.equal(x.get('payBtn').disabled,true);assert.equal(x.get('selectedPlanDisplay').style.display,'none');
    assert.equal(removed.some(([,key])=>key.includes('profile')),false);
    x.ctx.applyProfileDefaultsToWizard(false);x.get('offerPrice').value='500000';x.ctx.calculatePriceTermsOnly();
    assert.equal(Number(x.get('optionFee').value),0);assert.equal(Number(x.get('optionDays').value),0);
    assert.equal(Number(x.get('earnestMoney').value),10000);assert.equal(x.get('titleCompany').value,'My Title Office');
  });
}
for(const action of ['resetWizardForFreshOffer','applyOfferDataToFields']) {
  test(`${action} clears stale address, validation and recommendation state`,()=>{
    const x=setup();enableFreshReset(x);
    x.get('propAddress').dataset.hofAddressSelected='true';x.get('propAddress').dataset.validationInvalid='true';
    x.get('propAddress').style.borderColor='red';let removedAria=false;
    x.get('propAddress').removeAttribute=name=>{if(name==='aria-invalid')removedAria=true;};
    const hint={removed:false,remove(){this.removed=true;}};x.recommendations.push(hint);
    x.ctx[action](action==='resetWizardForFreshOffer'?'homebuyer':{});
    assert.equal(x.get('propAddress').dataset.hofAddressSelected,undefined);
    assert.equal(x.get('propAddress').dataset.validationInvalid,undefined);
    assert.equal(x.get('propAddress').style.borderColor,'');assert.equal(removedAria,true);assert.equal(hint.removed,true);
  });
}

function enableLocalDraft(x,draft,owner='owner') {
  enableFreshReset(x);
  const c=x.ctx,store=new Map([['draft',JSON.stringify(draft)],['owner',owner]]),timers=[];
  Object.assign(c,{HOF_STORAGE_KEY:'draft',HOF_STORAGE_OWNER_KEY:'owner',HOF_WIZARD_ORDER_VERSION:2,CSS:{escape:v=>v},
    localStorage:{getItem:key=>store.get(key)||null},setTimeout:fn=>timers.push(fn),
    renderUploadedDocsList(){},resetUploadedDisclosureAcknowledgement(){x.get('uploadedDisclosureAck').checked=false;}});
  c.document.body={style:{}};
  vm.runInContext(source('  const STEP_CONFIG =', '  const LEGAL_POLICY_VERSION'),c);
  vm.runInContext(source('  function collectAllData()', '  function selectPlan('),c);
  vm.runInContext(source('  function checkedValues(', '  function updateParagraph4LeaseVisibility('),c);
  vm.runInContext(source('  function uploadedDisclosureDraftNames()', '  function removeUploadedDisclosure('),c);
  vm.runInContext(source('  function getDraftSnapshot()', '  function saveDraftNow()'),c);
  vm.runInContext(source('  function restoredWizardStep(', '  function updateHoaFollowUpVisibility()'),c);
  c.showStep=n=>{c.state.step=n;x.calls.push(['step',n,c.state.data.userType,c.__hofRestoringDraft]);c.calculatePriceTermsOnly();c.calculateFinancingDefaults();};
  vm.runInContext(source('  function escapeAttr(', '  function withTimeout('),c);
  c.selectPlan=(plan,price)=>{c.state.selectedPlan=plan;c.state.selectedPrice=price;};
  return {store,timers};
}
const startupDraft={userType:'agent',wizardOrderVersion:2,step:3,fields:{buyer1First:'Saved',buyer1Last:'Client',propAddress:'Saved property'},radios:{}};
function enableCheckoutRecovery(x, offer) {
  const local=enableLocalDraft(x,{...startupDraft,userType:'homebuyer'},'');
  const c=x.ctx;
  c.URLSearchParams=URLSearchParams;
  c.window.location={search:'?payment=cancelled',origin:'https://www.homeofferflow.test',pathname:'/'};
  c.window.history={replaceState:()=>x.calls.push('clean-url')};
  c.sessionStorage={getItem:()=>offer===null?null:JSON.stringify(offer)};
  c.trackEvent=()=>{};c.recordHomebuyerCheckoutEvent=()=>{};
  c.setUploadedDisclosureStatus=message=>x.calls.push(['upload-status',message]);
  c.saveDraft=()=>{};c.renderReview=()=>{};
  c.getCurrentSteps=()=>['step0','step1','step2','step3','step5','step6','step7','step8','step9'];
  x.get('uploadedDisclosureDocs').focus=()=>x.calls.push('focus-attachments');
  if(html.includes('  function restoreBuyerCheckoutSnapshot('))
    vm.runInContext(source('  function restoreBuyerCheckoutSnapshot(', '  function checkPaymentReturn()'),c);
  vm.runInContext(source('  function checkPaymentReturn()',"  window.addEventListener('load', () => { try { if (typeof checkSubscriptionReturn"),c);
  vm.runInContext(source('  function removeUploadedDisclosure(', '  function renderUploadedDocsList()'),c);
  return local;
}
const cancelledBuyer={userType:'homebuyer',selectedPlan:'self',selectedPrice:99,buyer1:'Current Buyer',
  buyerEmail:'buyer@example.test',_paymentEmail:'receipt@example.test',address:'Current property',price:450000,
  financing:'cash',earnest:0,optionFee:0,optionDays:0,repairsText:'Current repairs',_hofOfferId:'do-not-reuse',
  uploadedDocNames:['survey.pdf'],uploadedDisclosureDocs:[{name:'survey.pdf',type:'survey',base64:'JVBERg==',size:4}]};
test('cancelled checkout hydrates the actual interview fields and current attachments',()=>{
  const x=setup();enableCheckoutRecovery(x,cancelledBuyer);const c=x.ctx;
  x.get('propAddress').value='Wrong previous property';
  c.window.hofUploadedDisclosureDocs=[{name:'old-client.pdf',base64:'old'}];
  c.checkPaymentReturn();
  assert.equal(x.get('propAddress').value,'Current property');
  assert.equal(x.get('buyer1First').value,'Current');assert.equal(x.get('buyer1Last').value,'Buyer');
  assert.equal(x.get('offerPrice').value,'450000');assert.equal(x.get('optionFee').value,'0');
  assert.equal(x.get('repairsText').value,'Current repairs');assert.equal(x.get('paymentEmail').value,'receipt@example.test');
  assert.equal(c.state.data._hofOfferId,null);assert.equal(c.state.step,8);
  assert.equal(c.window.hofUploadedDisclosureDocs.length,1);assert.equal(c.window.hofUploadedDisclosureDocs[0].name,'survey.pdf');
  assert.equal(c.window.hofUploadedDisclosureDocs[0].base64,'JVBERg==');
  assert.equal(x.get('uploadedDisclosureAck').checked,false);
  assert.equal(c.__hofRestoringDraft,false);assert.equal(c.window.__hofAutomaticDraftRestoreSettled,true);
});
test('cancel snapshot rejects unrelated agent or malformed work before mutation',()=>{
  const x=setup();enableCheckoutRecovery(x,cancelledBuyer);const original=x.ctx.state.data;
  for(const value of [null,[],{}, {...cancelledBuyer,userType:'agent'}, {...cancelledBuyer,selectedPlan:'monthly'}])
    assert.equal(x.ctx.restoreBuyerCheckoutSnapshot(value),false);
  assert.equal(x.ctx.state.data,original);
});
test('cancel fallback restores homebuyer fields but never an agent draft',()=>{
  const x=setup(),local=enableCheckoutRecovery(x,null);const c=x.ctx;
  c.checkPaymentReturn();assert.equal(x.get('propAddress').value,'Saved property');
  local.store.set('draft',JSON.stringify(startupDraft));
  const before=c.state.data;assert.equal(c.restoreDraft({expectedRole:'homebuyer'}),false);assert.equal(c.state.data,before);
});
test('compact quota fallback restores answers and explicitly identifies uncached files on cancellation',()=>{
  const x=setup();enableCheckoutRecovery(x,null);const c=x.ctx,cache=new Map();
  c.sessionStorage={setItem:(key,value)=>{if(value.length>2000)throw Error('QuotaExceededError');cache.set(key,value);},getItem:key=>cache.get(key)||null};
  vm.runInContext(source('  function cacheBuyerCheckoutSnapshot(', '  async function handlePayment()'),c);
  const packet={...cancelledBuyer,uploadedDisclosureDocs:[{...cancelledBuyer.uploadedDisclosureDocs[0],base64:'A'.repeat(16000)}]};
  assert.equal(c.cacheBuyerCheckoutSnapshot(packet),true);
  c.checkPaymentReturn();
  assert.equal(x.get('propAddress').value,'Current property');assert.equal(x.get('repairsText').value,'Current repairs');
  assert.equal(c.window.hofUploadedDisclosureDocs.length,0);
  assert.deepEqual(Array.from(c.missingUploadedDisclosureNames()),['survey.pdf']);
  assert.equal(c.validateUploadedDisclosureDocs(),false);
});
test('missing saved attachment stops sending and opens the upload step',()=>{
  const x=setup();enableCheckoutRecovery(x,cancelledBuyer);const c=x.ctx;
  c.state.data.uploadedDocNames=['survey.pdf'];c.window.hofUploadedDisclosureDocs=[];
  assert.equal(c.validateUploadedDisclosureDocs(),false);
  assert.equal(c.state.step,4);assert.ok(x.calls.includes('focus-attachments'));
});
test('removing one present upload does not silently remove a different missing one',()=>{
  const x=setup();enableCheckoutRecovery(x,cancelledBuyer);const c=x.ctx;
  c.state.data.uploadedDocNames=['survey.pdf','missing.pdf'];c.window.hofUploadedDisclosureDocs=[{name:'survey.pdf',base64:'data'}];
  c.removeUploadedDisclosure(0);
  assert.deepEqual(Array.from(c.missingUploadedDisclosureNames()),['missing.pdf']);
});
test('explicitly removing missing files preserves the uploads already present',()=>{
  const x=setup();enableCheckoutRecovery(x,cancelledBuyer);const c=x.ctx;
  c.state.data.uploadedDocNames=['survey.pdf','missing.pdf'];c.state.data.uploadedDisclosureDocs=[{name:'missing.pdf'}];
  c.window.hofUploadedDisclosureDocs=[{name:'survey.pdf',base64:'data',type:'survey'}];
  c.removeMissingUploadedDisclosures();
  assert.deepEqual(Array.from(c.state.data.uploadedDocNames),['survey.pdf']);
  assert.equal(c.window.hofUploadedDisclosureDocs.length,1);assert.equal(c.state.data.uploadedDisclosureDocs,undefined);
});
test('a partially re-uploaded set keeps remaining missing files visible',async()=>{
  const x=setup();enableCheckoutRecovery(x,cancelledBuyer);const c=x.ctx;
  c.state.data.uploadedDocNames=['survey.pdf','other.pdf'];c.window.hofUploadedDisclosureDocs=[];
  c.Uint8Array=Uint8Array;c.readFileAsBase64=async()=> 'JVBERg==';c.suggestedUploadedDisclosureType=()=> 'survey';
  vm.runInContext(source('  async function handleUploadedDisclosureDocs(', '  function controlledLaunchUnsupportedPaths('),c);
  await c.handleUploadedDisclosureDocs([{name:'survey.pdf',size:4,type:'application/pdf',slice:()=>({arrayBuffer:async()=>new Uint8Array([37,80,68,70]).buffer})}]);
  assert.deepEqual(Array.from(c.missingUploadedDisclosureNames()),['other.pdf']);
  assert.equal(c.validateUploadedDisclosureDocs(),false);
});
test('a restored draft cannot silently resubmit stale legacy attachment bytes',()=>{
  const x=setup();enableCheckoutRecovery(x,cancelledBuyer);const c=x.ctx;
  c.state.data={userType:'agent',uploadedDocs:[{name:'legacy.pdf',base64:'private-old-file'}]};
  c.resetUploadedDisclosureDraftForOffer(c.state.data);
  assert.equal(c.state.data.uploadedDocs,undefined);assert.equal(c.state.data.uploadedDisclosureDocs,undefined);
  assert.deepEqual(Array.from(c.state.data.uploadedDocNames),['legacy.pdf']);
  assert.equal(c.validateUploadedDisclosureDocs(),false);
});
test('automatic local restore runs once and cannot overwrite later answers',()=>{
  const x=setup();enableLocalDraft(x,startupDraft);
  assert.equal(x.ctx.restoreDraft({automatic:true}),true);
  const active=x.ctx.state.data;x.get('buyer1First').value='Latest';x.ctx.state.step=5;
  assert.equal(x.ctx.restoreDraft({automatic:true}),false);
  assert.equal(x.ctx.state.data,active);assert.equal(x.get('buyer1First').value,'Latest');assert.equal(x.ctx.state.step,5);
});
for(const action of ['fresh offer','cloud offer request','open wizard','input','change']) test(`automatic restore yields after ${action}`,()=>{
  const x=setup();enableLocalDraft(x,startupDraft);const c=x.ctx;
  if(action==='fresh offer')c.resetWizardForFreshOffer('homebuyer');
  else if(action==='cloud offer request')c.beginOfferOpenRequest();
  else if(action==='open wizard'){
    Object.assign(c,{trackEvent(){},applyAudienceWorkflow(){},updateProgress(){},applySmartDefaults(){},tryInitAutocomplete(){}});
    vm.runInContext(source('  function openWizard(', '  function closeWizard()'),c);
    c.openWizard(true);
  } else {
    const listeners={};c.document.addEventListener=(event,fn)=>listeners[event]=fn;
    Object.assign(c,{clearValidationFeedbackFor(){},sanitizeBuyerMailingAddressAutofill(){},scheduleDraftSave(){}});
    vm.runInContext(source('  function clearSavedDraft()',"  window.addEventListener('beforeunload'"),c);
    listeners[action]({target:{id:'buyer1First',closest:()=>({})}});
  }
  const active=c.state.data;c.state.step=5;x.get('buyer1First').value='Current';
  assert.equal(c.restoreDraft({automatic:true}),false);assert.equal(c.state.data,active);
  assert.equal(x.get('buyer1First').value,'Current');assert.equal(c.state.step,5);
});
for(const event of ['input','change'])test(`unrelated ${event} does not prevent initial draft restoration`,()=>{
  const x=setup();enableLocalDraft(x,startupDraft);const c=x.ctx,listeners={};
  c.document.addEventListener=(name,fn)=>listeners[name]=fn;
  vm.runInContext(source('  function clearSavedDraft()',"  window.addEventListener('beforeunload'"),c);
  listeners[event]({target:{closest:()=>null}});
  assert.equal(c.restoreDraft({automatic:true}),true);assert.equal(x.get('buyer1First').value,'Saved');
});
test('explicit resume remains available after automatic restore settles',()=>{
  const x=setup();enableLocalDraft(x,startupDraft);x.ctx.window.__hofAutomaticDraftRestoreSettled=true;
  assert.equal(x.ctx.restoreDraft(),true);assert.equal(x.get('buyer1First').value,'Saved');
});
test('a payment return cannot automatically reopen the saved pricing interview',()=>{
  const x=setup();enableLocalDraft(x,startupDraft);x.ctx.window.__hofPaymentReturn=true;const original=x.ctx.state.data;
  assert.equal(x.ctx.restoreDraft({automatic:true}),false);assert.equal(x.ctx.state.data,original);
});
test('an account sign-in handoff keeps an older local draft closed until explicitly resumed',()=>{
  const x=setup();enableLocalDraft(x,startupDraft);x.ctx.window.__hofAccountRouteAuthPending=true;const original=x.ctx.state.data;
  assert.equal(x.ctx.restoreDraft({automatic:true}),false);assert.equal(x.ctx.state.data,original);
  assert.notEqual(x.ctx.window.__hofAutomaticDraftRestoreSettled,true);
  assert.equal(x.ctx.restoreDraft(),true);assert.equal(x.get('buyer1First').value,'Saved');
});
test('an open secure sign-in screen prevents a stale wizard from appearing behind it',()=>{
  const x=setup();enableLocalDraft(x,startupDraft);x.get('authModal').classList.add('active');const original=x.ctx.state.data;
  assert.equal(x.ctx.restoreDraft({automatic:true}),false);assert.equal(x.ctx.state.data,original);
  assert.notEqual(x.ctx.window.__hofAutomaticDraftRestoreSettled,true);
});
test('an owner waiting for account resolution can still restore once it completes',()=>{
  const x=setup();enableLocalDraft(x,startupDraft);x.ctx.hofAuth.session=null;
  assert.equal(x.ctx.restoreDraft({automatic:true}),false);
  assert.notEqual(x.ctx.window.__hofAutomaticDraftRestoreSettled,true);
  x.ctx.hofAuth.session={user:{id:'owner'}};
  assert.equal(x.ctx.restoreDraft({automatic:true}),true);
});
test('missing or malformed draft does not consume the automatic restore opportunity',()=>{
  const x=setup();const {store}=enableLocalDraft(x,startupDraft);
  for(const raw of ['', '{broken', '[]']){
    store.set('draft',raw);assert.equal(x.ctx.restoreDraft({automatic:true}),false);
    assert.notEqual(x.ctx.window.__hofAutomaticDraftRestoreSettled,true);
  }
  store.set('draft',JSON.stringify(startupDraft));assert.equal(x.ctx.restoreDraft({automatic:true}),true);
});
test('the actual delayed load callback does not overwrite an explicitly opened offer',()=>{
  const x=setup();const {timers}=enableLocalDraft(x,startupDraft),c=x.ctx,listeners={};
  c.window.addEventListener=(event,fn)=>listeners[event]=fn;c.window.location={search:''};
  c.sessionStorage={getItem:()=>null};c.refreshResumeOfferCtas=()=>{};
  vm.runInContext(source("  window.addEventListener('load', () => {\n    const isNewOffer", "  document.addEventListener('DOMContentLoaded', () => {\n    // Landing CTA"),c);
  listeners.load();c.beginOfferOpenRequest();const original=c.state.data;
  x.get('buyer1First').value='Newly opened';timers.forEach(fn=>fn());
  assert.equal(c.state.data,original);assert.equal(x.get('buyer1First').value,'Newly opened');
});
for(const edited of [false,true])test(`account initialization automatic restore respects user action=${edited}`,async()=>{
  const x=setup();const {store}=enableLocalDraft(x,startupDraft),c=x.ctx;
  store.set('hof_offer_draft_owner','owner');
  Object.assign(c,{supabaseAuthInitialization:null,
    ensureSupabaseClient:async()=>({auth:{getSession:async()=>({data:{session:{user:{id:'owner'}}}}),onAuthStateChange(){}}}),
    updateAuthUI(){},cleanSupabaseAuthUrlNoise(){},ensureProfileShell:async()=>{},flushSubscriptionCheckoutReturnEvent:async()=>{},routeAfterMagicLinkIfNeeded(){}});
  vm.runInContext(source('  async function initSupabaseAuth()', '  function isProfileMeaningful('),c);
  const pending=c.initSupabaseAuth();
  if(edited)c.beginOfferOpenRequest();
  const original=c.state.data;x.get('buyer1First').value='Current';
  await pending;
  assert.equal(x.get('buyer1First').value,edited?'Current':'Saved');
  if(edited)assert.equal(c.state.data,original);
});
test('browser draft snapshot excludes other page forms and files but retains named fixture choices',()=>{
  const x=setup();enableLocalDraft(x,{});
  x.get('profAgentName').value='Private profile value';x.get('propAddress').value='Saved property';
  x.get('uploadedDisclosureDocs').value='C:\\fakepath\\private.pdf';
  const fixture=x.all('#wizardOverlay input[name="leasedFixtureTypes"]')[0];fixture.checked=true;
  x.ctx.state.data.uploadedDocNames=['disclosure.pdf'];
  const draft=x.ctx.getDraftSnapshot();
  assert.equal(draft.fields.profAgentName,undefined);assert.equal(draft.fields.uploadedDisclosureDocs,undefined);
  assert.equal(draft.fields.propAddress,'Saved property');assert.deepEqual(Array.from(draft.checkboxes.leasedFixtureTypes),[fixture.value]);
  assert.deepEqual(Array.from(draft.uploadedDocNames),['disclosure.pdf']);assert.equal(draft.offerId,'previous');
});
for(const role of ['agent','investor','homebuyer']) {
  test(`${role} local restore preserves chosen amounts through the real calculators and replaces stale state`,()=>{
    const x=setup();enableLocalDraft(x,{userType:role,wizardOrderVersion:2,offerId:'saved',step:3,termsOK:false,
      fields:{offerPrice:'500000',earnestMoney:'0',optionFee:'425',optionDays:'10',downPayment:'80000',loanAmount:'420000',loanYears:'15',interestRateCap:'5',interestFirstYears:'15',originationCap:'0',buyerApprovalDays:'14',buyer1First:'Saved',buyer1Last:'Buyer',termsAccepted:false},radios:{financing:'conventional'}});
    x.ctx.state.data.signwellDocumentId='previous-packet';x.get('termsAccepted').checked=true;
    x.get('repairsText').value='Old repairs';x.get('propAddress').value='Old property';
    assert.equal(x.ctx.restoreDraft(),true);
    const expected={earnestMoney:0,optionFee:425,optionDays:10,downPayment:80000,loanAmount:420000,loanYears:15,interestRateCap:5,interestFirstYears:15,originationCap:0,buyerApprovalDays:14};
    for(const [id,value] of Object.entries(expected))assert.equal(Number(x.get(id).value),value,id);
    assert.equal(x.ctx.state.data._hofOfferId,'saved');assert.equal(x.ctx.state.data.userType,role);
    assert.equal(x.ctx.state.data.signwellDocumentId,undefined);assert.equal(x.ctx.state.data.buyer1,'Saved Buyer');
    assert.equal(x.get('repairsText').value,'');assert.equal(x.get('propAddress').value,'');
    assert.equal(x.ctx.state.termsOK,false);assert.equal(x.ctx.__hofRestoringDraft,false);
    assert.ok(x.calls.some(v=>Array.isArray(v)&&v[0]==='step'&&v[2]===role&&v[3]===true));
  });
}
test('legacy draft ignores unrelated controls and file paths while preserving valid answers',()=>{
  const x=setup();enableLocalDraft(x,{fields:{profAgentName:'Old profile',uploadedDisclosureDocs:'C:\\fakepath\\old.pdf',buyer1First:'Legacy',offerPrice:'700000'},radios:{financing:'cash'},termsOK:true});
  x.get('profAgentName').value='Current profile';
  Object.defineProperty(x.get('uploadedDisclosureDocs'),'value',{get:()=>'',set:v=>{if(v)throw new Error('File input cannot be restored');}});
  assert.equal(x.ctx.restoreDraft(),true);assert.equal(x.get('profAgentName').value,'Current profile');
  assert.equal(x.get('buyer1First').value,'Legacy');assert.equal(x.ctx.state.data._hofOfferId,null);
  assert.equal(x.ctx.state.termsOK,true);assert.equal(Number(x.get('loanAmount').value),0);
});
test('named fixture selections round-trip without copying a different form with the same names',()=>{
  const x=setup();const {store}=enableLocalDraft(x,{});
  const group=x.all('#wizardOverlay input[name="leasedFixtureTypes"]');group[0].checked=true;
  const outside=x.controls.find(el=>el.name==='leasedFixtureTypes'&&!el.inWizard);outside.checked=true;
  const draft=x.ctx.getDraftSnapshot();store.set('draft',JSON.stringify(draft));group[0].checked=false;group[1].checked=true;
  assert.equal(x.ctx.restoreDraft(),true);assert.equal(group[0].checked,true);assert.equal(group[1].checked,false);assert.equal(outside.checked,true);
  assert.deepEqual(Array.from(x.ctx.state.data.leasedFixtureTypes),[group[0].value]);
});
for(const owner of ['different-owner','']) {
  test(`local draft owner=${JSON.stringify(owner)} cannot reuse another offer identity`,()=>{
    const x=setup();enableLocalDraft(x,{fields:{buyer1First:'Saved'},offerId:'foreign',userType:'agent'},owner);
    const original=x.ctx.state.data;
    if(owner){assert.equal(x.ctx.restoreDraft(),false);assert.equal(x.ctx.state.data,original);}
    else{assert.equal(x.ctx.restoreDraft(),true);assert.equal(x.ctx.state.data._hofOfferId,null);}
  });
}
for(const malformed of [null,[],{},'not an object',{fields:[]}]) {
  test(`malformed local draft ${JSON.stringify(malformed)} leaves the current interview unchanged`,()=>{
    const x=setup();enableLocalDraft(x,malformed);const original=x.ctx.state.data;
    x.get('buyer1First').value='Keep';assert.equal(x.ctx.restoreDraft(),false);
    assert.equal(x.ctx.state.data,original);assert.equal(x.get('buyer1First').value,'Keep');
  });
}
test('restore carries attachment names but discards prior file contents and attachment acknowledgment',()=>{
  const x=setup();const {timers}=enableLocalDraft(x,{fields:{uploadedDisclosureAck:true},uploadedDocNames:['saved.pdf'],userType:'agent'});
  x.ctx.window.hofUploadedDisclosureDocs=[{name:'previous.pdf',content:'private bytes'}];
  assert.equal(x.ctx.restoreDraft(),true);assert.equal(x.ctx.window.hofUploadedDisclosureDocs.length,0);
  assert.deepEqual(Array.from(x.ctx.state.data.uploadedDocNames),['saved.pdf']);assert.equal(x.get('uploadedDisclosureAck').checked,false);
  assert.equal(timers.length,0);assert.equal(x.ctx.__hofRestoringDraft,false);
});

function enableResumeEntry(x,draft,owner='owner') {
  const local=enableLocalDraft(x,draft,owner),actions=[];
  const c=x.ctx;c.window=c;
  c.__hofLandingAudienceUserSelected=true;
  c.location={search:'',assign:url=>actions.push(['navigate',url])};c.URLSearchParams=URLSearchParams;
  c.trackEvent=(...args)=>actions.push(['analytics',...args]);c.rememberHomebuyerCheckoutChannel=()=>{};
  c.announceWorkspaceStatus=message=>actions.push(['notice',message]);
  c.closeAuthModal=()=>{};
  c.startHomebuyerOffer=()=>actions.push(['fresh']);c.openFsboSellerModal=()=>actions.push(['seller']);
  c.openWizard=(skip,resume)=>actions.push(['open',c.state.data.userType,c.state.step,skip,resume]);
  vm.runInContext(source('  function resumableLocalOfferDraft()', '  function startPrimaryOffer()'),c);
  return {...local,actions};
}
for(const id of ['heroCta','bottomCta','navCta']) {
  test(`${id} actual homepage button resumes the homebuyer draft its label promises`,()=>{
    const draft={userType:'homebuyer',wizardOrderVersion:2,step:4,fields:{buyer1First:'Saved',offerPrice:'550000',earnestMoney:'8800'},radios:{financing:'cash'}};
    const x=setup(),{actions,store}=enableResumeEntry(x,draft);x.ctx.state.data.userType='homebuyer';
    assert.equal(x.ctx.refreshResumeOfferCtas(),true);assert.match(x.get(id).textContent,/Resume/);
    const click=html.match(new RegExp('id="'+id+'"[^>]*onclick="([^"]+)"'))?.[1];assert.ok(click,id);
    vm.runInContext(click,x.ctx);
    assert.equal(actions.some(a=>a[0]==='fresh'),false);assert.equal(x.get('buyer1First').value,'Saved');
    assert.equal(Number(x.get('earnestMoney').value),8800);
    assert.ok(actions.some(a=>a[0]==='open'&&a[1]==='homebuyer'&&a[2]===4&&a[4]===true));
    assert.equal(store.get('draft'),JSON.stringify(draft));
  });
}
for(const role of ['agent','investor'])test(`generic resume preserves ${role} interview instead of converting it to homebuyer`,()=>{
  const x=setup(),{actions}=enableResumeEntry(x,{userType:role,wizardOrderVersion:2,step:3,fields:{buyer1First:'Saved',offerPrice:'550000'},radios:{financing:'cash'}});
  assert.equal(x.ctx.resumeLocalOfferDraft(),true);assert.equal(x.ctx.state.data.userType,role);
  assert.ok(actions.some(a=>a[0]==='open'&&a[1]===role));assert.equal(actions.some(a=>a[0]==='fresh'),false);
});
for(const role of ['agent','investor'])test(`homebuyer buttons do not claim to resume a ${role} draft`,()=>{
  const x=setup();enableResumeEntry(x,{userType:role,step:3,fields:{buyer1First:'Saved'}});x.ctx.state.data.userType='homebuyer';
  x.get('heroCta').textContent='Build Your Offer';assert.equal(x.ctx.refreshResumeOfferCtas(),false);assert.equal(x.get('heroCta').textContent,'Build Your Offer');
});
test('restore failure does not fall back to a destructive fresh start',()=>{
  const draft={userType:'homebuyer',step:3,fields:{buyer1First:'Keep'}};
  const x=setup(),{actions,store}=enableResumeEntry(x,draft);x.ctx.restoreDraft=()=>false;
  assert.equal(x.ctx.resumeLocalOfferDraft(),false);assert.equal(actions.some(a=>a[0]==='fresh'),false);
  assert.equal(store.get('draft'),JSON.stringify(draft));assert.ok(actions.some(a=>a[0]==='notice'));
});
test('unavailable owned draft is not erased by a direct resume request',()=>{
  const draft={userType:'agent',step:3,fields:{buyer1First:'Keep'}};
  const x=setup(),{actions,store}=enableResumeEntry(x,draft,'different-owner');
  assert.equal(x.ctx.resumeLocalOfferDraft(),false);assert.equal(actions.some(a=>a[0]==='fresh'),false);assert.equal(store.get('draft'),JSON.stringify(draft));
});
test('analytics failure cannot turn a successful resume into a user-facing error',()=>{
  const x=setup();enableResumeEntry(x,{userType:'homebuyer',step:3,fields:{buyer1First:'Saved'}});
  x.ctx.trackEvent=()=>{throw new Error('analytics unavailable');};assert.equal(x.ctx.resumeLocalOfferDraft(),true);
});
test('new homepage visitors still begin a fresh homebuyer offer',()=>{
  const x=setup(),{actions,store}=enableResumeEntry(x,null);store.delete('draft');x.ctx.state.data.userType='homebuyer';
  x.ctx.beginOfferFrom('landing_hero_cta');assert.ok(actions.some(a=>a[0]==='fresh'));
});
for(const role of ['agent','investor','fsbo'])test(`explicit ${role} homepage entry keeps its dedicated route`,()=>{
  const x=setup(),{actions}=enableResumeEntry(x,{userType:'homebuyer',step:3,fields:{buyer1First:'Saved'}});
  x.ctx.state.data.userType=role;x.ctx.beginOfferFrom('landing_hero_cta');
  assert.equal(actions.some(a=>a[0]==='open'),false);assert.equal(actions.some(a=>a[0]==='fresh'),false);
  assert.ok(actions.some(a=>a[0]===(role==='fsbo'?'seller':'navigate')));
});
test('resume labels revert when the saved draft is removed without replacing new audience copy',()=>{
  const x=setup(),{store}=enableResumeEntry(x,{userType:'homebuyer',step:3,fields:{buyer1First:'Saved'}});
  x.ctx.state.data.userType='homebuyer';
  for(const id of ['heroCta','bottomCta','navCta'])x.get(id).textContent='Build Your Offer';
  x.get('heroPriceNote').innerHTML='Original price note';x.ctx.refreshResumeOfferCtas();
  store.delete('draft');assert.equal(x.ctx.refreshResumeOfferCtas(),false);
  for(const id of ['heroCta','bottomCta','navCta'])assert.equal(x.get(id).textContent,'Build Your Offer');
  assert.equal(x.get('heroPriceNote').innerHTML,'Original price note');
  store.set('draft',JSON.stringify({userType:'homebuyer',step:3,fields:{buyer1First:'Saved'}}));x.ctx.refreshResumeOfferCtas();
  x.ctx.state.data.userType='agent';x.get('heroCta').textContent='Start a Transaction';x.get('heroPriceNote').innerHTML='Agent information';
  x.ctx.refreshResumeOfferCtas();assert.equal(x.get('heroCta').textContent,'Start a Transaction');assert.equal(x.get('heroPriceNote').innerHTML,'Agent information');
});
