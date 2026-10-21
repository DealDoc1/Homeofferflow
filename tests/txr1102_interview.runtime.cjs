const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{test}=require('node:test');
const model=require('../assets/txr1102-interview.js');
const shared=fs.readFileSync(path.join(__dirname,'../assets/txr1101-interview.js'),'utf8');
function values(changes={}){
  const data={seller_one:'QA Landlord One',seller_two:'QA Landlord Two',property_address:'100 Fictional Lane',
    listing_price:'2,500',lease_min_months:'12',lease_max_months:'24',term_start:'2026-11-01',term_end:'2027-03-01',
    fee_scope:'with_other_broker',fee_basis:'month_percentage',fee_amount:'100',cobroker_basis:'month_percentage',cobroker_amount:'50',
    renewal_basis:'total_percentage',renewal_amount:'2.5',sale_fee_basis:'percentage',sale_fee_amount:'3',
    mls_filing:'standard',internet_display:'full',keybox:'yes',hoa:'yes',intermediary:'authorized',make_ready:'not_authorized',
    signer_plan:'clients_and_associate',built_before_1978:'no',addenda:['A'],...changes};
  return {get:key=>data[key]??'',getAll:key=>data[key]||[]};
}
test('maps lease facts only, keeps explicit zero and leaves unconfirmed preferences unspecified',()=>{
  const result=model.collect(values({fee_amount:'0',cobroker_amount:'0',agent_user_id:'injected',foreign_person:'yes'}));
  assert.equal(result.agreementData.listing_price,'2500');assert.equal(result.agreementData.fee_amount,'0');
  assert.deepEqual(result.clientNames,['QA Landlord One','QA Landlord Two']);
  for(const key of ['agent_user_id','foreign_person','financing','client_names','seller_one'])assert.ok(!(key in result.agreementData));
  assert.equal(result.agreementData.include_rental_preferences,false);assert.equal(result.agreementData.animals,undefined);
});
test('all conditional core terms are cleared when their authority or fee basis changes',()=>{
  const a=model.collect(values({fee_scope:'broker_only',fee_basis:'other',fee_other:'Agreed fee terms',fee_amount:'9',
    renewal_other:'unused',sale_fee_other:'unused',mls_filing:'none',mls_delay_days:'5',mls_delay_purpose:'old',
    make_ready_limit:'500',make_ready_service_fee:'old'})).agreementData;
  assert.equal(a.fee_amount,'');assert.equal(a.cobroker_basis,'');assert.equal(a.cobroker_amount,'');
  assert.equal(a.renewal_other,'');assert.equal(a.sale_fee_other,'');assert.equal(a.internet_display,'not_applicable');
  assert.equal(a.mls_delay_days,'');assert.equal(a.make_ready_limit,'');assert.equal(a.make_ready_service_fee,'');
});
test('unknown age requests a lease lead document but never claims it is attached',()=>{
  assert.deepEqual(model.collect(values({built_before_1978:''})).agreementData.addenda,['A','B','C']);
  assert.deepEqual(model.collect(values({built_before_1978:'yes',addenda:['A','C','C']})).agreementData.addenda,['A','B','C']);
  assert.deepEqual(model.collect(values()).agreementData.addenda,['A','B']);
});
test('optional preference branches do not carry stale amounts, contacts or animal permissions',()=>{
  const a=model.collect(values({include_rental_preferences:'on',rent_due:'first',rent_due_other:'old',animals:'not_permitted',
    animal_deposit:'300',animal_restrictions:'old',animal_violation_initial:'100',yard:'tenant',yard_contractor:'old',
    pool:'landlord',pool_other:'old',pool_contractor:'old',initial_late_amount:'30'})).agreementData;
  assert.equal(a.rent_due_other,'');assert.equal(a.animal_deposit,'');assert.equal(a.animal_restrictions,'');
  assert.equal(a.animal_violation_initial,'100');assert.equal(a.yard_contractor,'');assert.equal(a.pool_other,'');
  assert.equal(a.initial_late_basis,'unspecified');assert.equal(a.initial_late_amount,'');
  const unchecked=model.collect(values({animal_deposit:'300',animals:'permitted'})).agreementData;
  assert.ok(!('animal_deposit' in unchecked));
});
test('saved snapshots, including blank office contacts and preference zeroes, override workspace defaults',()=>{
  const saved={client_names:['Saved Landlord'],agreement_data:{property_address:'Saved property',include_rental_preferences:true,
    security_deposit:'0',broker_notice_contacts:{address:'',email:''}}};
  const result=model.prefill({property_address:'Wrong property'},saved,{noticeContacts:{email:'new@example.test'}});
  assert.equal(result.property_address,'Saved property');assert.equal(result.seller_one,'Saved Landlord');
  assert.equal(result.include_rental_preferences,true);assert.equal(result.security_deposit,'0');
  assert.equal(result.broker_notice_email,'');assert.equal(result.broker_notice_address,'');
});
test('new workspaces supply identity and property, never unagreed fees or lease preferences',()=>{
  const a=model.prefill({property_address:'QA property',seller_names:['QA Landlord'],listing_price:'9999'});
  assert.equal(a.property_address,'QA property');assert.equal(a.seller_one,'QA Landlord');assert.deepEqual(a.addenda,['A','B']);
  assert.ok(!('listing_price' in a));assert.ok(!('fee_amount' in a));
});
test('current-step checks surface rent, chronology, negotiated fees and delay errors before proceeding',()=>{
  assert.equal(model.validateTerms(model.collect(values())), '');
  for(const changes of [{lease_min_months:'24',lease_max_months:'12'},{listing_price:'0'},{term_end:'2026-01-01'}]){
    const data=model.collect(values(changes));assert.ok(model.validateStep(data,1));assert.equal(model.validateStep(data,0),'');
  }
  assert.ok(model.validateTerms(model.collect(values({cobroker_amount:'101'}))));
  assert.equal(model.validateTerms(model.collect(values({fee_amount:'150',cobroker_amount:'125'}))), '');
  assert.ok(model.validateTerms(model.collect(values({mls_filing:'delayed',mls_delay_days:'5'}))));
  assert.ok(model.validateTerms(model.collect(values({include_rental_preferences:'on',initial_late_basis:'percentage',initial_late_amount:'101'}))));
});
test('related document labels match lease-specific source choices instead of the sale checklist',()=>{
  const labels=Object.fromEntries(model.documentChoices);
  assert.equal(labels.B,'Rental flood disclosure');assert.equal(labels.D,'Owners’ association information request');
  assert.equal(labels.K,'Assistance-animal information for landlords');
  assert.equal(labels.I,'IRS Form W-9 or W-8');
  const markup=model.markup({officeContext:{},officeIdentity:'QA Office',hasNoticeDetails:false});
  assert.match(markup,/name="seller_one"[^>]*maxlength="300"/);
  assert.match(markup,/name="seller_two"[^>]*maxlength="300"/);
});
test('review escapes data, retains negotiation bases and distinguishes requested documents from attachments',()=>{
  const payload=model.collect(values({property_address:'<img onerror=attack()>',built_before_1978:'unanswered'}));
  const html=model.review(payload,'<script>injected</script>');
  assert.ok(!html.includes('<img'));assert.ok(!html.includes('<script>'));
  assert.match(html,/Percentage of one month/);assert.match(html,/does not confirm attachments/);
});
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
function setup(){
  const requests=[],source=deferred(),root={hofLeaseListingInterview:model,
    document:{getElementById:()=>null,createElement:()=>{throw Error('A stale response cannot create a dialog.');}},
    hofAuth:{role:'agent',session:{user:{id:'qa-agent'},access_token:'qa-token'}},
    hofLoadApprovedBrokerageSource:code=>{root.requestedCode=code;return source.promise;},
    fetch:(url,options)=>{requests.push({url,options});return Promise.resolve({ok:true,json:async()=>url.includes('_context')?{noticeContacts:{}}:{agreement:{id:'saved'}}});}};
  vm.runInNewContext(shared,{window:root});return {root,requests,source};
}
test('lease opener loads only its form/source and context and drops a stale account response',async()=>{
  const x=setup(),pending=x.root.hofOpenTxr1102Draft();assert.equal(x.root.requestedCode,'TXR-1102');
  assert.match(x.requests[0].url,/scope=txr1102_context/);assert.equal(x.requests[0].options.cache,'no-store');
  x.root.hofAuth.session.user.id='different-agent';x.source.resolve({id:'source'});await pending;
});
test('lease saved draft read uses its own authenticated scope, never the sale draft reader',async()=>{
  const x=setup(),pending=x.root.hofOpenTxr1102Draft({agreementId:'qa/id'});
  assert.match(x.requests[0].url,/scope=txr1102_draft&agreement_id=qa%2Fid/);
  assert.equal(x.requests[0].options.headers.Authorization,'Bearer qa-token');
  x.root.hofAuth.session.user.id='different-agent';await pending;
});
test('late source responses cannot cross same-user session epochs',async()=>{
  const x=setup(),pending=x.root.hofOpenTxr1102Draft();x.root.__hofAccountProfileEpoch=1;
  x.source.resolve({id:'source'});await pending;
});

module.exports={values};
