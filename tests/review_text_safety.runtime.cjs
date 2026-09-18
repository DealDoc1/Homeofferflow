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
const fields=['buyer1','buyer2','seller','buyerPhone','buyerEmail','buyerMailAddr','address','city','zip','county','lotNumber','blockNumber','subdivision','legalDescription','optionDays','financing','appraisalTerminateDays','nonRealtyDescription','disclosureDays','closingDate','possession','titleCompany','agentName','agentBrokerage','brokerFeePercent'];
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
test('description is truncated before escaping so entities remain intact',()=>{
  const x=setup({nonRealtyItems:'yes',nonRealtyDescription:'x'.repeat(119)+'<&tail'});x.buildReview();
  assert.ok(x.nodes.reviewSummary.innerHTML.includes('x'.repeat(119)+'&lt;…'));
});
test('blank placeholders, numeric formatting, and addendum markup remain intact',()=>{
  const x=setup({price:350000,earnest:0,financing:'conventional'});x.buildReview();
  const out=x.nodes.reviewSummary.innerHTML;
  assert.ok(out.includes('Not entered</span>'));assert.ok(out.includes('$350,000'));
  assert.ok(out.includes('$0'));assert.ok(out.includes('class="addendum-tag ">✓ Third Party Financing Addendum'));
});
