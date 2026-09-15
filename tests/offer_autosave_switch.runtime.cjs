const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict'), {test}=require('node:test');
const root=path.join(__dirname,'..');
const html=process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git',['show',process.env.HOF_TEST_SOURCE_REF+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024})
  : fs.readFileSync(path.join(root,'index.html'),'utf8');
const source=(start,end)=>html.slice(html.indexOf(start),html.indexOf(end,html.indexOf(start)));
const saveSource=source('  function cleanOfferDraftData(', '  function setFeedbackStatus(');

function setup(initialId='offer-a') {
  const calls=[], notices=[];
  const pending=[];
  const context=vm.createContext({
    state:{data:{_hofOfferId:initialId,userType:'agent',buyer1:'Buyer A',buyerEmail:'a@example.test',address:'Property A',price:100000}},
    hofAuth:{session:{user:{id:'owner'}}},__hofCloudDraftSaveNeedsCopy:false,
    collectAllData(){},collectData(){},getVal:()=>'',getRadio:()=>'',moneyNumber:v=>Number(v)||0,
    updateSaveStatus:v=>notices.push(v),console:{warn(){}},
    getSupabaseClient:()=>({from:()=>{
      const call={kind:'read',filters:[]};
      const chain={select:()=>chain,eq:(...args)=>{call.filters.push(args);return chain;},is:()=>chain,
        update:body=>{call.kind='update';call.body=body;return chain;},insert:body=>{call.kind='insert';call.body=body;return chain;},
        single:()=>{calls.push(call);return new Promise(resolve=>pending.push(resolve));}};
      return chain;
    }}),
  });
  vm.runInContext(saveSource,context);
  const switchOffer=()=>{context.state.data={_hofOfferId:'offer-b',userType:'agent',buyer1:'Buyer B',address:'Property B'};};
  // Await cross-context promise continuations before inspecting the next query.
  const release=async(value)=>{assert.ok(pending.length);pending.shift()(value);await new Promise(setImmediate);};
  return {context,calls,notices,switchOffer,release};
}
test('switch during the read cannot target the new offer with the old payload',async()=>{
  const x=setup(); const saving=x.context.saveOfferDraftToSupabase();
  x.switchOffer(); await x.release({data:{id:'offer-a',status:'Draft',last_updated:'version-a'}});
  const update=x.calls[1];
  assert.equal(update.kind,'update'); assert.ok(update.filters.some(([key,value])=>key==='id'&&value==='offer-a'));
  assert.equal(update.body.property_address,'Property A');
  await x.release({data:{id:'offer-a'}}); await saving;
  assert.equal(x.context.state.data._hofOfferId,'offer-b'); assert.deepEqual(x.notices,[]);
});
test('late insert completion cannot attach its record ID to another draft',async()=>{
  const x=setup(null); const saving=x.context.saveOfferDraftToSupabase();
  assert.equal(x.calls[0].kind,'insert'); x.switchOffer();
  await x.release({data:{id:'new-offer-a'}}); await saving;
  assert.equal(x.context.state.data._hofOfferId,'offer-b'); assert.deepEqual(x.notices,[]);
});
test('old prepared-packet response cannot put the newly opened offer into copy mode',async()=>{
  const x=setup(); const saving=x.context.saveOfferDraftToSupabase(); x.switchOffer();
  await x.release({data:{id:'offer-a',status:'Buyer Signed'}}); await saving;
  assert.equal(x.context.__hofCloudDraftSaveNeedsCopy,false); assert.equal(x.calls.length,1);
});
test('old protection error cannot put the newly opened offer into copy mode',async()=>{
  const x=setup(); const saving=x.context.saveOfferDraftToSupabase(); x.switchOffer();
  await x.release({error:{code:'55000'}}); await saving;
  assert.equal(x.context.__hofCloudDraftSaveNeedsCopy,false);
});
test('account switch also prevents adopting an old save result',async()=>{
  const x=setup(null); const saving=x.context.saveOfferDraftToSupabase();
  x.context.hofAuth.session.user.id='another-account';
  await x.release({data:{id:'new-offer-a'}}); await saving;
  assert.equal(x.context.state.data._hofOfferId,null); assert.deepEqual(x.notices,[]);
});
test('ordinary same-offer saves still adopt the saved record',async()=>{
  const x=setup(null); const saving=x.context.saveOfferDraftToSupabase();
  await x.release({data:{id:'new-offer-a'}}); await saving;
  assert.equal(x.context.state.data._hofOfferId,'new-offer-a'); assert.equal(x.notices.length,1);
});
test('account switch during a read cannot start a write with a different session',async()=>{
  const x=setup(); const saving=x.context.saveOfferDraftToSupabase();
  x.context.hofAuth.session={user:{id:'another-account'}};
  await x.release({data:{id:'offer-a',status:'Draft',last_updated:'version-a'}});
  assert.equal(x.calls.length,1); await saving; assert.deepEqual(x.notices,[]);
});
test('a delayed cloud-save toast cannot claim the newly opened offer was saved',async()=>{
  const notices=[], timers=[];
  const c=vm.createContext({state:{data:{_hofOfferId:'offer-a'}},hofAuth:{session:{user:{id:'owner'}}},
    __hofCloudDraftSaveInFlight:false,__hofCloudDraftSaveQueued:false,__hofSaveTimer:null,
    hasMeaningfulCloudDraft:()=>true, saveOfferDraftToSupabase:async()=>({id:'offer-a'}),
    clearTimeout(){},setTimeout:fn=>{timers.push(fn);return 1;},updateSaveStatus:m=>notices.push(m),showCloudSaveFailure:()=>notices.push('failed')});
  vm.runInContext(source('  async function syncCloudDraftSave()', '  function getDraftSnapshot()'),c);
  await c.syncCloudDraftSave(); c.state.data={_hofOfferId:'offer-b'};
  timers.forEach(fn=>fn()); assert.deepEqual(notices,[]);
});
