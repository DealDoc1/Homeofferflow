const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict'),{test}=require('node:test');
const root=path.join(__dirname,'..');
const html=process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git',['show',process.env.HOF_TEST_SOURCE_REF+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024})
  : fs.readFileSync(path.join(root,'index.html'),'utf8');
function source(a,b) {const start=html.indexOf(a),end=html.indexOf(b,start);assert.ok(start>=0&&end>start,a);return html.slice(start,end);}
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
const tick=()=>new Promise(setImmediate);
function setup(kind='canonical') {
  const reads=[],renders=[],removed=[];
  const c=vm.createContext({hofAuth:{session:{user:{id:'owner'}},role:'agent',accountProfile:null,agentIabsDocument:null},
    state:{data:{userType:'agent',includeAgentIabs:true}},
    document:{getElementById:id=>({remove:()=>removed.push(id)})},
    normalizeAccountRole:role=>role||'agent',
    getSupabaseClient:()=>({from:table=>{
      const query={table,filters:[]};const chain={select:()=>chain,eq:(...filter)=>{query.filters.push(filter);return chain;},
        maybeSingle:()=>{const pending=deferred();reads.push({...query,...pending});return pending.promise;}};return chain;
    }}),
    updateAuthUI:()=>renders.push('auth'),applyProfileDefaultsToWizard:()=>renders.push('defaults'),
    renderProfileIabsCard:()=>renders.push('iabs-card'),mountIabsOfferOption:()=>renders.push('iabs-option'),
    isAgentAccount:()=>['agent','broker'].includes(c.hofAuth.role)&&!!c.hofAuth.session?.user,
    console:{warn(){}},
  });c.window=c;c.root=c;
  if(html.includes('  function resetProfileForSessionChange('))vm.runInContext(source('  function resetProfileForSessionChange(','  async function loadAccountProfile()'),c);
  const authPrefix='      client.auth.onAuthStateChange(async (event, session) => {';
  const authStart=html.indexOf(authPrefix)+authPrefix.length;
  const authEnd=html.indexOf('        hofAuth.session = session || null;',authStart);
  vm.runInContext('function authChange(session,event="SIGNED_IN"){'+html.slice(authStart,authEnd)+'hofAuth.session=session||null;}',c);
  if(kind==='base')vm.runInContext(source('  async function loadAccountProfile()','  function isCurrentAdmin()'),c);
  else vm.runInContext(source('  root.hofResolveAgentProfileOwner =','  const oldIsProfileMeaningful ='),c);
  vm.runInContext(source('  root.loadAgentIabsDocument =','  function renderProfileIabsCard()'),c);
  return {c,reads,renders,removed,reply:async(index,value)=>{reads[index].resolve(value);await tick();}};
}
for(const kind of ['base','canonical']) {
  // Canonical loader resolves the profile alias first; isolate that separate
  // read when testing profile-query ordering. Alias integration has its own case.
  function configured(){const x=setup(kind);x.c.hofResolveAgentProfileOwner=async()=> 'canonical-owner';return x;}
  test(`${kind}: late profile response cannot repopulate a signed-out account`,async()=>{
    const x=configured(),pending=x.c.loadAccountProfile();await tick();x.c.authChange(null,'SIGNED_OUT');
    await x.reply(0,{data:{user_id:'owner',agent_name:'Old'}});await pending;
    assert.equal(x.c.hofAuth.accountProfile,null);assert.deepEqual(x.renders,[]);
  });
  test(`${kind}: switching account prevents old profile defaults from rendering`,async()=>{
    const x=configured(),pending=x.c.loadAccountProfile();await tick();x.c.authChange({user:{id:'next'}});
    const next={agent_name:'Next'};x.c.hofAuth.accountProfile=next;
    await x.reply(0,{data:{agent_name:'Old'}});await pending;
    assert.equal(x.c.hofAuth.accountProfile,next);assert.deepEqual(x.renders,[]);
  });
  test(`${kind}: latest load wins when responses arrive in reverse order`,async()=>{
    const x=configured(),a=x.c.loadAccountProfile(),b=x.c.loadAccountProfile();await tick();
    // Canonical load can cancel the first request before it issues a query.
    const latest=x.reads.length-1;await x.reply(latest,{data:{agent_name:'Latest'}});await b;
    if(latest>0)await x.reply(0,{data:{agent_name:'Older'}});await a;
    assert.equal(x.c.hofAuth.accountProfile.agent_name,'Latest');assert.deepEqual(x.renders,['auth','defaults']);
  });
  test(`${kind}: a successful profile save supersedes an earlier read`,async()=>{
    const x=configured(),pending=x.c.loadAccountProfile();await tick();
    const saved={agent_name:'Just saved'};x.c.hofAuth.accountProfile=saved;
    await x.reply(0,{data:{agent_name:'Before save'}});await pending;
    assert.equal(x.c.hofAuth.accountProfile,saved);assert.deepEqual(x.renders,[]);
  });
  test(`${kind}: signing back into the same account cannot revive an old request`,async()=>{
    const x=configured(),pending=x.c.loadAccountProfile();await tick();
    x.c.authChange(null,'SIGNED_OUT');x.c.authChange({user:{id:'owner'}});
    await x.reply(0,{data:{agent_name:'Old sign-in'}});await pending;
    assert.equal(x.c.hofAuth.accountProfile,null);assert.deepEqual(x.renders,[]);
  });
  test(`${kind}: same-account token refresh retains the pending current load`,async()=>{
    const x=configured(),pending=x.c.loadAccountProfile();await tick();
    x.c.authChange({user:{id:'owner'},access_token:'new'},'TOKEN_REFRESHED');
    await x.reply(0,{data:{agent_name:'Current'}});await pending;
    assert.equal(x.c.hofAuth.accountProfile.agent_name,'Current');assert.deepEqual(x.renders,['auth','defaults']);
  });
  test(`${kind}: role change discards an old profile type`,async()=>{
    const x=configured(),pending=x.c.loadAccountProfile();await tick();x.c.hofAuth.role='investor';
    await x.reply(0,{data:{agent_name:'Old'}});await pending;
    assert.equal(x.c.hofAuth.accountProfile,null);assert.deepEqual(x.renders,[]);
  });
}
test('account change clears cached profile and optional IABS presentation immediately',()=>{
  const x=setup();x.c.hofAuth.accountProfile={agent_name:'Old'};x.c.hofAuth.agentIabsDocument={original_filename:'Old.pdf'};
  x.c.authChange({user:{id:'next'}});
  assert.equal(x.c.hofAuth.accountProfile,null);assert.equal(x.c.hofAuth.agentIabsDocument,null);
  assert.equal(x.c.state.data.includeAgentIabs,false);assert.deepEqual(x.removed,['agentIabsProfileCard','agentIabsOfferOption']);
});
test('canonical alias lookup cannot continue under a changed account',async()=>{
  const x=setup(),pending=x.c.loadAccountProfile();
  assert.equal(x.reads[0].table,'hof_agent_profile_aliases');x.c.authChange({user:{id:'next'}});
  await x.reply(0,{data:{canonical_user_id:'canonical-owner'}});
  assert.equal(x.reads.length,1);await pending;assert.deepEqual(x.renders,[]);
});
test('linked account still loads its authorized canonical profile',async()=>{
  const x=setup(),pending=x.c.loadAccountProfile();
  await x.reply(0,{data:{canonical_user_id:'canonical-owner'}});
  assert.deepEqual(x.reads[1].filters,[['user_id','canonical-owner']]);
  await x.reply(1,{data:{user_id:'canonical-owner',agent_name:'Shared'}});await pending;
  assert.equal(x.c.hofAuth.accountProfile.agent_name,'Shared');
});
for(const fail of [false,true]) {
  test(`obsolete IABS ${fail?'error':'response'} cannot replace the current document`,async()=>{
    const x=setup(),pending=x.c.loadAgentIabsDocument();
    x.c.authChange({user:{id:'next'}});const next={original_filename:'Next.pdf'};x.c.hofAuth.agentIabsDocument=next;
    if(fail){x.reads[0].reject(new Error('old failure'));await tick();}
    else await x.reply(0,{data:{original_filename:'Old.pdf'}});
    await pending;assert.equal(x.c.hofAuth.agentIabsDocument,next);
  });
}
test('removing a cached IABS document prevents an older load from resurrecting it',async()=>{
  const x=setup();x.c.hofAuth.agentIabsDocument={original_filename:'Removed.pdf'};
  const pending=x.c.loadAgentIabsDocument();x.c.hofAuth.agentIabsDocument=null;
  await x.reply(0,{data:{original_filename:'Removed.pdf'}});await pending;
  assert.equal(x.c.hofAuth.agentIabsDocument,null);
});
test('latest IABS query result wins',async()=>{
  const x=setup(),a=x.c.loadAgentIabsDocument(),b=x.c.loadAgentIabsDocument();
  await x.reply(1,{data:{original_filename:'Latest.pdf'}});await b;
  await x.reply(0,{data:{original_filename:'Old.pdf'}});await a;
  assert.equal(x.c.hofAuth.agentIabsDocument.original_filename,'Latest.pdf');
});
test('profile wrapper does not start IABS loading after the account changes',async()=>{
  const x=setup(),profile=deferred();let loads=0;
  x.c.loadAccountProfile=()=>profile.promise;x.c.loadAgentIabsDocument=async()=>{loads++;};
  vm.runInContext(source('  const priorLoadProfile = root.loadAccountProfile;','  const priorProfileRender ='),x.c);
  const pending=x.c.loadAccountProfile();x.c.authChange({user:{id:'next'}});profile.resolve(null);await pending;
  assert.equal(loads,0);assert.deepEqual(x.renders,[]);
});
test('profile wrapper does not render after account change during IABS lookup',async()=>{
  const x=setup(),document=deferred();x.c.loadAccountProfile=async()=>null;x.c.loadAgentIabsDocument=()=>document.promise;
  vm.runInContext(source('  const priorLoadProfile = root.loadAccountProfile;','  const priorProfileRender ='),x.c);
  const pending=x.c.loadAccountProfile();await tick();x.c.authChange({user:{id:'next'}});document.resolve(null);await pending;
  assert.deepEqual(x.renders,[]);
});
