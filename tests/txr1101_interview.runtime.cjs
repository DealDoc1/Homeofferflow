const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{test}=require('node:test');
const file=path.join(__dirname,'../assets/txr1101-interview.js');
const source=fs.readFileSync(file,'utf8'),model=require(file);
const leadDefaults={lead_knowledge:'unanswered',lead_records:'unanswered',lead_knowledge_details:'',lead_records_details:''};
const values=(changes={})=>{
  const data={seller_one:'QA Seller',seller_two:'',property_address:'100 Fictional Lane',term_start:'2026-10-17',term_end:'2027-04-17',listing_price:'350,000',
    fee_basis:'percentage',fee_amount:'2.5',additional_fee_basis:'none',mls_filing:'standard',internet_display:'full',hoa:'no',foreign_person:'unanswered',financing:[],addenda:[],...changes};
  return {get:key=>data[key]??'',getAll:key=>[...(data[key]||[])]};
};
test('maps only supported legal answer keys and does not copy account IDs or internal controls',()=>{
  const result=model.collect(values({agent_user_id:'untrusted',brokerage_id:'untrusted',built_before_1978:'no'}));
  assert.deepEqual(result.clientNames,['QA Seller']);assert.equal(result.agreementData.listing_price,'350000');
  for(const key of ['agent_user_id','brokerage_id','seller_one','_for_signing'])assert.ok(!(key in result.agreementData));
  assert.equal(result.agreementData.built_before_1978,'no');
});
test('explicit zero is retained, and no percentage is chosen by the mapper',()=>{
  assert.equal(model.collect(values({fee_amount:'0'})).agreementData.fee_amount,'0');
  assert.equal(model.collect(values({fee_amount:''})).agreementData.fee_amount,'');
});
test('an explicitly selected disclosure reopens by saved ID without copying its answers',()=>{
 const id='22222222-2222-4222-8222-222222222222';
 assert.equal(model.collect(values({disclosure_draft_id:id})).agreementData.disclosure_draft_id,id);
 assert.equal(model.collect(values()).agreementData.disclosure_draft_id,undefined);
 assert.equal(model.prefill(null,{client_names:['QA Seller'],agreement_data:{disclosure_draft_id:id}}).disclosure_draft_id,id);
 assert.ok(source.includes('data-water="${d.includesWaterRights'));
});
test('unselected compensation and MLS delay values cannot leak from a previous branch',()=>{
  const a=model.collect(values({fee_basis:'none',fee_amount:'9',other_compensation:'Agreed terms',additional_fee_amount:'150',mls_filing:'none',internet_display:'hide_address',mls_delay_days:'10',mls_delay_purpose:'Old choice'})).agreementData;
  assert.equal(a.fee_amount,'');assert.equal(a.additional_fee_amount,'');assert.equal(a.mls_delay_days,'');assert.equal(a.mls_delay_purpose,'');assert.equal(a.internet_display,'not_applicable');
});
test('known pre-1978 construction selects the lead document once, unknown age does not',()=>{
  assert.deepEqual(model.collect(values({built_before_1978:'yes',addenda:['A','C']})).agreementData.addenda,['A','C']);
  assert.deepEqual(model.collect(values({built_before_1978:''})).agreementData.addenda,[]);
  assert.deepEqual(model.collect(values({built_before_1978:'no'})).agreementData.addenda,[]);
});
test('association membership alone does not infer an information request',()=>{
  assert.deepEqual(model.collect(values({hoa:'yes'})).agreementData.addenda,[]);
  assert.deepEqual(model.collect(values({hoa:'yes',request_hoa_information:'yes'})).agreementData.addenda,['G']);
});
test('tax status remains unanswered, and identical legal names are not merged',()=>{
  const result=model.collect(values({seller_two:'QA Seller'}));
  assert.deepEqual(result.clientNames,['QA Seller','QA Seller']);assert.equal(result.agreementData.foreign_person,'unanswered');
});
test('prefill reuses only selected workspace seller/property data, not fabricated terms',()=>{
  const result=model.prefill({property_address:'100 QA Lane',seller_names:['José 李','Zoë QA'],listing_price:'999999'});
  assert.deepEqual(result,{property_address:'100 QA Lane',seller_one:'José 李',seller_two:'Zoë QA',...leadDefaults});
  assert.ok(!('fee_amount' in result));
});
test('editing rehydrates saved answers rather than a different selected workspace',()=>{
  assert.deepEqual(model.prefill({property_address:'Wrong house'},{client_names:['Saved Seller'],agreement_data:{property_address:'Saved house',fee_amount:'0'}}),
    {property_address:'Saved house',fee_amount:'0',seller_one:'Saved Seller',seller_two:'',...leadDefaults});
});
test('lead answers default to Seller completion, and saved explicit facts survive reopening',()=>{
  const blank=model.collect(values()).agreementData.lead_disclosure;
  assert.deepEqual(blank,{knowledge:'unanswered',records:'unanswered',knowledge_details:'',records_details:''});
  const supplied=model.collect(values({lead_knowledge:'known',lead_records:'provided',lead_knowledge_details:'Seller supplied QA fact',lead_records_details:'QA report'}));
  const opened=model.prefill(null,{client_names:['QA Seller'],agreement_data:supplied.agreementData});
  assert.equal(opened.lead_knowledge,'known');assert.equal(opened.lead_records_details,'QA report');
});
test('new agreements reuse office defaults but a saved snapshot, including blanks, always wins',()=>{
  const context={noticeContacts:{address:'10 Current Office',email:'current@example.test'}};
  assert.equal(model.prefill(null,null,context).broker_notice_address,'10 Current Office');
  const saved={client_names:['Seller'],agreement_data:{broker_notice_contacts:{address:'42 Saved Office',email:''}}};
  const edit=model.prefill(null,saved,context);
  assert.equal(edit.broker_notice_address,'42 Saved Office');assert.equal(edit.broker_notice_email,'');
});
test('brokerage notice contacts are bounded legal answers, not a broker signer or an account update',()=>{
  const a=model.collect(values({broker_notice_address:'42 QA Lane',broker_notice_email:'notices@example.test',broker_notice_name:'Untrusted name'})).agreementData;
  assert.equal(a.broker_notice_contacts.address,'42 QA Lane');assert.equal(a.broker_notice_contacts.email,'notices@example.test');
  assert.ok(!('name' in a.broker_notice_contacts));assert.ok(!('broker_signer' in a));assert.ok(!('broker_notice_name' in a));
});
test('validates chronology, explicit compensation and delayed MLS purpose',()=>{
  assert.equal(model.validateTerms(model.collect(values())), '');
  assert.match(model.validateTerms(model.collect(values({term_end:'2026-01-01'}))),/end date/);
  assert.match(model.validateTerms(model.collect(values({fee_basis:'none',other_compensation:''}))),/agreed compensation/);
  assert.match(model.validateTerms(model.collect(values({fee_amount:'1e2'}))),/compensation/);
  assert.match(model.validateTerms(model.collect(values({fee_amount:'100.0001'}))),/compensation/);
  assert.match(model.validateTerms(model.collect(values({mls_filing:'delayed',mls_delay_days:'0'}))),/delay/);
});
function deferred(){let resolve,reject;const promise=new Promise((y,n)=>{resolve=y;reject=n;});return {resolve,reject,promise};}
function openingSetup(holdOffice=false){
  const sourceRead=deferred(),officeRead=deferred(),requests=[],officeRequests=[];
  const root={hofAuth:{role:'agent',session:{user:{id:'agent-a'},access_token:'qa-token'}},
    document:{getElementById:()=>null,createElement:()=>{throw new Error('No stale modal should be created');}},
    hofLoadApprovedBrokerageSource:()=>sourceRead.promise,
    fetch:(url,options)=>{
      if(url.includes('scope=txr1101_context')){officeRequests.push({url,options});return holdOffice?officeRead.promise:Promise.resolve({ok:true,status:200,json:async()=>({brokerage:{},noticeContacts:{}})});}
      const result=deferred();requests.push({url,options,...result});return result.promise;}};
  vm.runInNewContext(source,{window:root});return {root,requests,sourceRead,officeRead,officeRequests};
}
test('source load rejection remains visible to the existing guided handoff',async()=>{
  const x=openingSetup(),pending=x.root.hofOpenTxr1101Draft();x.sourceRead.reject(new Error('QA outage'));
  await assert.rejects(pending,/QA outage/);
});
test('a cross-account source response cannot open the old seller interview',async()=>{
  const x=openingSetup(),pending=x.root.hofOpenTxr1101Draft();x.root.hofAuth.session.user.id='agent-b';
  x.sourceRead.resolve({id:'qa-source'});await pending;
});
test('same-user new session epoch also invalidates an old source response',async()=>{
  const x=openingSetup(),pending=x.root.hofOpenTxr1101Draft();x.root.__hofAccountProfileEpoch=1;
  x.sourceRead.resolve({id:'qa-source'});await pending;
});
test('late office defaults cannot open an interview after the account changes',async()=>{
  const x=openingSetup(true),pending=x.root.hofOpenTxr1101Draft();x.sourceRead.resolve({id:'source'});
  x.root.hofAuth.session.user.id='agent-b';x.officeRead.resolve({ok:true,json:async()=>({noticeContacts:{address:'Old office'}})});await pending;
  assert.equal(x.officeRequests[0].options.cache,'no-store');assert.equal(x.officeRequests[0].options.headers.Authorization,'Bearer qa-token');
});
test('the optional office-default loader falls back to manual entry but preserves an expired-session error',async()=>{
  const start=source.indexOf('  async function loadOfficeContext()'),end=source.indexOf('  async function openInterview(',start);
  const root={hofAuth:{session:{access_token:'qa-token'}},fetch:async()=>{throw new Error('Synthetic optional defaults outage');}};
  const c=vm.createContext({root});vm.runInContext(source.slice(start,end)+'this.load=loadOfficeContext;',c);
  const fallback=await c.load();assert.equal(fallback.unavailable,true);
  root.fetch=async()=>({ok:false,status:401});await assert.rejects(c.load(),error=>error.requiresSignIn===true);
});
test('double open while loading uses one source lookup',async()=>{
  const x=openingSetup();let count=0;x.root.hofLoadApprovedBrokerageSource=()=>{count++;return x.sourceRead.promise;};
  const first=x.root.hofOpenTxr1101Draft(),second=x.root.hofOpenTxr1101Draft();
  x.root.hofAuth.session.user.id='agent-b';x.sourceRead.resolve({id:'source'});await Promise.all([first,second]);assert.equal(count,1);
});
test('saved draft read is authenticated, uncached and discarded after account change',async()=>{
  const x=openingSetup(),pending=x.root.hofOpenTxr1101Draft({agreementId:'qa/id'});
  assert.match(x.requests[0].url,/scope=txr1101_draft&agreement_id=qa%2Fid/);
  assert.equal(x.requests[0].options.headers.Authorization,'Bearer qa-token');assert.equal(x.requests[0].options.cache,'no-store');
  x.root.hofAuth.session.user.id='agent-b';x.requests[0].resolve({ok:true,json:async()=>({agreement:{id:'qa'}})});await pending;
});
test('no brokerage seat is required to reach an independent agent source lookup',async()=>{
  const x=openingSetup(),pending=x.root.hofOpenTxr1101Draft();x.sourceRead.reject(new Error('Source requested without a seat'));
  await assert.rejects(pending,/without a seat/);
});

// Execute the real submit callback with a minimal DOM boundary. Browser QA
// separately checks native controls, conditional panels and responsive layout.
function submittingSetup(){
  const start=source.indexOf("    form.addEventListener('submit',async event => {"),end=source.indexOf('    showStep();\n  }',start);
  assert.ok(start>0&&end>start);
  const requests=[],controls=[{disabled:false},{disabled:false}],listeners={};
  const buttons={};const status={className:'',textContent:'',innerHTML:'',querySelector:key=>buttons[key]||(buttons[key]={addEventListener:(event,fn)=>{listeners[event]=fn;}}),appendChild:()=>{}};
  const save={disabled:false,textContent:'Prepare agreement',setAttribute(){}},back={disabled:false};
  let submit;
  const form={addEventListener:(_,fn)=>{submit=fn;},querySelectorAll:()=>controls};
  const modal={isConnected:true,remove(){this.isConnected=false;}};
  const root={hofAuth:{session:{user:{id:'actor'},access_token:'qa-token'}},FormData:class{get(key){return values().get(key);}getAll(key){return values().getAll(key);}},
    fetch:(url,options)=>{const pending=deferred();requests.push({url,options,...pending});return pending.promise;}};
  const context=vm.createContext({root,form,modal,status,save,back,document:{createElement:()=>({addEventListener(){}})},
    current:()=>root.hofAuth.session.user.id==='actor',actor:{id:'actor'},approved:{id:'source'},collect:model.collect,validateTerms:model.validateTerms,
    validActor:()=>{if(root.hofAuth.session.user.id==='actor')return true;modal.remove();return false;},invalidStep:()=>false,reviewSaved:()=>{},sync:()=>{},step:5,busy:false,uncertain:false,saved:null,FORM_CODE:'TXR-1101'});
  vm.runInContext(source.slice(start,end),context);
  return {submit:()=>submit({preventDefault(){}}),requests,root,save,status,modal,context,
    reply:(index,body,statusCode=200)=>requests[index].resolve({ok:statusCode<300,status:statusCode,json:async()=>body})};
}
test('submit freezes answers, suppresses duplicate taps, and saves subsequent edits to the same versioned draft',async()=>{
  const x=submittingSetup(),first=x.submit();await x.submit();assert.equal(x.requests.length,1);assert.equal(x.save.disabled,true);
  x.reply(0,{agreement:{id:'saved-id',updated_at:'version-1'}});await first;
  assert.equal(x.status.className,'hof-iabs-status ready');assert.equal(x.save.disabled,false);
  const next=x.submit(),body=JSON.parse(x.requests[1].options.body);
  assert.equal(body.action,'update_txr_1101_draft');assert.equal(body.agreementId,'saved-id');assert.equal(body.updatedAt,'version-1');
  x.reply(1,{agreement:{id:'saved-id',updated_at:'version-2'}});await next;assert.equal(x.requests.length,2);
});
for(const kind of ['network','conflict','server-error','missing-readback'])test(`uncertain ${kind} save requires checking the queue instead of another create`,async()=>{
  const x=submittingSetup(),pending=x.submit();
  if(kind==='network')x.requests[0].reject(new Error('Synthetic connection loss'));
  else if(kind==='missing-readback')x.reply(0,{agreement:{id:'saved-id'}});
  else x.reply(0,{refreshRequired:kind==='conflict'},kind==='conflict'?409:500);
  await pending;await x.submit();assert.equal(x.requests.length,1);assert.equal(x.save.disabled,true);assert.match(x.status.textContent,/Check your saved documents/);
});
test('a known validation rejection retains answers and permits a deliberate retry',async()=>{
  const x=submittingSetup(),pending=x.submit();x.reply(0,{error:'Check the listing dates.'},400);await pending;
  assert.equal(x.save.disabled,false);assert.equal(x.status.textContent,'Check the listing dates.');
  const retry=x.submit();assert.equal(x.requests.length,2);assert.equal(x.requests[1].options.body,x.requests[0].options.body);
  x.reply(1,{agreement:{id:'saved-id',updated_at:'version-1'}});await retry;
});
test('a save response cannot publish an old actor’s confirmation in a different account',async()=>{
  const x=submittingSetup(),pending=x.submit();x.root.hofAuth.session.user.id='different-actor';
  x.reply(0,{agreement:{id:'saved-id',updated_at:'version-1'}});await pending;
  assert.equal(x.modal.isConnected,false);assert.notEqual(x.status.className,'hof-iabs-status ready');
});
