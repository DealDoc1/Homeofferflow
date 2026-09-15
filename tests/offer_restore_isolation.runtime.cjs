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
  const elements = new Map(), controls = [], cards = [], calls = [];
  const wizardStart = html.indexOf('id="wizardOverlay"');
  const wizardEnd = html.indexOf('<script>', wizardStart);
  function node(id='') {
    const classes=new Set();
    return {id,value:'',checked:false,type:'text',style:{},dataset:{},
      classList:{add:k=>classes.add(k), remove:k=>classes.delete(k), toggle:(k,on)=>on?classes.add(k):classes.delete(k)},
      setAttribute(){},removeAttribute(){},closest(){return this.card || null;}};
  }
  for (const match of html.matchAll(/<(input|textarea|select)\b([^>]*)>/g)) {
    const attrs=Object.fromEntries([...match[2].matchAll(/([\w-]+)="([^"]*)"/g)].map(m=>[m[1],m[2]]));
    if (!attrs.id && !attrs.name) continue;
    const el=Object.assign(node(attrs.id),attrs);
    el.inWizard=match.index>wizardStart && match.index<wizardEnd;
    if (attrs.type === 'radio') {el.card=node(); cards.push(el.card);}
    controls.push(el);
    if(attrs.id) elements.set(attrs.id,el);
  }
  const get=id=>{if(!elements.has(id))elements.set(id,node(id)); return elements.get(id);};
  function all(selector) {
    if(selector==='#wizardOverlay input, #wizardOverlay textarea, #wizardOverlay select') return controls.filter(el=>el.inWizard);
    if(selector==='#wizardOverlay .radio-card') return controls.filter(el=>el.inWizard&&el.card).map(el=>el.card);
    const name=selector.match(/\[name="([^"]+)"\]/)?.[1];
    if(name) {
      const value=selector.match(/\[value="([^"]+)"\]/)?.[1];
      return controls.filter(el=>el.name===name && (value===undefined || el.value===value) && (!selector.includes(':checked')||el.checked));
    }
    return [];
  }
  const ctx=vm.createContext({
    state:{data:{userType:'agent',buyer1:'Previous Client',buyerEmail:'previous@example.test',repairsText:'Previous repairs',_hofOfferId:'previous'},selectedPlan:'old',selectedPrice:99},
    hofAuth:{role:'agent',session:{user:{id:'owner',email:'account@example.test'}},accountProfile:{}},
    document:{getElementById:get,querySelectorAll:all,querySelector:s=>all(s)[0]||null},
    getVal:id=>String(get(id).value||'').trim(),getRadio:name=>all('input[name="'+name+'"]:checked')[0]?.value||'',
    updateParagraph4LeaseVisibility(){},toggleSellerTemporaryLeaseFields(){},updateHydrostaticVisibility(){},updateSurveyExistingDetails(){},
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
  const clearStart=html.includes('  function clearOfferInterviewFields(')?'  function clearOfferInterviewFields(':'  function applyOfferDataToFields(';
  vm.runInContext(source(clearStart,'  async function resumeOffer('),ctx);
  vm.runInContext(source('  async function resumeOffer(', '  async function duplicateOffer('),ctx);
  vm.runInContext(source('  async function reuseOfferTerms(', '  async function deleteOffer('),ctx);
  return {ctx,get,all,calls};
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
