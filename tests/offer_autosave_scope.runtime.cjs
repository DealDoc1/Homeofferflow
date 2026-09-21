const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict'),{test}=require('node:test');
const root=path.join(__dirname,'..');
const html=process.env.HOF_TEST_SOURCE_REF
  ?execFileSync('git',['show',process.env.HOF_TEST_SOURCE_REF+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024})
  :fs.readFileSync(path.join(root,'index.html'),'utf8');
function source(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0&&b>a,start);return html.slice(a,b);}
function setup({open=true,role='agent'}={}){
  const events={},timers=new Map(),writes=[],notices=[],work={validation:0,conditions:0,sanitize:0,cloud:0};let next=0;
  const nodes=new Map();const get=id=>{if(!nodes.has(id))nodes.set(id,{hidden:false,textContent:'',classList:{contains:()=>open}});return nodes.get(id);};
  const store=new Map([['draft','original saved draft'],['owner','owner']]);
  const c=vm.createContext({state:{data:{userType:role,price:500000}},hofAuth:{session:{user:{id:'owner'}}},
    __hofRestoringDraft:false,__hofSaveDebounce:null,__hofWasOffline:false,__hofOfflineDraftToSync:null,HOF_STORAGE_KEY:'draft',HOF_STORAGE_OWNER_KEY:'owner',
    navigator:{onLine:true},console:{error(){}},
    document:{getElementById:get,addEventListener:(name,fn)=>events[name]=fn},
    addEventListener:(name,fn)=>events[name]=fn,
    setTimeout:fn=>{timers.set(++next,fn);return next;},clearTimeout:id=>timers.delete(id),
    getDraftSnapshot:()=>({data:{...c.state.data}}),hasMeaningfulCloudDraft:()=>true,
    localStorage:{getItem:key=>store.get(key)||null,setItem:(key,value)=>{writes.push([key,value]);store.set(key,value);},removeItem:key=>store.delete(key)},
    updateSaveStatus:message=>notices.push(message),syncCloudDraftSave:()=>work.cloud++,logOfferEvent(){},
    clearValidationFeedbackFor:()=>work.validation++,sanitizeBuyerMailingAddressAutofill:()=>work.sanitize++,restoreConditionalSections:()=>work.conditions++,
  });c.window=c;
  vm.runInContext(source('  function saveDraftNow()', '  window.addEventListener(\'offline\''),c);
  vm.runInContext(source('  function clearSavedDraft()',"  window.addEventListener('load', () => {"),c);
  const flush=()=>{for(const [id,fn] of [...timers]){timers.delete(id);fn();}};
  const event=(name,inside,id='offerPrice')=>events[name]({target:{id,closest:selector=>inside&&selector==='#wizardOverlay'?{}:null}});
  return {c,events,timers,writes,notices,work,store,get,flush,event,setOpen:value=>open=value};
}
for(const event of ['input','change'])for(const field of ['profAgentName','partnerSetupWebsite','platformSourceRevision']){
  test(`${event} in ${field} cannot overwrite the offer snapshot or invoke cloud sync`,()=>{
    const x=setup();x.event(event,false,field);x.flush();
    assert.equal(x.store.get('draft'),'original saved draft');assert.equal(x.writes.length,0);assert.equal(x.work.cloud,0);
    assert.equal(x.work.conditions,0);assert.equal(x.notices.length,0);
  });
}
for(const event of ['input','change'])test(`offer ${event} still saves and runs matching interview helpers`,()=>{
  const x=setup();x.event(event,true,'buyerMailAddr');x.flush();
  assert.equal(x.writes.filter(([key])=>key==='draft').length,1);assert.equal(x.work.cloud,1);
  assert.equal(x.work.validation,1);assert.equal(x.work.conditions,event==='change'?1:0);assert.equal(x.work.sanitize,event==='input'?1:0);
});
for(const change of ['offer','account','signout','same-account-new-sign-in']){
  test(`scheduled autosave is discarded after ${change}`,()=>{
    const x=setup();x.event('input',true);
    if(change==='offer')x.c.state.data={userType:'agent',price:700000};
    if(change==='account')x.c.hofAuth.session={user:{id:'different'}};
    if(change==='signout')x.c.hofAuth.session=null;
    if(change==='same-account-new-sign-in')x.c.__hofAccountProfileEpoch=2;
    x.flush();assert.equal(x.writes.length,0);assert.equal(x.work.cloud,0);assert.equal(x.store.get('draft'),'original saved draft');
  });
}
test('same-account token refresh keeps scheduled edits',()=>{
  const x=setup();x.event('input',true);x.c.hofAuth.session={user:{id:'owner'},access_token:'refreshed'};x.flush();
  assert.equal(x.writes.filter(([key])=>key==='draft').length,1);
});
test('multiple edits debounce to one save with the latest value',()=>{
  const x=setup();x.event('input',true);x.c.state.data.price=600000;x.event('input',true);x.flush();
  assert.equal(x.writes.filter(([key])=>key==='draft').length,1);assert.equal(JSON.parse(x.store.get('draft')).data.price,600000);
});
test('explicit save scheduled while closing the wizard is not discarded just because it closed',()=>{
  const x=setup();x.c.scheduleDraftSave();x.setOpen(false);x.flush();assert.equal(x.writes.filter(([key])=>key==='draft').length,1);
});
test('hydrating an offer does not schedule an autosave',()=>{
  const x=setup();x.c.__hofRestoringDraft=true;x.event('input',true);x.flush();assert.equal(x.writes.length,0);
});
test('offline status on an inactive page preserves the saved draft',()=>{
  const x=setup({open:false});x.c.navigator.onLine=false;x.c.updateConnectionStatus();
  assert.equal(x.writes.length,0);assert.equal(x.store.get('draft'),'original saved draft');assert.equal(x.get('appConnectivityNotice').hidden,false);
});
test('active offline offer stays local and reconnects once',()=>{
  const x=setup();x.c.navigator.onLine=false;x.c.updateConnectionStatus();
  assert.equal(x.writes.filter(([key])=>key==='draft').length,1);assert.equal(x.work.cloud,0);
  x.c.navigator.onLine=true;x.c.updateConnectionStatus();assert.equal(x.work.cloud,1);
  x.c.updateConnectionStatus();assert.equal(x.work.cloud,1);
});
test('inactive reconnect does not submit an offer while the user is on another page',()=>{
  const x=setup({open:false});x.c.__hofWasOffline=true;x.c.updateConnectionStatus();assert.equal(x.work.cloud,0);
});
test('valid offline edits still sync after the interview closes',()=>{
  const x=setup();x.c.navigator.onLine=false;x.c.updateConnectionStatus();x.setOpen(false);
  x.c.navigator.onLine=true;x.c.updateConnectionStatus();assert.equal(x.work.cloud,1);assert.equal(x.c.__hofOfflineDraftToSync,null);
});
for(const change of ['offer','account','same-account-new-sign-in'])test(`offline queue cannot sync after ${change}`,()=>{
  const x=setup();x.c.navigator.onLine=false;x.c.updateConnectionStatus();
  if(change==='offer')x.c.state.data={userType:'agent',price:700000};
  if(change==='account')x.c.hofAuth.session={user:{id:'new'}};
  if(change==='same-account-new-sign-in')x.c.__hofAccountProfileEpoch=2;
  x.c.navigator.onLine=true;x.c.updateConnectionStatus();assert.equal(x.work.cloud,0);assert.equal(x.c.__hofOfflineDraftToSync,null);
});
for(const open of [true,false])test(`beforeunload saves only an open interview (open=${open})`,()=>{
  const x=setup({open});x.events.beforeunload();assert.equal(x.writes.filter(([key])=>key==='draft').length,open?1:0);
});
test('homebuyer edits save locally without invoking account cloud sync',()=>{
  const x=setup({role:'homebuyer'});x.event('input',true);x.flush();assert.equal(x.writes.filter(([key])=>key==='draft').length,1);assert.equal(x.work.cloud,0);
});
