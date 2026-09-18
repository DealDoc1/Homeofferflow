const fs=require('node:fs');
const vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const test=require('node:test');
const assert=require('node:assert/strict');
const html=process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git',['show',process.env.HOF_TEST_SOURCE_REF+':index.html'],{encoding:'utf8',maxBuffer:8*1024*1024})
  : fs.readFileSync('index.html','utf8');
function source(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0&&b>a);return html.slice(a,b);}
function setup(data={},docs=[]){
  const nodes={};
  for(const id of ['reviewSummary','reviewDeliveryExpectation','reviewSigningExpectation','reviewRevisionExpectation','uploadedDocsList','uploadedDisclosureAckRow','uploadedDocsResumeNotice']){
    nodes[id]={innerHTML:'',textContent:'',style:{},querySelectorAll:()=>[],querySelector:()=>null,insertAdjacentHTML(_,value){this.innerHTML+=value;}};
  }
  const ctx={state:{data},window:{hofUploadedDisclosureDocs:docs},document:{getElementById:id=>nodes[id]||null}};
  vm.createContext(ctx);
  // Use the actual globally available helper; do not hide a scope error with a stub.
  vm.runInContext(source('  function escapeAttr(', '  function withTimeout('),ctx);
  vm.runInContext(source('  function buildReview()', '  function toggleHelper('),ctx);
  vm.runInContext(source('  const uploadedDisclosureTypes =','  function readFileAsBase64('),ctx);
  ctx.nodes=nodes;return ctx;
}
const payload='<img src=x onerror="alert(1)"> & "Client"';
const escaped='&lt;img src=x onerror=&quot;alert(1)&quot;&gt; &amp; &quot;Client&quot;';
const fields=['buyer1','buyer2','seller','buyerPhone','buyerEmail','buyerMailAddr','address','city','zip','county','lotNumber','blockNumber','subdivision','legalDescription','optionDays','financing','appraisalTerminateDays','nonRealtyDescription','disclosureDays','closingDate','titleCompany','agentName','agentBrokerage','brokerFeePercent'];
for(const field of fields)test(`review displays ${field} as text`,()=>{
  const data={buyer1:'Buyer',address:'123 Main',financing:'conventional',appraisalAddendum:'additional',nonRealtyItems:'yes',sellerDisclosure:'notReceived',hasBuyerAgent:'yes',brokerFeeType:'percent',[field]:payload};
  const before=JSON.stringify(data),x=setup(data);x.buildReview();
  const out=x.nodes.reviewSummary.innerHTML;
  assert.ok(!out.includes('<img'),out);
  assert.ok(out.includes(escaped),`${field} was not displayed as escaped text`);
  assert.equal(JSON.stringify(data),before,'Rendering must not alter the contract payload');
});
test('uploaded filename is text in review, list, and quoted accessibility labels',()=>{
  const name=payload+'.pdf',x=setup({},[{name,size:100,type:'other',base64:'JVBERg=='}]);
  x.buildReview();x.renderUploadedDocsList();
  for(const id of ['reviewSummary','uploadedDocsList']){
    assert.ok(!x.nodes[id].innerHTML.includes('<img'));
    assert.ok(x.nodes[id].innerHTML.includes(escaped+'.pdf'));
  }
  assert.ok(x.nodes.uploadedDocsList.innerHTML.includes('aria-label="Remove '+escaped+'.pdf"'));
});
test('missing attachment notice uses the available global escaping helper',()=>{
  const x=setup({uploadedDocNames:[payload+'.pdf']});x.renderUploadedDisclosureResumeNotice();
  assert.ok(x.nodes.uploadedDocsResumeNotice.innerHTML.includes(escaped+'.pdf'));
  assert.ok(!x.nodes.uploadedDocsResumeNotice.innerHTML.includes('<img'));
});
test('ordinary punctuation, Unicode, and literal entities survive without mutating data',()=>{
  const name='O\'Brien & García <Trust> "North" &amp;',x=setup({buyer1:name});
  x.buildReview();assert.ok(x.nodes.reviewSummary.innerHTML.includes('O\'Brien &amp; García &lt;Trust&gt; &quot;North&quot; &amp;amp;'));
  assert.equal(x.state.data.buyer1,name);
});
test('full non-realty description is preserved and safely escaped',()=>{
  const x=setup({nonRealtyItems:'yes',nonRealtyDescription:'x'.repeat(119)+'<&tail'});x.buildReview();
  assert.ok(x.nodes.reviewSummary.innerHTML.includes('x'.repeat(119)+'&lt;&amp;tail'));
  assert.ok(!x.nodes.reviewSummary.innerHTML.includes('…'));
});
test('blank placeholders, numeric formatting, and addendum markup remain intact',()=>{
  const x=setup({price:350000,earnest:0,financing:'conventional'});x.buildReview();
  const out=x.nodes.reviewSummary.innerHTML;
  assert.ok(out.includes('Not entered</span>'));assert.ok(out.includes('$350,000'));
  assert.ok(out.includes('$0'));assert.ok(out.includes('class="addendum-tag ">✓ Third Party Financing Addendum'));
});
test('active repairs are shown in full, safely, without altering agreed text',()=>{
  const repairs='Repair the window.\n'+payload+'\n'+'Keep every agreed detail. '.repeat(20);
  const x=setup({asIs:'repairs',repairsText:repairs});x.buildReview();
  assert.ok(x.nodes.reviewSummary.innerHTML.includes(x.escapeAttr(repairs)));
  assert.ok(x.nodes.reviewSummary.innerHTML.includes('review-row review-long-text'));
  assert.ok(!x.nodes.reviewSummary.innerHTML.includes('<img'));
  assert.equal(x.state.data.repairsText,repairs);
});
test('inactive repair text is not presented as an agreed requirement',()=>{
  const x=setup({asIs:'yes',repairsText:'Old repair answer'});x.buildReview();
  assert.ok(!x.nodes.reviewSummary.innerHTML.includes('Old repair answer'));
  assert.ok(!x.nodes.reviewSummary.innerHTML.includes('Required repairs or treatments'));
});
test('missing required repair text is visibly marked rather than hidden',()=>{
  const x=setup({asIs:'repairs',repairsText:''});x.buildReview();
  assert.match(x.nodes.reviewSummary.innerHTML,/Required repairs or treatments<\/span><span class="rv"><span[^>]*>Not entered/);
});
test('possession uses readable choices and never renders an unknown internal value',()=>{
  for(const [value,label] of Object.entries({closing:'Upon closing and funding',funding:'Upon closing and funding',
      buyerTemporaryLease:'Buyer occupies temporarily before closing',sellerTemporaryLease:'Seller remains temporarily after closing'})){
    const x=setup({possession:value});x.buildReview();
    assert.ok(x.nodes.reviewSummary.innerHTML.includes(`<span class="rl">Possession</span><span class="rv">${label}</span>`));
  }
  const x=setup({possession:payload});x.buildReview();
  assert.doesNotMatch(x.nodes.reviewSummary.innerHTML,/<img|onerror/);
  assert.match(x.nodes.reviewSummary.innerHTML,/Possession<\/span><span class="rv"><span[^>]*>Not entered/);
  assert.equal(x.state.data.possession,payload);
});
test('seller lease review includes its complete terms and correct simultaneous signing scope',()=>{
  const data={possession:'sellerTemporaryLease',sellerTemporaryLeaseTerminationDate:'2026-10-20',
    sellerTemporaryLeaseRentPerDay:'125.50',sellerTemporaryLeaseDeposit:'1,000',
    sellerTemporaryLeaseUtilitiesPaidByBuyer:'Water & trash',sellerTemporaryLeasePetsAllowed:'One dog',
    sellerTemporaryLeaseHoldoverPerDay:'300',sellerTemporaryLeaseSpecialProvisions:'Keep every detail. '.repeat(30)+payload};
  const x=setup(data);x.buildReview();const out=x.nodes.reviewSummary.innerHTML;
  for(const term of ['2026-10-20','$125.5','$1,000','Water &amp; trash','One dog','$300',x.escapeAttr(data.sellerTemporaryLeaseSpecialProvisions)]) assert.ok(out.includes(term),term);
  assert.match(out,/✓ Seller's Temporary Residential Lease/);
  assert.match(x.nodes.reviewSigningExpectation.textContent,/invitations together for the purchase contract, seller's temporary lease/);
  assert.doesNotMatch(x.nodes.reviewSigningExpectation.textContent,/remain with/);
});
test('buyer lease review shows before-closing terms and does not promise new seller invitations',()=>{
  const x=setup({possession:'buyerTemporaryLease',buyerTemporaryLeaseStartDate:'2026-10-01',
    buyerTemporaryLeaseRentPerDay:'0',buyerTemporaryLeaseTotalRent:'0',buyerTemporaryLeaseDeposit:0,
    buyerTemporaryLeaseUtilitiesPaidBySeller:'Electricity',buyerTemporaryLeasePetsAllowed:'No pets',
    buyerTemporaryLeaseHoldoverPerDay:'200',sellerTemporaryLeaseSpecialProvisions:'STALE_SELLER_LEASE'});
  x.buildReview();const out=x.nodes.reviewSummary.innerHTML;
  assert.match(out,/Buyer occupies temporarily before closing/);
  assert.match(out,/Lease start date<\/span><span class="rv">2026-10-01/);
  assert.match(out,/Total rent<\/span><span class="rv">\$0/);
  assert.match(out,/Security deposit<\/span><span class="rv">\$0/);
  assert.match(out,/✓ Buyer's Temporary Residential Lease/);
  assert.doesNotMatch(out,/STALE_SELLER_LEASE/);
  assert.match(x.nodes.reviewSigningExpectation.textContent,/Seller acceptance and seller-side signatures remain with/);
});
test('switching away from a temporary lease removes stale lease terms without deleting answers',()=>{
  const data={possession:'sellerTemporaryLease',sellerTemporaryLeaseSpecialProvisions:'PRIOR_LEASE_TERM'};
  const x=setup(data);x.buildReview();assert.match(x.nodes.reviewSummary.innerHTML,/PRIOR_LEASE_TERM/);
  data.possession='funding';x.buildReview();
  assert.doesNotMatch(x.nodes.reviewSummary.innerHTML,/PRIOR_LEASE_TERM|Lease special provisions<\/span>/);
  assert.equal(data.sellerTemporaryLeaseSpecialProvisions,'PRIOR_LEASE_TERM');
});
test('every displayed lease text field is escaped and data remains unchanged',()=>{
  for(const prefix of ['buyerTemporaryLease','sellerTemporaryLease']){
    for(const suffix of ['StartDate','TerminationDate','UtilitiesPaidByBuyer','UtilitiesPaidBySeller','PetsAllowed','SpecialProvisions']){
      if(prefix==='buyerTemporaryLease'&&['TerminationDate','UtilitiesPaidByBuyer'].includes(suffix))continue;
      if(prefix==='sellerTemporaryLease'&&['StartDate','UtilitiesPaidBySeller'].includes(suffix))continue;
      const data={possession:prefix,[prefix+suffix]:payload};const before=JSON.stringify(data);
      const x=setup(data);x.buildReview();
      assert.ok(x.nodes.reviewSummary.innerHTML.includes(escaped),prefix+suffix);
      assert.ok(!x.nodes.reviewSummary.innerHTML.includes('<img'));
      assert.equal(JSON.stringify(data),before);
    }
  }
});
test('invalid or missing lease amounts never show NaN or a made-up zero',()=>{
  const x=setup({possession:'buyerTemporaryLease',buyerTemporaryLeaseRentPerDay:'invalid',
    buyerTemporaryLeaseTotalRent:'',buyerTemporaryLeaseDeposit:null});x.buildReview();
  const out=x.nodes.reviewSummary.innerHTML;assert.doesNotMatch(out,/NaN|\$0/);
  for(const label of ['Daily rent','Total rent','Security deposit']){
    assert.ok(out.includes(label+'</span><span class="rv"><span style="color:var(--warn);font-size:0.8rem;">Not entered'));
  }
});
function packageTags(ctx){
  return [...ctx.nodes.reviewSummary.innerHTML.matchAll(/<span class="addendum-tag[^\"]*">([^<]+)<\/span>/g)].map(match=>match[1]);
}
test('a cash-only packet shows its contract without irrelevant addenda',()=>{
  const x=setup({financing:'cash',hoa:'no',nonRealtyItems:'no'});x.buildReview();
  assert.deepEqual(packageTags(x),['✓ TREC 1–4 Family Residential Contract']);
  assert.doesNotMatch(x.nodes.reviewSummary.innerHTML,/addendum-tag na|Lead-Based Paint — flag/);
});
test('district and lead reminders cannot claim a document is attached',()=>{
  for(const choice of ['yes','unknown']){
    const x=setup({mud:choice,leadBuiltBefore1978:choice,leadDisclosureStatus:'received'});x.buildReview();
    assert.deepEqual(packageTags(x),['✓ TREC 1–4 Family Residential Contract']);
    assert.match(x.nodes.reviewSummary.innerHTML,/MUD \/ PID notices/);
    assert.match(x.nodes.reviewSummary.innerHTML,/Upload notices to include them in this package/);
    assert.match(x.nodes.reviewSummary.innerHTML,/Buyer has received it/);
  }
  assert.doesNotMatch(html,/I'm not sure — include disclosure to be safe/);
});
test('an uploaded notice appears as an upload, not as an automatically generated disclosure',()=>{
  const x=setup({mud:'yes',leadBuiltBefore1978:'yes'},[{name:'Provided district notice.pdf',base64:'JVBERg=='}]);x.buildReview();
  assert.deepEqual(packageTags(x),['✓ TREC 1–4 Family Residential Contract','✓ Uploaded documents']);
  assert.match(x.nodes.reviewSummary.innerHTML,/Provided district notice.pdf/);
});
test('appraisal eligibility matches current packet financing choices and drops stale selections',()=>{
  for(const financing of ['cash','fha','va','conventional','usda']){
    for(const appraisalAddendum of ['none','waiver','partial','additional','unknown']){
      const x=setup({financing,appraisalAddendum});x.buildReview();
      const expected=['conventional','usda'].includes(financing)&&['waiver','partial','additional'].includes(appraisalAddendum);
      assert.equal(packageTags(x).includes('✓ Appraisal Addendum'),expected,financing+' '+appraisalAddendum);
      assert.equal(x.nodes.reviewSummary.innerHTML.includes('<span class="rl">Appraisal Addendum</span>'),expected);
    }
  }
});
test('non-realty list retains final model numbers, line breaks, and zero consideration',()=>{
  const description='Kitchen refrigerator & laundry appliances.\n'+'Serial XYZ123; '.repeat(30)+'FINAL ITEM: patio table <oak>';
  const data={nonRealtyItems:'yes',nonRealtyAmount:0,nonRealtyDescription:description};
  const x=setup(data);x.buildReview();
  assert.ok(x.nodes.reviewSummary.innerHTML.includes('$0 · '+x.escapeAttr(description)));
  assert.ok(packageTags(x).includes('✓ Non-Realty Items'));
  assert.equal(data.nonRealtyDescription,description);
  data.nonRealtyItems='no';x.buildReview();
  assert.doesNotMatch(x.nodes.reviewSummary.innerHTML,/FINAL ITEM/);
  assert.ok(!packageTags(x).includes('✓ Non-Realty Items'));
});
test('missing non-realty description remains visible without falsely listing an included addendum',()=>{
  const x=setup({nonRealtyItems:'yes',nonRealtyDescription:''});x.buildReview();
  assert.match(x.nodes.reviewSummary.innerHTML,/Non-Realty Items<\/span><span class="rv">No separate amount · <span[^>]*>Not entered/);
  assert.ok(!packageTags(x).includes('✓ Non-Realty Items'));
});
test('selected addenda stay in the clean package list',()=>{
  const x=setup({financing:'conventional',appraisalAddendum:'waiver',hoa:'yes',saleContingency:'yes',
    backupOffer:'yes',nonRealtyItems:'yes',nonRealtyDescription:'Refrigerator',leaseResidential:'yes',
    leaseFixture:'yes',possession:'sellerTemporaryLease'});x.buildReview();
  assert.deepEqual(packageTags(x),['✓ TREC 1–4 Family Residential Contract','✓ Third Party Financing Addendum',
    '✓ Appraisal Addendum','✓ HOA Addendum','✓ Sale of Other Property','✓ Back-Up Contract',
    '✓ Non-Realty Items','✓ Residential Lease Addendum','✓ Fixture Lease Addendum',"✓ Seller's Temporary Residential Lease"]);
});
test('blank non-realty consideration remains distinct from an explicit zero',()=>{
  for(const amount of ['',null,undefined,0,'0']){
    const x=setup({nonRealtyItems:'yes',nonRealtyDescription:'Refrigerator',nonRealtyAmount:amount});x.buildReview();
    const expected=amount===0||amount==='0'?'$0':'No separate amount';
    assert.ok(x.nodes.reviewSummary.innerHTML.includes(expected+' · Refrigerator'));
    assert.equal(x.state.data.nonRealtyAmount,amount);
  }
});
