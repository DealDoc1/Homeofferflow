const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{test}=require('node:test');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
function section(a,b){const start=html.indexOf(a),end=html.indexOf(b,start);assert.ok(start>=0&&end>start,a);return html.slice(start,end);}
function setup(financing='conventional'){
  const nodes=new Map(),radios={financing,leases:'no',hoa:'yes',saleContingency:'yes',backupOffer:'yes',nonRealtyItems:'yes',wantsConcessions:'yes',homeWarranty:'yes',brokerFeeType:'amount'};
  const el=id=>{if(!nodes.has(id))nodes.set(id,{value:'',style:{},dataset:{},checked:false,addEventListener(){}});return nodes.get(id);};
  const c=vm.createContext({state:{step:0,data:{}},window:{},document:{getElementById:el,querySelectorAll:()=>[],querySelector:()=>({value:radios.financing})},
    getCurrentSteps:()=>['step3','step5','step7'],getRadio:id=>radios[id]||'',getVal:id=>String(el(id).value??'').trim(),showFieldRecommendation(){},setInputIfEmpty(){},
  });
  vm.runInContext(section('  function moneyNumber(', '  function buildLegalDescription(')
    +section('  function numFromEl(', '  function showFieldRecommendation(')
    +section('  function calculatePriceTermsOnly(', '  function wireSmartCalculations(')
    +section('  function assumptionAnswerKeys(', '  function environmentalInterviewData(')
    +section('  function hydrostaticInterviewData(', '  function hydrostaticInterviewIssues(')
    +section('  function collectData()', '  function selectPlan('),c);
  const values={offerPrice:'500000.55',downPayment:'50000.11',loanAmount:'450000.44',earnestMoney:'5000.45',optionFee:'250.99',optionDays:'7',
    loanYears:'30',interestRateCap:'6.125',interestFirstYears:'30',originationCap:'1.125',buyerApprovalDays:'21',
    hoaReserves:'1000.75',saleAdditionalEarnest:'1500.25',bkupAdditionalEarnest:'1000.55',bkupAdditionalOption:'50.25',nonRealtyAmount:'150.75',nonRealtyDescription:'QA appliances',
    concessionAmount:'2000.75',homeWarrantyAmount:'650.25',brokerFeeAmount:'2500.75',possession:'funding'};
  for(const [id,value] of Object.entries(values))el(id).value=value;
  return {c,el,radios};
}
function collectExample(financing='conventional'){
  const x=setup(financing);for(x.c.state.step=0;x.c.state.step<3;x.c.state.step++)x.c.collectData();return JSON.parse(JSON.stringify(x.c.state.data));
}
module.exports={setup,collectExample};
if(require.main===module){
  test('answer collection preserves cents for every supported ordinary financing choice',()=>{
    for(const financing of ['cash','conventional','fha','va','usda']){
      const data=collectExample(financing);assert.equal(data.price,500000.55);assert.equal(data.earnest,5000.45);assert.equal(data.optionFee,250.99);
      assert.equal(data.loanAmount,financing==='cash'?0:450000.44);assert.equal(data.downPayment,financing==='cash'?500000.55:50000.11);
      for(const [key,value] of Object.entries({hoaReserves:1000.75,saleAdditionalEarnest:1500.25,bkupAdditionalEarnest:1000.55,bkupAdditionalOption:50.25,nonRealtyAmount:150.75,concessionAmount:2000.75,homeWarrantyAmount:650.25,brokerFeeAmount:2500.75}))assert.equal(data[key],value,key);
      if(financing!=='cash')assert.equal(data.interestRateCap,'6.125','Currency precision must not limit rate precision');
    }
  });
  test('calculated money rounds to nearest cent, not whole dollars',()=>{
    const {c,el}=setup();for(const [input,expected] of [[1.005,1.01],[1.004,1],[1000000.005,1000000.01],[0.1+0.2,0.3],[500000.55-450000.44,50000.11]])assert.equal(c.roundCurrency(input),expected);
    c.setMoneyVal(el('result'),50000.115);assert.equal(el('result').value,50000.12);
  });
  test('default down payment and loan balance add back to the exact sales price',()=>{
    for(const financing of ['conventional','fha','va','usda','cash']){
      const {c,el}=setup(financing);c.calculateFinancingDefaults(true);
      assert.equal(Math.round(Number(el('downPayment').value)*100)+Math.round(Number(el('loanAmount').value)*100),50000055);
    }
  });
  test('an edited down payment derives the missing loan amount to cents',()=>{
    const {c,el}=setup();el('loanAmount').value='';c.collectData();assert.equal(c.state.data.loanAmount,450000.44);
    el('loanAmount').value='450000.44';el('downPayment').value='';c.collectData();assert.equal(c.state.data.downPayment,50000.11);
  });
  test('an empty financing split receives cent-accurate editable defaults',()=>{
    const {c,el}=setup();el('loanAmount').value='';el('downPayment').value='';c.collectData();assert.equal(c.state.data.downPayment,50000.06);assert.equal(c.state.data.loanAmount,450000.49);
  });
  test('money suggestions never overwrite edited amounts',()=>{
    const {c,el}=setup();for(const id of ['downPayment','loanAmount','earnestMoney'])el(id)._userEdited=true;
    c.calculateFinancingDefaults(false);c.calculatePriceTermsOnly();assert.equal(el('downPayment').value,'50000.11');assert.equal(el('loanAmount').value,'450000.44');assert.equal(el('earnestMoney').value,'5000.45');
  });
  test('displayed calculator currency no longer hides entered cents',()=>{
    const {c}=setup();vm.runInContext(section('  function fmtCurrencyShort(', '  function getCalcNumber('),c);assert.equal(c.fmtCurrencyShort(50000.11),'$50,000.11');assert.equal(c.fmtCurrencyShort(0),'$0.00');
  });
}
