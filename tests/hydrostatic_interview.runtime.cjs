const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
function section(start, end) {
  const first = html.indexOf(start), last = html.indexOf(end, first);
  assert.ok(first >= 0 && last > first);
  return html.slice(first, last);
}
const helpers = section('  function hydrostaticSigningSummary(', '  function validateSellerTemporaryLeaseInputs(');
const collector = section('  function collectData()', '  function selectPlan(');
function setup(data = {}) {
  const fields = new Map();
  const radio = {hydrostaticTesting:'yes', leases:'no'};
  const el = id => {
    if (!fields.has(id)) fields.set(id, {value:'', style:{}, dataset:{}, setAttribute(){}, removeAttribute(){}});
    return fields.get(id);
  };
  const context = vm.createContext({
    state:{step:0, data:{buyerEmail:'buyer@example.test', ...data}},
    document:{getElementById:el, querySelectorAll:()=>[]}, getVal:id => String(el(id).value || '').trim(), getRadio:id => radio[id] || '',
    window:{},
    setInputIfEmpty:(id, value, force=false) => {if(value != null && value !== '' && (force || !el(id).value)) el(id).value=value;},
    setRadioValue:(id,value)=>{radio[id]=value;},
    updateParagraph4LeaseVisibility:()=>{}, updateSurveyExistingDetails:()=>{},
    getCurrentSteps:() => ['step5'], moneyNumber:value => Number(value) || '',
    setPaymentStatus:message => {context.message=message;},
  });
  vm.runInContext(section('  function escapeAttr(', '  function withTimeout(') + helpers + collector, context);
  return {context, fields, radio, el};
}
const valid = {hydrostaticTesting:'yes', hydrostaticRiskAllocation:'buyer_capped', hydrostaticBuyerLiabilityLimit:'2,500.00',
               buyer1:'Buyer One', buyerEmail:'buyer@example.test', seller1Name:'Seller One', seller1Email:'seller@example.test'};

test('mineral interview asks only selected terms and reuses valid packet signers', () => {
  const {context:c} = setup();
  const data={...valid,hydrostaticTesting:'no',mineralReservation:'yes',mineralReservationChoice:'undivided_interest',mineralUndividedInterest:'25.125',mineralSurfaceRights:'waived'};
  assert.equal(c.mineralInterviewIssues(data).length,0);
  for(const value of ['', '0', '-1', '100.1', 'NaN', '1e2', '2,5', '1.12345']) {
    assert.equal(c.mineralInterviewIssues({...data,mineralUndividedInterest:value},false)[0].id,'mineralUndividedInterest');
  }
  assert.equal(c.mineralInterviewIssues({...data,mineralReservationChoice:'all',mineralUndividedInterest:'old'}).length,0);
  assert.equal(c.mineralInterviewIssues({...data,mineralSurfaceRights:''},false)[0].id,'mineralSurfaceRights');
  assert.equal(c.mineralInterviewIssues({...data,mineralReservationChoice:''},false)[0].id,'mineralReservationChoice');
  assert.ok(c.mineralInterviewIssues({...data,seller1Email:'bad'}).length);
  assert.equal(c.validateMineralInputs({...data,seller1Email:'bad'}),false);
  assert.equal(c.validateMineralInputs({mineralReservation:'no'}),true);
});

test('mineral selection shows shared sellers and removes stale choices from the package',()=>{
  const {context:c,el,radio}=setup();radio.hydrostaticTesting='no';radio.mineralReservation='yes';
  el('mineralReservationChoice').value='undivided_interest';el('mineralUndividedInterest').value='25.125';el('mineralSurfaceRights').value='not_waived';
  el('seller1').value='Seller One';c.updateMineralVisibility();c.collectData();
  assert.equal(el('mineralDetails').style.display,'block');assert.equal(el('mineralInterestField').style.display,'block');
  assert.equal(el('sellerSigningFields').style.display,'flex');assert.equal(el('seller1Name').value,'Seller One');
  assert.equal(c.state.data.mineralUndividedInterest,'25.125');
  el('mineralReservationChoice').value='all';c.collectData();c.updateMineralVisibility();
  assert.equal(c.state.data.mineralUndividedInterest,'');assert.equal(el('mineralInterestField').style.display,'none');
  radio.mineralReservation='no';c.collectData();c.updateMineralVisibility();
  assert.equal(c.state.data.mineralReservationAddendum,'no');assert.equal(c.state.data.mineralSurfaceRights,'');
  assert.equal(c.state.data.mineralReservationChoice,'');assert.equal(el('sellerSigningFields').style.display,'none');
  assert.equal(el('mineralUndividedInterest').value,'25.125','Keep editable answer if they switch back');
});

test('mineral validation marks missing terms and does not erase hydrostatic signer errors',()=>{
  const {context:c,el,radio}=setup(valid);radio.mineralReservation='yes';
  c.markHydrostaticInterviewIssues([],true);
  const missing=[];c.markMineralInterviewIssues(missing,true);
  assert.ok(missing.includes('choose the mineral interest the seller reserves'));
  assert.equal(el('mineralReservationChoice').dataset.validationInvalid,'true');
  assert.equal(el('seller1Email').dataset.validationInvalid,'true');
  assert.match(c.mineralSigningSummary({}),/Seller acceptance.*remains/);
  assert.match(c.mineralSigningSummary({possession:'sellerTemporaryLease'}),/purchase contract, temporary lease, mineral/);
});

test('switching to As Is clears hidden repair text from collected packet data',()=>{
  const {context:c,radio,el}=setup({asIs:'repairs',repairsText:'Old requirement'});
  c.getCurrentSteps=()=>['step6'];el('repairsText').value='Old requirement';radio.asIs='yes';
  c.collectData();assert.equal(c.state.data.asIs,'yes');assert.equal(c.state.data.repairsText,'');
  assert.equal(el('repairsText').value,'Old requirement','Keep the editable answer in case the user switches back');
  radio.asIs='repairs';c.collectData();assert.equal(c.state.data.repairsText,'Old requirement');
});

test('all inline application scripts remain syntactically valid', () => {
  for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    if (/src=|application\/ld\+json/.test(match[1])) continue;
    new vm.Script(match[2]);
  }
});
test('risk is never defaulted, and only a capped election needs an amount', () => {
  const {context:c} = setup();
  assert.equal(c.hydrostaticInterviewIssues({...valid, hydrostaticRiskAllocation:''}, false)[0].id, 'hydrostaticRiskAllocation');
  for (const amount of ['', '-1', '1e3', '2,50', '1.001', '1000000000', 'Infinity']) {
    assert.equal(c.hydrostaticInterviewIssues({...valid, hydrostaticBuyerLiabilityLimit:amount}, false).length, 1);
  }
  for (const amount of ['0', '2,500.25', '999999999.99']) {
    assert.equal(c.hydrostaticInterviewIssues({...valid, hydrostaticBuyerLiabilityLimit:amount}, false).length, 0);
  }
  assert.equal(c.hydrostaticInterviewIssues({...valid, hydrostaticRiskAllocation:'seller', hydrostaticBuyerLiabilityLimit:''}, false).length, 0);
});
test('seller identity requires a name, distinct valid email, and paired optional seller', () => {
  const {context:c} = setup();
  assert.equal(c.hydrostaticInterviewIssues(valid).length, 0);
  for (const changes of [{buyer1:''}, {buyer2:'Missing Email'}, {buyer2Email:'missing-name@example.test'},
                         {buyer2:'Two',buyer2Email:'BUYER@example.test'}, {seller1Name:''}, {seller1Email:'bad'}, {seller1Email:'BUYER@example.test'},
                         {seller2Email:'two@example.test'}, {seller2Name:'Two'}, {seller2Name:'Two',seller2Email:'seller@example.test'}]) {
    assert.ok(c.hydrostaticInterviewIssues({...valid,...changes}).length > 0);
  }
  const lease = {...valid, leases:'yes', paragraph4Seller1Name:'Lease Seller', paragraph4Seller1Email:'lease@example.test', seller1Email:'stale'};
  assert.equal(c.hydrostaticInterviewIssues(lease).length, 0);
});
test('conditional follow-ups use the shared seller fields and preserve typed answers', () => {
  const {context:c, el, radio} = setup();
  el('hydrostaticRiskAllocation').value='buyer_capped';
  el('seller1').value='Seller One';
  el('paragraph4Seller1Email').value='stale@example.test';
  c.updateHydrostaticVisibility();
  assert.equal(el('hydrostaticDetails').style.display,'block');
  assert.equal(el('hydrostaticLimitField').style.display,'block');
  assert.equal(el('sellerSigningFields').style.display,'flex');
  assert.equal(el('seller1Name').value,'Seller One');
  assert.equal(el('seller1Email').value,'');
  el('seller1Email').value='current@example.test';
  radio.leases='yes'; c.updateHydrostaticVisibility();
  assert.equal(el('sellerSigningFields').style.display,'none');
  assert.equal(el('seller1Email').value,'current@example.test');
  radio.hydrostaticTesting='no'; c.updateHydrostaticVisibility();
  assert.equal(el('hydrostaticDetails').style.display,'none');
  assert.equal(el('hydrostaticLimitField').style.display,'none');
});
test('collecting answers clears deselected terms and legacy selection without rounding cents', () => {
  const {context:c, el, radio} = setup();
  el('hydrostaticRiskAllocation').value='buyer_capped';
  el('hydrostaticBuyerLiabilityLimit').value='2500.25';
  c.collectData();
  assert.equal(c.state.data.hydrostaticBuyerLiabilityLimit,'2500.25');
  el('hydrostaticRiskAllocation').value='buyer'; c.collectData();
  assert.equal(c.state.data.hydrostaticBuyerLiabilityLimit,'');
  radio.hydrostaticTesting='no'; c.collectData();
  assert.equal(c.state.data.hydrostaticAddendum,'no');
  assert.equal(c.state.data.hydrostaticRiskAllocation,'');
});
test('generation validation cannot skip missing signer details', () => {
  const {context:c}=setup();
  assert.equal(c.validateHydrostaticInputs({...valid, seller1Email:''}), false);
  assert.match(c.message, /Seller 1 email/);
  assert.equal(c.validateHydrostaticInputs(valid), true);
  assert.equal(c.validateHydrostaticInputs({hydrostaticTesting:'no'}), true);
  assert.equal((html.match(/if \(!validateHydrostaticInputs\(state.data\)\) return;/g)||[]).length,2);
});
test('review describes the actual seller signature scope for each packet', () => {
  const {context:c}=setup();
  assert.match(c.hydrostaticSigningSummary({possession:'funding'}), /Seller acceptance.*remains with/);
  assert.match(c.hydrostaticSigningSummary({possession:'sellerTemporaryLease'}), /purchase contract, temporary lease, hydrostatic/);
  assert.doesNotMatch(c.hydrostaticSigningSummary({possession:'sellerTemporaryLease'}), /remains with/);
});
test('the actual review contains the selected amount and removes it when deselected', () => {
  const {context:c,el}=setup(valid);
  c.document.getElementById=id=>{
    assert.ok(html.includes('id="' + id + '"'), 'Review target exists: ' + id);
    const element=el(id);
    element.insertAdjacentHTML=(_position,value)=>{element.innerHTML += value;};
    return element;
  };
  vm.runInContext(section('  function buildReview()', '  function toggleHelper('), c);
  c.buildReview();
  assert.match(el('reviewSummary').innerHTML,/Buyer up to \$2,500/);
  assert.match(el('reviewSigningExpectation').textContent,/invitations together/);
  c.state.data.hydrostaticTesting='no'; c.buildReview();
  assert.doesNotMatch(el('reviewSummary').innerHTML,/Buyer up to/);
});
test('restoring a saved draft restores follow-ups and clears a previous offer signer', () => {
  const {context:c,el,radio}=setup();
  vm.runInContext(section('  function clearOfferInterviewFields(', '  async function resumeOffer('), c);
  el('seller2Name').value='Previous Seller';
  el('seller2Email').value='old@example.test';
  el('paragraph4Seller2Email').value='older@example.test';
  c.applyOfferDataToFields(valid);
  assert.equal(el('hydrostaticRiskAllocation').value,'buyer_capped');
  assert.equal(el('hydrostaticBuyerLiabilityLimit').value,'2,500.00');
  assert.equal(el('hydrostaticLimitField').style.display,'block');
  assert.equal(el('seller2Name').value,'');
  assert.equal(el('seller2Email').value,'');
  assert.equal(el('paragraph4Seller2Email').value,'');
  c.applyOfferDataToFields({hydrostaticTesting:'no'});
  assert.equal(el('hydrostaticBuyerLiabilityLimit').value,'');
  assert.equal(el('hydrostaticRiskAllocation').value,'');
  assert.equal(radio.hydrostaticTesting,'no');
  assert.equal(el('hydrostaticDetails').style.display,'none');
});
test('validation marks the missing answer for accessible focus and clears when corrected', () => {
  const {context:c,el}=setup();
  let missing=[]; c.markHydrostaticInterviewIssues(missing,false);
  assert.equal(el('hydrostaticRiskAllocation').dataset.validationInvalid,'true');
  el('hydrostaticRiskAllocation').value='seller';
  missing=[]; c.markHydrostaticInterviewIssues(missing,false);
  assert.equal(missing.length,0);
  assert.equal(el('hydrostaticRiskAllocation').dataset.validationInvalid,undefined);
});

test('restoring a mineral draft restores elections without leaking an older offer',()=>{
  const {context:c,el,radio}=setup();
  vm.runInContext(section('  function clearOfferInterviewFields(', '  async function resumeOffer('),c);
  c.applyOfferDataToFields({...valid,hydrostaticTesting:'no',mineralReservationAddendum:true,
    mineralReservationChoice:'undivided_interest',mineralUndividedInterest:'25.125',mineralSurfaceRights:'not_waived'});
  assert.equal(radio.mineralReservation,'yes');
  assert.equal(el('mineralUndividedInterest').value,'25.125');
  assert.equal(el('mineralInterestField').style.display,'block');
  assert.equal(el('mineralSurfaceRights').value,'not_waived');
  c.applyOfferDataToFields({});
  assert.equal(radio.mineralReservation,'no');
  for(const id of ['mineralReservationChoice','mineralUndividedInterest','mineralSurfaceRights'])assert.equal(el(id).value,'');
  assert.equal(el('mineralDetails').style.display,'none');
});

test('review shows actual mineral terms, escapes text, and removes deselected terms',()=>{
  const {context:c,el}=setup({...valid,mineralReservation:'yes',mineralReservationChoice:'undivided_interest',
    mineralUndividedInterest:'25.125',mineralSurfaceRights:'waived'});
  c.document.getElementById=id=>{const element=el(id);element.insertAdjacentHTML=(_p,v)=>{element.innerHTML+=v;};return element;};
  vm.runInContext(section('  function buildReview()', '  function toggleHelper('),c);
  c.buildReview();
  assert.match(el('reviewSummary').innerHTML,/25.125% of mineral estate/);
  assert.match(el('reviewSummary').innerHTML,/Surface rights.*Waived/);
  assert.match(el('reviewSigningExpectation').textContent,/mineral-reservation addendum/);
  c.state.data.mineralUndividedInterest='<img src=x onerror=alert(1)>';c.buildReview();
  assert.doesNotMatch(el('reviewSummary').innerHTML,/<img src=x/);
  c.state.data.mineralReservation='no';c.buildReview();
  assert.doesNotMatch(el('reviewSummary').innerHTML,/Seller reserves/);
});
