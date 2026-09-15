const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const assert = require('node:assert/strict'), {test} = require('node:test');
const root = path.join(__dirname, '..');
const html = process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git', ['show', process.env.HOF_TEST_SOURCE_REF + ':index.html'], {cwd:root, encoding:'utf8', maxBuffer:8*1024*1024})
  : fs.readFileSync(path.join(root, 'index.html'), 'utf8');
function source(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert.ok(a >= 0 && b > a, start);
  return html.slice(a, b);
}
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => {resolve=yes; reject=no;});
  return {promise, resolve, reject};
}
const tick = () => new Promise(setImmediate);
const offer = (id, extra={}) => ({id, role:'agent', status:'Draft', offer_data:{buyer1:id, financing:'cash'}, ...extra});
function setup() {
  const reads=[], inserts=[], opened=[], alerts=[], logs=[];
  const c=vm.createContext({
    state:{data:{_hofOfferId:'initial', userType:'agent'}},
    hofAuth:{role:'agent',session:{user:{id:'owner'}}},
    getOfferById:id=>{const pending=deferred(); reads.push({id,...pending}); return pending.promise;},
    getSupabaseClient:()=>({from:()=>({insert:body=>({select:()=>({single:()=>{
      const pending=deferred(); inserts.push({body,...pending}); return pending.promise;
    }})})})}),
    resetUploadedDisclosureDraftForOffer(){},
    openSavedOfferInterview:()=>opened.push({...c.state.data}),
    updateSaveStatus(){},loadMyOffers:async()=>{},
    logOfferEvent:async(...args)=>logs.push(args),
    window:{confirm:message=>{alerts.push(message); return false;},announceWorkspaceStatus:message=>alerts.push(message),hofCustomerActionError:(_,message)=>message},
    console:{error(){},warn(){}},
  });
  vm.runInContext(source('  function cleanOfferDraftData(', '  async function saveOfferDraftToSupabase('),c);
  const start=html.includes('  function beginOfferOpenRequest(')?'  function beginOfferOpenRequest(':'  async function resumeOffer(';
  vm.runInContext(source(start,'  async function deleteOffer('),c);
  const reply=async(index,row)=>{reads[index].resolve(row); await tick();};
  return {c,reads,inserts,opened,alerts,logs,reply};
}

for (const [older,newer] of [['resumeOffer','resumeOffer'],['reuseOfferTerms','resumeOffer'],['resumeOffer','reuseOfferTerms']]) {
  test(`${older} cannot replace a later ${newer} selection`,async()=>{
    const x=setup(); const a=x.c[older]('a'), b=x.c[newer]('b');
    await x.reply(1,offer('b')); await b;
    const selected=x.c.state.data;
    await x.reply(0,offer('a')); await a;
    assert.equal(x.c.state.data,selected); assert.equal(x.opened.length,1); assert.deepEqual(x.alerts,[]);
  });
}
test('starting a fresh draft invalidates an older read',async()=>{
  const x=setup(); const a=x.c.resumeOffer('a');
  x.c.state.data={userType:'agent'}; const fresh=x.c.state.data;
  await x.reply(0,offer('a')); await a;
  assert.equal(x.c.state.data,fresh); assert.equal(x.opened.length,0);
});
for (const operation of ['resumeOffer','reuseOfferTerms']) {
  test(`${operation} ignores a response after changing accounts`,async()=>{
    const x=setup(); const a=x.c[operation]('a');
    x.c.hofAuth.session={user:{id:'other-owner'}};
    await x.reply(0,offer('a')); await a;
    assert.equal(x.opened.length,0); assert.deepEqual(x.alerts,[]);
  });
}
test('signing out ignores a pending resume',async()=>{
  const x=setup(); const a=x.c.resumeOffer('a'); x.c.hofAuth.session=null;
  await x.reply(0,offer('a')); await a;
  assert.equal(x.opened.length,0);
});
test('same-account token refresh does not discard a requested offer',async()=>{
  const x=setup(); const a=x.c.resumeOffer('a');
  x.c.hofAuth.session={user:{id:'owner'},access_token:'refreshed'};
  await x.reply(0,offer('a')); await a;
  assert.equal(x.opened.length,1); assert.equal(x.c.state.data._hofOfferId,'a');
});
test('an obsolete read failure cannot interrupt the newly opened offer',async()=>{
  const x=setup(); const a=x.c.resumeOffer('a'), b=x.c.resumeOffer('b');
  await x.reply(1,offer('b')); await b;
  x.reads[0].reject(new Error('old network failure')); await a;
  assert.deepEqual(x.alerts,[]); assert.equal(x.c.state.data._hofOfferId,'b');
});
test('a pending prepared-packet copy stops before insertion when selection changes',async()=>{
  const x=setup(); const a=x.c.resumeOffer('signed');
  await x.reply(0,offer('signed',{status:'Buyer Signed'}));
  const b=x.c.resumeOffer('b'); await x.reply(2,offer('b')); await b;
  await x.reply(1,offer('signed',{status:'Buyer Signed'}));
  assert.equal(x.inserts.length,0); await a;
  assert.equal(x.c.state.data._hofOfferId,'b');
});
test('an already-created copy stays saved without opening over a newer selection',async()=>{
  const x=setup(); const a=x.c.duplicateOffer('a',false,true);
  await x.reply(0,offer('a')); assert.equal(x.inserts.length,1);
  const b=x.c.resumeOffer('b'); await x.reply(1,offer('b')); await b;
  x.inserts[0].resolve({data:{id:'copy'}}); await tick();
  assert.equal(x.reads.length,2); await a;
  assert.equal(x.c.state.data._hofOfferId,'b'); assert.equal(x.inserts.length,1);
});
test('a duplicate source read cannot start a write after account change',async()=>{
  const x=setup(); const a=x.c.duplicateOffer('a');
  x.c.hofAuth.session={user:{id:'other-owner'}};
  await x.reply(0,offer('a')); assert.equal(x.inserts.length,0); await a;
});
test('failure of a superseded copy cannot prompt the user to retry it',async()=>{
  const x=setup(); const a=x.c.duplicateOffer('a',false,true);
  await x.reply(0,offer('a'));
  const b=x.c.resumeOffer('b'); await x.reply(1,offer('b')); await b;
  x.inserts[0].resolve({error:new Error('old failure')}); await a;
  assert.deepEqual(x.alerts,[]); assert.equal(x.c.state.data._hofOfferId,'b');
});
for (const failingSideEffect of ['logOfferEvent','loadMyOffers']) {
  test(`${failingSideEffect} failure does not duplicate an already-created copy`,async()=>{
    const x=setup(); x.c[failingSideEffect]=async()=>{throw new Error('unavailable');};
    // Logging during the subsequent resume is unrelated to the copy operation.
    const a=x.c.duplicateOffer('a',false,true); await x.reply(0,offer('a'));
    x.inserts[0].resolve({data:{id:'copy'}}); await tick();
    assert.equal(x.reads[1]?.id,'copy');
    x.c.logOfferEvent=async()=>{}; await x.reply(1,offer('copy')); await a;
    assert.equal(x.inserts.length,1); assert.equal(x.c.state.data._hofOfferId,'copy'); assert.deepEqual(x.alerts,[]);
  });
}
test('a selection made while retry logging runs cancels the old retry',async()=>{
  const x=setup(), logged=deferred();
  x.c.window.confirm=()=>true;
  x.c.logOfferEvent=async(_,event)=>event==='resume_retry_clicked'?logged.promise:undefined;
  const a=x.c.resumeOffer('a'); x.reads[0].reject(new Error('network')); await tick();
  const b=x.c.resumeOffer('b'); await x.reply(1,offer('b')); await b;
  logged.resolve(); await tick(); assert.equal(x.reads.length,2); await a;
  assert.equal(x.c.state.data._hofOfferId,'b');
});
for (const operation of ['resumeOffer','reuseOfferTerms']) {
  test(`${operation} succeeds without an error notice when only logging fails`,async()=>{
    const x=setup(); x.c.logOfferEvent=async()=>{throw new Error('logging unavailable');};
    const a=x.c[operation]('a'); await x.reply(0,offer('a')); await a;
    assert.equal(x.opened.length,1); assert.deepEqual(x.alerts,[]);
  });
}
