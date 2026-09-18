const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict'), {test}=require('node:test');
const root=path.join(__dirname,'..');
const html=process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git',['show',process.env.HOF_TEST_SOURCE_REF+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024})
  : fs.readFileSync(path.join(root,'index.html'),'utf8');
function source(start,end) {
  const a=html.indexOf(start), b=html.indexOf(end,a);
  assert.ok(a>=0&&b>a,start); return html.slice(a,b);
}
function deferred() {let resolve,reject; const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
const tick=()=>new Promise(setImmediate);
function setup({role='agent',path=role,base=true}={}) {
  const nodes=new Map(), radios={}, notices=[], queries=[], writes=[], timers=[], events={};
  const get=id=>{
    if(!nodes.has(id))nodes.set(id,{id,_value:'',get value(){return this._value;},set value(v){this._value=String(v);},style:{},disabled:false,checked:false,attrs:{},
      setAttribute(k,v){this.attrs[k]=v;},focus(){this.focused=true;},checkValidity:()=>true});
    return nodes.get(id);
  };
  const initialSession={user:{id:'owner',email:'agent@example.test'},access_token:'test-token'};
  const hooks={session:async()=>({data:{session:initialSession}}),lookup:async()=>({data:{user_id:'owner'}}),
    write:async body=>({data:{...body}}),fetch:async()=>({ok:true,json:async()=>({profile:{preferredTitleCompany:'Shared Title',preferredEscrowAgent:'Shared Officer'}})})};
  const store=new Map();
  const c=vm.createContext({state:{data:{userType:path,price:500000}},hofAuth:{role,session:initialSession,accountProfile:{}},
    document:{getElementById:get,querySelector:s=>{const name=s.match(/name="([^"]+)"/)?.[1];return radios[name]?{value:radios[name]}:null;},
      addEventListener:(event,fn)=>{(events[event] ||= []).push(fn);}},
    localStorage:{getItem:key=>store.get(key)||null,setItem:(key,value)=>{writes.push({key,value});store.set(key,value);}},
    getVal:id=>String(get(id).value||'').trim(),getRadio:name=>radios[name]||'',
    setRadioValue:(name,value)=>{radios[name]=value;},moneyNumber:v=>Number(v)||0,
    syncAgentQuickFields(){},renderAccountDashboard(){},updateAuthUI(){},
    setAccountStatus:(message,type)=>notices.push({message,type}),withTimeout:p=>p,
    startAccountOffer(){},setTimeout:fn=>{timers.push(fn);return timers.length;},
    console:{warn(){},error(){}},fetch:(...args)=>hooks.fetch(...args),
    getSupabaseClient:()=>({auth:{getSession:()=>hooks.session()},from:table=>{
      const query={table,kind:'read',filters:[]};
      const chain={select:()=>chain,eq:(...filter)=>{query.filters.push(filter);return chain;},
        update:body=>{query.kind='update';query.body=body;return chain;},insert:body=>{query.kind='insert';query.body=body;return chain;},
        maybeSingle:()=>{queries.push(query);return hooks.lookup();},single:()=>{queries.push(query);return hooks.write(query.body);}};
      return chain;
    }}),
  });
  c.window=c; c.root=c;
  for(const [id,value] of Object.entries({profAgentName:'Agent',profAgentLicense:'123',profAgentEmail:'agent@example.test',profAgentPhone:'555',
    profTitleCompany:'New Title',profEscrowAgent:'New Officer',profOptionFee:'250',profOptionDays:'7',profEarnestAmount:'5000',
    profTitlePayer:'seller',profSurveyChoice:'sellerExisting',profSurveyRejectedBy:'seller',
    profDefaultPossession:'funding',profDefaultFinancing:'cash',profDefaultBrokerFeeType:'percent',profDefaultBrokerFeeValue:'3',
    profDefaultEarnestRule:'percent',profDefaultEarnestPercent:'1',offerPrice:'500000'}))get(id).value=value;
  vm.runInContext(source('  function setInputIfEmpty(','  function resetWizardForFreshOffer('),c);
  if(html.includes('  function roundCurrency(')) vm.runInContext(source('  function roundCurrency(', '  function setMoneyVal('),c);
  if(base)vm.runInContext(source('  async function saveAccountProfile()','  function setInputIfEmpty('),c);
  else c.saveAccountProfile=async()=>null;
  const extra=source('<script id="hof-agent-defaults-v8-script">','</script>');
  vm.runInContext(extra.slice(extra.indexOf('>')+1),c);
  vm.runInContext(source('  root.applyBrokerageSharedDefaults =','  function brokerageAgentFollowUpAction('),c);
  const key=`hof_profile_extra_defaults_v8:${role}:agent@example.test`;
  store.set(key,JSON.stringify({default_financing:'cash',default_possession:'funding',default_broker_fee_type:'percent',default_broker_fee_value:'3',default_earnest_rule:'percent',default_earnest_percent:'1'}));
  return {c,get,radios,notices,queries,writes,timers,events,hooks,store,key};
}
test('saving profile and extras preserves the current offer, while new blanks receive defaults',async()=>{
  const x=setup(); x.get('titleCompany').value='Agreed Title'; x.get('escrowAgent').value='Agreed Officer';
  x.get('possession').value='leaseback'; x.get('earnestMoney').value='8000';
  x.radios.financing='conventional';x.radios.brokerFeeType='amount';x.get('brokerFeeAmount').value='9000';
  await x.c.saveAccountProfile();
  assert.equal(x.get('titleCompany').value,'Agreed Title');assert.equal(x.get('escrowAgent').value,'Agreed Officer');
  assert.equal(x.get('possession').value,'leaseback');assert.equal(x.get('earnestMoney').value,'8000');
  assert.equal(x.radios.financing,'conventional');assert.equal(x.radios.brokerFeeType,'amount');
  assert.equal(x.get('brokerFeeAmount').value,'9000');assert.equal(x.writes.length,1);
  assert.equal(x.c.hofAuth.accountProfile.preferred_title_company,'New Title');
  for(const id of ['titleCompany','escrowAgent','possession','earnestMoney','brokerFeeAmount'])x.get(id).value='';
  delete x.radios.financing;delete x.radios.brokerFeeType;
  x.c.applyProfileDefaultsToWizard(false);
  assert.equal(x.get('titleCompany').value,'New Title');assert.equal(x.radios.financing,'cash');assert.equal(x.radios.brokerFeeType,'percent');
});
for(const path of ['homebuyer','fsbo','investor']) {
  test(`agent extra defaults cannot alter the ${path} path`,()=>{
    const x=setup({path}); x.get('possession').value='';
    x.c.applyProfileExtraDefaultsToWizard(true);
    assert.equal(x.get('possession').value,'');assert.deepEqual(x.radios,{});assert.equal(x.get('earnestMoney').value,'');
  });
}
test('signed-out visitors do not receive account extra defaults',()=>{
  const x=setup();x.c.hofAuth.session=null;x.c.applyProfileExtraDefaultsToWizard(false);
  assert.equal(x.get('possession').value,'');assert.deepEqual(x.radios,{});
});
test('price changes preserve financing and fee choices and matching conditional fields',()=>{
  const x=setup(); x.radios.financing='fha';x.radios.brokerFeeType='amount';x.get('brokerFeeAmount').value='8000';
  x.events.input.forEach(fn=>fn({target:x.get('offerPrice')}));
  assert.equal(x.radios.financing,'fha');assert.equal(x.radios.brokerFeeType,'amount');
  assert.equal(x.get('brokerFeeAmount').value,'8000');assert.equal(x.get('brokerFeeAmountField').style.display,'block');
  assert.equal(x.get('brokerFeePercentField').style.display,'none');
});
test('fresh matching investor blanks still receive saved preferences',()=>{
  const x=setup({role:'investor'});x.c.applyProfileExtraDefaultsToWizard(false);
  assert.equal(x.radios.financing,'cash');assert.equal(x.get('possession').value,'funding');
  assert.equal(Number(x.get('earnestMoney').value),5000);assert.equal(x.radios.brokerFeeType,undefined);
});
test('saved seller leaseback preference selects the actual temporary-lease option',()=>{
  const x=setup();x.store.set(x.key,JSON.stringify({default_possession:'leaseback'}));
  x.c.applyProfileExtraDefaultsToWizard(false);
  assert.equal(x.get('possession').value,'sellerTemporaryLease');
  assert.ok(html.includes('<option value="sellerTemporaryLease">Seller remains temporarily after closing'));
  x.get('possession').value='buyerTemporaryLease';
  x.c.applyProfileExtraDefaultsToWizard(false);
  assert.equal(x.get('possession').value,'buyerTemporaryLease','Saved defaults cannot replace a current agreement');
});
test('reopening through account start cannot schedule a forced defaults overwrite',()=>{
  const x=setup();x.radios.financing='va';x.get('possession').value='leaseback';
  x.c.startAccountOffer();x.timers.forEach(fn=>fn());
  assert.equal(x.radios.financing,'va');assert.equal(x.get('possession').value,'leaseback');assert.equal(x.timers.length,0);
});
test('required-field validation failure is not reported as a successful profile save',async()=>{
  const x=setup();x.get('profAgentLicense').value='';await x.c.saveAccountProfile();
  assert.equal(x.writes.length,0);assert.equal(x.queries.length,0);assert.equal(x.notices.at(-1).type,'err');
  assert.equal(x.get('saveAccountProfileButton').disabled,false);
});
test('a blocked duplicate click does not save extras or report success',async()=>{
  const x=setup();x.get('saveAccountProfileButton').disabled=true;await x.c.saveAccountProfile();
  assert.equal(x.writes.length,0);assert.equal(x.notices.length,0);
});
test('device storage failure is reported without claiming all preferences saved',async()=>{
  const x=setup();x.c.localStorage.setItem=()=>{throw new Error('quota');};await x.c.saveAccountProfile();
  assert.equal(x.notices.at(-1).type,'err');assert.match(x.notices.at(-1).message,/could not be saved on this device/);
  assert.equal(x.c.hofAuth.accountProfile.preferred_title_company,'New Title');
});
test('late session response cannot restore the previous account',async()=>{
  const x=setup(), wait=deferred(), oldSession=x.c.hofAuth.session;x.hooks.session=()=>wait.promise;
  const saving=x.c.saveAccountProfile();x.c.hofAuth.session={user:{id:'new',email:'new@example.test'}};
  wait.resolve({data:{session:oldSession}});await saving;
  assert.equal(x.c.hofAuth.session.user.id,'new');assert.equal(x.queries.length,0);assert.equal(x.writes.length,0);
});
test('a missing refreshed session cannot fall back to saving as a logged-out user',async()=>{
  const x=setup();x.hooks.session=async()=>({data:{session:null}});await x.c.saveAccountProfile();
  assert.equal(x.queries.length,0);assert.equal(x.writes.length,0);assert.equal(x.notices.at(-1).type,'err');
});
test('account change during profile lookup prevents a write',async()=>{
  const x=setup(),wait=deferred();x.hooks.lookup=()=>wait.promise;
  const saving=x.c.saveAccountProfile();await tick();x.c.hofAuth.session={user:{id:'new'}};
  wait.resolve({data:{user_id:'owner'}});await saving;
  assert.equal(x.queries.length,1);assert.equal(x.writes.length,0);
});
test('late profile write cannot replace a different account profile or local preferences',async()=>{
  const x=setup(),wait=deferred();x.hooks.write=()=>wait.promise;
  const saving=x.c.saveAccountProfile();await tick();
  x.c.hofAuth.session={user:{id:'new',email:'new@example.test'}};const other={agent_name:'Other'};x.c.hofAuth.accountProfile=other;
  wait.resolve({data:{agent_name:'Old'}});await saving;
  assert.equal(x.c.hofAuth.accountProfile,other);assert.equal(x.writes.length,0);
});
test('alias lookup failure restores the save button and cannot claim success',async()=>{
  const x=setup();x.c.hofResolveAgentProfileOwner=async()=>{throw new Error('offline');};
  // Observe rejections on the baseline without hiding the expected UI assertion.
  await x.c.saveAccountProfile().catch(()=>{});
  assert.equal(x.get('saveAccountProfileButton').disabled,false);assert.equal(x.writes.length,0);assert.equal(x.notices.at(-1).type,'err');
});
test('shared title defaults save to the profile without changing an agreed title office',async()=>{
  const x=setup();x.get('titleCompany').value='Agreed Title';x.get('escrowAgent').value='Agreed Officer';
  await x.c.applyBrokerageSharedDefaults();
  assert.equal(x.c.hofAuth.accountProfile.preferred_title_company,'Shared Title');
  assert.equal(x.get('titleCompany').value,'Agreed Title');assert.equal(x.get('escrowAgent').value,'Agreed Officer');
  assert.equal(x.get('applyBrokerageSharedDefaultsButton').disabled,false);
});
test('shared defaults response is ignored after account change',async()=>{
  const x=setup(),wait=deferred();x.hooks.fetch=()=>wait.promise;
  const saving=x.c.applyBrokerageSharedDefaults();x.c.hofAuth.session={user:{id:'new'}};const other={agent_name:'Other'};x.c.hofAuth.accountProfile=other;
  wait.resolve({ok:true,json:async()=>({profile:{preferredTitleCompany:'Old Title'}})});await saving;
  assert.equal(x.c.hofAuth.accountProfile,other);assert.equal(x.get('applyBrokerageSharedDefaultsButton').disabled,false);
});
test('profile write from an earlier sign-in cannot apply after signing back into the same account',async()=>{
  const x=setup(),wait=deferred();x.hooks.write=()=>wait.promise;
  const saving=x.c.saveAccountProfile();await tick();
  x.c.__hofAccountProfileEpoch=2;const fresh={agent_name:'Fresh sign-in'};x.c.hofAuth.accountProfile=fresh;
  wait.resolve({data:{agent_name:'Previous sign-in'}});await saving;
  assert.equal(x.c.hofAuth.accountProfile,fresh);assert.equal(x.writes.length,0);
});
test('brokerage defaults from an earlier sign-in cannot apply after signing back in',async()=>{
  const x=setup(),wait=deferred();x.hooks.fetch=()=>wait.promise;
  const saving=x.c.applyBrokerageSharedDefaults();x.c.__hofAccountProfileEpoch=2;
  const fresh={agent_name:'Fresh sign-in'};x.c.hofAuth.accountProfile=fresh;
  wait.resolve({ok:true,json:async()=>({profile:{preferredTitleCompany:'Old Title'}})});await saving;
  assert.equal(x.c.hofAuth.accountProfile,fresh);
});

const numericIds={agent:['profOptionFee','profOptionDays','profEarnestAmount'],investor:['profInvestorOptionFee','profInvestorOptionDays','profInvestorEarnest']};
const numericKeys=['default_option_fee','default_option_days','default_earnest_amount'];
for(const role of ['agent','investor']) {
  for(const values of [['0','0','0'],['','',''],['425','10','8250']]) {
    test(`${role} profile preserves numeric defaults ${JSON.stringify(values)} through save and render`,async()=>{
      const x=setup({role}); numericIds[role].forEach((id,i)=>x.get(id).value=values[i]);
      await x.c.saveAccountProfile();
      const body=x.queries.find(q=>q.kind==='update').body;
      numericKeys.forEach((key,i)=>assert.equal(body[key],values[i]===''?null:Number(values[i])));
      // Execute the original form renderer, independently of later UI wrappers.
      x.c.escapeAttr=v=>String(v);
      vm.runInContext(source('  function profileValue(','  function escapeAttr('),x.c);
      x.c.renderAccountProfileForm();
      numericIds[role].forEach((id,i)=>{
        const input=x.get('accountProfileForm').innerHTML.match(new RegExp('<input id="'+id+'"[^>]*>'))?.[0];
        assert.ok(input,id);assert.match(input,new RegExp('value="'+values[i]+'"'));
      });
    });
  }
  for(const [value,badInput] of [['-1',false],['1.5',false],['Infinity',false],['not a number',false],['9007199254740992',false],['',true]]) {
    for(const id of numericIds[role]) {
      test(`${role} rejects invalid ${id} ${JSON.stringify(value)} badInput=${badInput} before network access`,async()=>{
        const x=setup({role});let sessionCalls=0;
        x.hooks.session=async()=>{sessionCalls++;return {data:{session:x.c.hofAuth.session}};};
        x.get(id).value=value;x.get(id).validity={badInput};
        await x.c.saveAccountProfile();
        assert.equal(sessionCalls,0);assert.equal(x.queries.length,0);assert.equal(x.writes.length,0);
        assert.equal(x.notices.at(-1).type,'err');assert.match(x.notices.at(-1).message,/whole number/);
        assert.equal(x.get(id).focused,true);assert.equal(x.get('saveAccountProfileButton').disabled,false);
      });
    }
  }
  test(`${role} rejects option days outside the existing database integer range`,async()=>{
    const x=setup({role});x.get(numericIds[role][1]).value='2147483648';
    await x.c.saveAccountProfile();assert.equal(x.queries.length,0);assert.equal(x.writes.length,0);
    assert.equal(x.notices.at(-1).type,'err');
  });
  for(const values of [[0,0,0],[425,10,8250],[null,null,null]]) {
    test(`${role} saved defaults ${JSON.stringify(values)} survive the actual price calculator`,()=>{
      const x=setup({role});x.store.delete(x.key);
      numericKeys.forEach((key,i)=>x.c.hofAuth.accountProfile[key]=values[i]);
      vm.runInContext(source('  function numFromEl(','  function getSelectedFinancingType('),x.c);
      vm.runInContext(source('  function calculatePriceTermsOnly(','  function calculateFinancingDefaults('),x.c);
      x.c.showFieldRecommendation=()=>{};
      x.c.applyProfileDefaultsToWizard(false);x.c.calculatePriceTermsOnly();
      const expected=values[0]===null?[250,7,5000]:values;
      ['optionFee','optionDays','earnestMoney'].forEach((id,i)=>assert.equal(Number(x.get(id).value),expected[i]));
      x.get('offerPrice').value='700000';x.c.calculatePriceTermsOnly();
      assert.equal(Number(x.get('earnestMoney').value),values[2]===null?7000:values[2]);
    });
  }
  test(`${role} profile completion distinguishes zero terms from missing terms`,()=>{
    const x=setup({role});x.c.readExtraDefaults=()=>({});
    vm.runInContext(source('  function completionItems(){','  function renderCompletionStrip(){'),x.c);
    for(const value of [0,'0',null,undefined,'']) {
      x.c.hofAuth.accountProfile={default_option_fee:value,default_option_days:value};
      const terms=x.c.completionItems().at(-1)[1];assert.equal(Boolean(terms),value===0||value==='0');
    }
  });
}
