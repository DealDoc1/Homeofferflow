const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{test}=require('node:test');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
function section(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0&&b>a,start);return html.slice(a,b);}
const valid={financing:'assumption',price:'500000.55',assumptionCreditDays:'7',assumptionCreditDocuments:['credit_report','other'],assumptionCreditOther:'QA proof',
  assumptionFirstEnabled:true,assumptionFirstLender:'QA Lender',assumptionFirstBalance:'240000.12',assumptionFirstPayment:'1750.25',assumptionFirstFeeCap:'500.25',assumptionFirstRateCap:'6.125',
  assumptionSecondEnabled:true,assumptionSecondLender:'QA Second',assumptionSecondBalance:'30000.23',assumptionSecondPayment:'300.50',assumptionSecondFeeCap:'0',assumptionSecondRateCap:'8',
  assumptionVarianceAdjustment:'cash',assumptionVarianceThreshold:'2500.75',buyer1:'QA Buyer',buyerEmail:'buyer@example.test',seller1Name:'QA Seller',seller1Email:'seller@example.test',leases:'no'};
function setup(){
  const fields=new Map(),radio={financing:'assumption',leases:'no'},docs=['credit_report','employment','funds','financial_statement','other'].map(value=>({value,checked:false}));
  const el=id=>{if(!fields.has(id))fields.set(id,{value:'',checked:false,style:{},dataset:{},innerHTML:'',setAttribute(){},removeAttribute(){},insertAdjacentHTML(_p,value){this.innerHTML+=value;}});return fields.get(id);};
  const c=vm.createContext({state:{step:0,data:{buyer1:valid.buyer1,buyerEmail:valid.buyerEmail}},window:{},
    document:{getElementById:el,querySelectorAll:s=>s.includes('assumptionCreditDocuments')?docs.filter(x=>!s.endsWith(':checked')||x.checked):[],querySelector:s=>s.includes('name="financing"')?{value:radio.financing}:null},
    getVal:id=>String(el(id).value??'').trim(),getRadio:id=>radio[id]||'',moneyNumber:v=>v===''?'':Number(String(v).replace(/,/g,'')),getCurrentSteps:()=>['step3'],
    setInputIfEmpty:(id,v)=>{if(!el(id).value&&v)el(id).value=v;},setRadioValue:(id,v)=>radio[id]=v,
    setPaymentStatus:message=>c.message=message,setValidationStatus:message=>c.message=message,guideToFirstValidationAnswer:()=>{},
    requireField:(id,label,missing)=>{if(!el(id).value)missing.push(label);},requireRadioSelection:(id,label,missing)=>{if(!radio[id])missing.push(label);},
    setAppraisalAddendumRequired:()=>{},numFromEl:field=>Number(field.value),getCalcNumber:id=>Number(el(id).value),getSelectedFinancingType:()=>radio.financing,getCurrentFinancingChoice:()=>radio.financing,
  });
  vm.runInContext(section('  function escapeAttr(', '  function withTimeout(')+section('  function hydrostaticSigningSummary(', '  function validateSellerTemporaryLeaseInputs(')+section('  function collectData()', '  function selectPlan(')+section('  function validateCurrentStep()', '  function startHomebuyerOffer(')+section('  function updateAppraisalAddendumVisibility(', '  function sanitizeBuyerMailingAddressAutofill('),c);
  vm.runInContext(section('  function moneyNumber(', '  function buildLegalDescription('),c);
  c.restoreAssumptionAnswers(valid);el('offerPrice').value=valid.price;el('seller1Name').value=valid.seller1Name;el('seller1Email').value=valid.seller1Email;
  el('earnestMoney').value='5000';el('optionFee').value='250';el('optionDays').value='7';el('appraisalAddendumBox').style.display='none';
  return {c,el,radio,docs};
}
test('money parser and totals preserve cents without accepting malformed amounts',()=>{
  const {c}=setup();assert.equal(c.assumptionCents('240,000.12'),24000012);
  for(const value of ['','1e2','1,00','NaN','-1','0.001','1000000000'])assert.equal(c.assumptionCents(value),null,value);
  assert.deepEqual(JSON.parse(JSON.stringify(c.assumptionTotals(valid))),{loan:27000035,cash:23000020,payment:205075});
  assert.equal(c.assumptionTotals({...valid,price:'100000'}),null);
  assert.equal(c.assumptionTotals({...valid,assumptionFirstPayment:''}).payment,null);
});
test('valid assumption advances price step without hidden new-mortgage terms',()=>{
  const {c,el}=setup();c.collectData();assert.equal(c.validateCurrentStep(),true,c.message);
  assert.equal(c.state.data.price,'500000.55');assert.equal(c.state.data.loanAmount,'270000.35');assert.equal(c.state.data.downPayment,'230000.20');
  assert.equal(el('loanYears').value,'');assert.equal(c.state.data.loanAssumption,'yes');
});
test('new mortgages still require their own terms',()=>{
  const {c,radio}=setup();radio.financing='conventional';assert.equal(c.validateCurrentStep(),false);assert.match(c.message,/loan amount/);
});
test('selected-loan and credit-document validation matches backend constraints',()=>{
  const {c}=setup();assert.equal(c.assumptionInterviewIssues(valid).length,0);
  for(const [key,value] of [['assumptionCreditDays','0'],['assumptionCreditDays','1e2'],['assumptionCreditDocuments',[]],['assumptionCreditDocuments',['bad']],['assumptionCreditOther',''],['assumptionFirstLender',''],['assumptionFirstRateCap','101'],['assumptionFirstRateCap','6.12345'],['assumptionFirstBalance','0'],['assumptionFirstPayment',''],['assumptionFirstFeeCap','-1'],['assumptionVarianceAdjustment',''],['assumptionVarianceThreshold','1.001']])assert.ok(c.assumptionInterviewIssues({...valid,[key]:value},false).length,key);
  assert.equal(c.assumptionInterviewIssues({...valid,assumptionFirstPayment:'0',assumptionFirstFeeCap:'0',assumptionFirstRateCap:'0',assumptionVarianceThreshold:'0'},false).length,0);
});
test('missing selections mark visible questions for accessible focus',()=>{
  const {c,el}=setup();el('assumptionFirstEnabled').checked=false;el('assumptionSecondEnabled').checked=false;
  const missing=[];c.markAssumptionInterviewIssues(missing,false);assert.ok(missing.includes('choose at least one existing loan'));assert.equal(el('assumptionLoans').dataset.validationInvalid,'true');
  el('assumptionFirstEnabled').checked=true;c.markAssumptionInterviewIssues([],false);assert.equal(el('assumptionLoans').dataset.validationInvalid,undefined);
});
test('shared seller fields and generation validation include assumption',()=>{
  const {c,el}=setup();c.updateAssumptionVisibility();assert.equal(el('sellerSigningFields').style.display,'flex');
  assert.equal(c.validateAssumptionInputs(valid),true);assert.equal(c.validateAssumptionInputs({...valid,seller1Email:''}),false);assert.match(c.message,/Seller 1 email/);
  assert.equal((html.match(/if \(!validateAssumptionInputs\(state.data\)\) return;/g)||[]).length,2);
});
test('deselected loan answers stay editable but are not submitted',()=>{
  const {c,el,docs}=setup();el('assumptionFirstEnabled').checked=false;el('assumptionFirstBalance').value='invalid';docs.find(x=>x.value==='other').checked=false;c.collectData();
  assert.equal(c.state.data.loanAmount,'30000.23');assert.equal(c.state.data.downPayment,'470000.32');assert.equal(c.state.data.assumptionFirstBalance,'');assert.equal(c.state.data.assumptionCreditOther,'');
  assert.equal(el('assumptionFirstBalance').value,'invalid');assert.equal(c.assumptionInterviewIssues(c.state.data,false).length,0);
});
test('changing to cash clears all submitted assumption terms and restores calculator',()=>{
  const {c,el,radio}=setup();c.updateAssumptionVisibility();assert.equal(el('paymentCalcCard').style.display,'none');
  radio.financing='cash';c.updateAssumptionVisibility();c.collectData();assert.equal(c.state.data.loanAssumption,'no');assert.equal(c.state.data.assumptionFirstEnabled,false);assert.equal(c.state.data.assumptionCreditDays,'');assert.equal(c.state.data.loanAmount,0);assert.equal(c.state.data.downPayment,500000.55);
  assert.equal(el('assumptionDetails').style.display,'none');assert.equal(el('sellerSigningFields').style.display,'none');assert.equal(el('paymentCalcCard').style.display,'');
});
test('restoring a different draft clears previous assumption answers and checkboxes',()=>{
  const {c,el,docs}=setup();c.restoreAssumptionAnswers({assumptionSecondEnabled:'yes',assumptionSecondLender:'Other lender',assumptionCreditDocuments:['funds']});
  assert.equal(el('assumptionFirstEnabled').checked,false);assert.equal(el('assumptionFirstLender').value,'');assert.equal(el('assumptionSecondEnabled').checked,true);assert.equal(el('assumptionSecondLender').value,'Other lender');assert.deepEqual(docs.filter(x=>x.checked).map(x=>x.value),['funds']);
  assert.ok(html.includes('restoreAssumptionAnswers(data);'));
});
test('totals update immediately and missing monthly payment is not presented as zero',()=>{
  const {c,el}=setup();c.updateAssumptionTotals();assert.match(el('assumptionTotals').textContent,/\$230,000.20/);assert.match(el('assumptionTotals').textContent,/\$2,050.75/);
  el('assumptionFirstPayment').value='';c.updateAssumptionTotals();assert.doesNotMatch(el('assumptionTotals').textContent,/Current monthly/);
  el('offerPrice').value='100';c.updateAssumptionTotals();assert.equal(el('loanAmount').value,'');
});
test('new-mortgage defaults and estimated payment never run for assumption',()=>{
  const {c,el}=setup();vm.runInContext(section('  function calculateFinancingDefaults(', '  function wireSmartCalculations(')+section('  function updatePaymentCalculator()', '  function wirePaymentCalculator('),c);
  el('loanAmount').value='450000';el('downPayment').value='50000';
  c.calculateFinancingDefaults(true);assert.equal(el('loanAmount').value,'450000');assert.equal(el('downPayment').value,'50000');assert.equal(el('loanYears').value,'');c.updatePaymentCalculator();assert.equal(el('paymentCalcCard').style.display,'none');assert.equal(el('calcPI').textContent,undefined);
  c.collectData();assert.equal(c.state.data.loanAmount,'270000.35');assert.equal(c.state.data.downPayment,'230000.20');
});
test('appraisal terms are not inherited from a new mortgage',()=>{
  const {c,el,radio}=setup();radio.appraisalAddendum='partial';c.updateAppraisalAddendumVisibility();assert.equal(el('appraisalAddendumBox').style.display,'none');assert.equal(radio.appraisalAddendum,'none');c.collectData();assert.equal(c.state.data.appraisalPartialValue,'');
});
test('review includes full selected terms with safe text and simultaneous-signing scope',()=>{
  const {c,el}=setup();c.state.data={...valid,loanAmount:'270000.35',downPayment:'230000.20',assumptionFirstLender:'<img src=x>',assumptionCreditOther:'<script>bad</script>'};
  vm.runInContext(section('  function buildReview()', '  function toggleHelper('),c);c.buildReview();
  assert.match(el('reviewSummary').innerHTML,/Loan Assumption Addendum/);assert.match(el('reviewSummary').innerHTML,/230,000.2/);assert.match(el('reviewSummary').innerHTML,/6.125%/);assert.match(el('reviewSummary').innerHTML,/&lt;img/);assert.doesNotMatch(el('reviewSummary').innerHTML,/<script>bad/);assert.match(el('reviewSigningExpectation').textContent,/invitations together/);
  c.state.data.financing='cash';c.buildReview();assert.doesNotMatch(el('reviewSummary').innerHTML,/Loan Assumption Addendum|First-lien lender/);
});
test('UI answer controls exist, have labels, and no lender consent is preselected',()=>{
  const {c}=setup();for(const id of c.assumptionAnswerKeys()){assert.ok(html.includes('id="'+id+'"'),id);assert.ok(html.includes('for="'+id+'"'),id);}
  const markup=section('        <div id="assumptionDetails"','        <div class="field-group" id="financingDetails"');assert.doesNotMatch(markup,/checked(?:\s|=|\/?>)/);assert.match(markup,/Signing does not obtain lender consent/);
});
