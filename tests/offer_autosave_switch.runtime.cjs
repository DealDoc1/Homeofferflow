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
    hofAuth:{session:{user:{id:'owner'},access_token:'test-token'}},__hofCloudDraftSaveNeedsCopy:false,
    collectAllData(){},collectData(){},getVal:()=>'',getRadio:()=>'',moneyNumber:v=>Number(v)||0,
    updateSaveStatus:v=>notices.push(v),console:{warn(){}},
    window:{hofSaveAgentOfferDraft:(offerId,offer)=>{
      calls.push({offerId,offer});
      return new Promise((resolve,reject)=>pending.push({resolve,reject}));
    }},
  });
  vm.runInContext(saveSource,context);
  const switchOffer=()=>{context.state.data={_hofOfferId:'offer-b',userType:'agent',buyer1:'Buyer B',address:'Property B'};};
  // Await cross-context promise continuations before inspecting the result.
  const release=async(value)=>{assert.ok(pending.length);pending.shift().resolve(value);await new Promise(setImmediate);};
  const fail=async(error)=>{assert.ok(pending.length);pending.shift().reject(error);await new Promise(setImmediate);};
  return {context,calls,notices,switchOffer,release,fail};
}
test('switch during the API save cannot apply its result to the new offer',async()=>{
  const x=setup(); const saving=x.context.saveOfferDraftToSupabase();
  assert.equal(x.calls[0].offerId,'offer-a'); assert.equal(x.calls[0].offer.property_address,'Property A');
  x.switchOffer(); await x.release({id:'offer-a',saved:true}); await saving;
  assert.equal(x.context.state.data._hofOfferId,'offer-b'); assert.deepEqual(x.notices,[]);
});
test('late insert completion cannot attach its record ID to another draft',async()=>{
  const x=setup(null); const saving=x.context.saveOfferDraftToSupabase();
  assert.equal(x.calls[0].offerId,null); x.switchOffer();
  await x.release({id:'new-offer-a',saved:true}); await saving;
  assert.equal(x.context.state.data._hofOfferId,'offer-b'); assert.deepEqual(x.notices,[]);
});
test('old prepared-packet response cannot put the newly opened offer into copy mode',async()=>{
  const x=setup(); const saving=x.context.saveOfferDraftToSupabase(); x.switchOffer();
  await x.release({id:'offer-a',saved:false,copyRequired:true}); await saving;
  assert.equal(x.context.__hofCloudDraftSaveNeedsCopy,false); assert.equal(x.calls.length,1);
});
test('old protection error cannot put the newly opened offer into copy mode',async()=>{
  const x=setup(); const saving=x.context.saveOfferDraftToSupabase(); x.switchOffer();
  const error=new Error('protected packet');error.code='55000'; await x.fail(error); await saving;
  assert.equal(x.context.__hofCloudDraftSaveNeedsCopy,false);
});
test('account switch also prevents adopting an old save result',async()=>{
  const x=setup(null); const saving=x.context.saveOfferDraftToSupabase();
  x.context.hofAuth.session.user.id='another-account';
  await x.release({id:'new-offer-a',saved:true}); await saving;
  assert.equal(x.context.state.data._hofOfferId,null); assert.deepEqual(x.notices,[]);
});
test('ordinary same-offer saves still adopt the saved record',async()=>{
  const x=setup(null); const saving=x.context.saveOfferDraftToSupabase();
  await x.release({id:'new-offer-a',saved:true}); await saving;
  assert.equal(x.context.state.data._hofOfferId,'new-offer-a'); assert.equal(x.notices.length,1);
});
test('account switch after the authorized save begins cannot adopt it in another session',async()=>{
  const x=setup(); const saving=x.context.saveOfferDraftToSupabase();
  x.context.hofAuth.session={user:{id:'another-account'}};
  await x.release({id:'offer-a',saved:true});
  assert.equal(x.calls.length,1); await saving; assert.deepEqual(x.notices,[]);
});
test('a cloud save that finishes after an offer switch cannot mark the new offer saved', async () => {
  const notices = [];
  let finishSave;
  const pendingSave = new Promise(resolve => { finishSave = resolve; });
  const context = vm.createContext({
    state: {data: {_hofOfferId: 'offer-a'}},
    hofAuth: {session: {user: {id: 'owner'}}},
    __hofCloudDraftSaveInFlight: false,
    __hofCloudDraftSaveQueued: false,
    hasMeaningfulCloudDraft: () => true,
    saveOfferDraftToSupabase: () => pendingSave,
    updateSaveStatus: message => notices.push(message),
    showCloudSaveFailure: () => notices.push('failed')
  });
  vm.runInContext(source('  async function syncCloudDraftSave()', '  function getDraftSnapshot()'), context);
  const saving = context.syncCloudDraftSave();
  context.state.data = {_hofOfferId: 'offer-b'};
  finishSave({id: 'offer-a'});
  await saving;
  assert.deepEqual(notices, []);
});
