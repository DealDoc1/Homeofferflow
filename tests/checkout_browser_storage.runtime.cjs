const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict'),{test}=require('node:test');
const root=path.resolve(__dirname,'..');
const html=process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git',['show',process.env.HOF_TEST_SOURCE_REF+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024})
  : fs.readFileSync(path.join(root,'index.html'),'utf8');
function source(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0&&b>a,start);return html.slice(a,b);}
function setup({quota=Infinity,blocked=false,readBlocked=false,silent=false,localFails=false}={}) {
  const store=new Map([['hofOfferData',JSON.stringify({address:'Previous property'})]]),events=[],requests=[],notices=[];
  const files=[{name:'survey.pdf',base64:'A'.repeat(32000),type:'survey',size:24000}];
  const button={disabled:false,textContent:'Pay $99 & Continue',style:{},setAttribute(){}};
  const email={value:'buyer@example.test',checkValidity:()=>true,setAttribute(){},focus(){}};
  const c=vm.createContext({state:{selectedPlan:'self',selectedPrice:99,data:{userType:'homebuyer',address:'Current property',price:450000,
    buyer1:'Current Buyer',buyerEmail:'buyer@example.test',repairsText:'José 🏡\u2028all debris removed',uploadedDocNames:['survey.pdf']}},
    window:{hofUploadedDisclosureDocs:files,location:{origin:'https://www.homeofferflow.test',pathname:'/',href:'original'}},
    document:{getElementById:id=>id==='payBtn'?button:id==='paymentEmail'?email:id==='oneTimePacketAck'?{checked:true}:null},
    console:{error(){}},collectAllData(){},confirmControlledLaunchSupport:()=>true,validateParagraph4LeaseInputs:()=>true,
    validateHydrostaticInputs:()=>true,validateMineralInputs:()=>true,validateEnvironmentalInputs:()=>true,validateAssumptionInputs:()=>true,validateSellerTemporaryLeaseInputs:()=>true,validateUploadedDisclosureDocs:()=>true,
    setPaymentStatus:message=>notices.push(message),trackEvent(){},
    saveDraftNow:()=>{events.push('local-save');if(localFails)throw Error('Local store unavailable');},
    saveDraft:()=>events.push('delayed-save'),
    sessionStorage:{setItem:(key,value)=>{events.push('session-save');if(blocked||value.length>quota)throw Error('QuotaExceededError');if(!silent)store.set(key,value);},
      getItem:key=>{if(readBlocked)throw Error('Read denied');return store.get(key)||null;}},
    fetch:async(url,options)=>{events.push('fetch');requests.push(JSON.parse(options.body));return{
      ok:true,headers:{get:()=> 'application/json'},json:async()=>({url:'https://checkout.example.test/current'})};},
    generateSubscribedPacket:()=>events.push('subscribed')
  });
  vm.runInContext(source('  function cleanOfferDraftData(', '  function offerHasPreparedPacket('),c);
  if(html.includes('  function cacheBuyerCheckoutSnapshot('))vm.runInContext(source('  function cacheBuyerCheckoutSnapshot(', '  async function handlePayment()'),c);
  vm.runInContext(source('  async function handlePayment()', '  async function generateSubscribedPacket()'),c);
  return {c,store,events,requests,notices,files,button};
}
test('normal checkout keeps same-tab files and sends the complete packet',async()=>{
  const x=setup();await x.c.handlePayment();
  assert.equal(x.requests.length,1);assert.equal(x.requests[0].offerData.uploadedDisclosureDocs[0].base64,x.files[0].base64);
  assert.equal(JSON.parse(x.store.get('hofOfferData')).uploadedDisclosureDocs[0].base64,x.files[0].base64);
  assert.equal(x.c.window.location.href,'https://checkout.example.test/current');
  assert.deepEqual(x.events,['session-save','local-save','fetch']);
});
test('full cache quota falls back to answers without dropping server-bound attachments',async()=>{
  const x=setup({quota:2000});await x.c.handlePayment();
  assert.equal(x.requests.length,1,'Browser quota must not block supported packet checkout');
  const saved=JSON.parse(x.store.get('hofOfferData'));
  assert.equal(saved.address,'Current property');assert.equal(saved.repairsText,x.c.state.data.repairsText);
  assert.deepEqual(saved.uploadedDocNames,['survey.pdf']);assert.equal(saved.uploadedDisclosureDocs,undefined);
  assert.equal(x.requests[0].offerData.uploadedDisclosureDocs[0].base64,x.files[0].base64);
  assert.equal(x.c.window.hofUploadedDisclosureDocs,x.files);assert.equal(x.events.at(-1),'fetch');
});
for(const options of [{blocked:true},{quota:0},{readBlocked:true},{silent:true}])test(`unconfirmed browser save keeps interview open: ${JSON.stringify(options)}`,async()=>{
  const x=setup(options);await x.c.handlePayment();
  assert.equal(x.requests.length,0);assert.equal(x.c.window.location.href,'original');assert.equal(x.button.disabled,false);
  assert.equal(x.c.state.data.address,'Current property');assert.equal(x.files[0].base64.length,32000);
  assert.ok(x.notices.some(message=>message.includes('Your answers are still here.')));
  assert.ok(!x.notices.some(message=>message.includes('QuotaExceededError')));
});
test('confirmed tab snapshot allows checkout even when optional local backup fails',async()=>{
  const x=setup({localFails:true});await x.c.handlePayment();assert.equal(x.requests.length,1);
});
test('retry after browser space is available keeps the original answers and files',async()=>{
  const x=setup({blocked:true});await x.c.handlePayment();assert.equal(x.requests.length,0);
  x.c.sessionStorage.setItem=(key,value)=>x.store.set(key,value);
  await x.c.handlePayment();assert.equal(x.requests.length,1);assert.equal(x.requests[0].offerData.address,'Current property');
  assert.equal(x.requests[0].offerData.uploadedDisclosureDocs[0].base64,x.files[0].base64);
});
test('compact fallback strips both attachment aliases without mutating the input',()=>{
  const x=setup({quota:2000}),offer={...x.c.state.data,uploadedDisclosureDocs:x.files,uploadedDocs:x.files,
    signwell:{private:'provider-state'},_paragraph4_source_pdf_bytes:'private-source'};
  const original=JSON.stringify(offer);
  assert.equal(x.c.cacheBuyerCheckoutSnapshot(offer),true);
  const saved=JSON.parse(x.store.get('hofOfferData'));
  for(const key of ['uploadedDocs','uploadedDisclosureDocs','signwell','_paragraph4_source_pdf_bytes'])assert.equal(saved[key],undefined);
  assert.equal(JSON.stringify(offer),original);
});
