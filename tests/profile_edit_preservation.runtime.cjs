const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {test}=require('node:test');
const html=fs.readFileSync(path.resolve(__dirname,'..','index.html'),'utf8');
function source(a,b){const start=html.indexOf(a),end=html.indexOf(b,start);assert.ok(start>=0&&end>start);return html.slice(start,end);}
function setup(role='agent'){
  const nodes=new Map(),events={},doc={activeElement:null},controls=[];
  function element(tag='div'){
    const e={tagName:tag.toUpperCase(),id:'',type:tag==='input'?'text':'',value:'',checked:false,children:[],dataset:{},className:'',textContent:'',selectionStart:0,selectionEnd:0,
      classList:{contains:k=>e.className.split(' ').includes(k)},
      appendChild(c){this.children.push(c);if(c.id)nodes.set(c.id,c);},prepend(c){this.children.unshift(c);if(c.id)nodes.set(c.id,c);},
      remove(){nodes.delete(this.id);},addEventListener:(name,fn)=>{e['on'+name]=fn;},click(){e.onclick?.();},
      focus(){doc.activeElement=e;},setSelectionRange(a,b){e.selectionStart=a;e.selectionEnd=b;},
      closest:s=>s==='#accountProfileForm'&&controls.includes(e)?container:null,
      querySelectorAll:()=>controls.filter(c=>c.id.startsWith('prof')),contains:c=>controls.includes(c),setAttribute(k,v){e[k]=v;}};
    let markup='';Object.defineProperty(e,'innerHTML',{get:()=>markup,set:v=>{markup=v;if(e!==container)return;
      for(const child of e.children)if(child.id)nodes.delete(child.id);e.children=[];
      controls.forEach(x=>nodes.delete(x.id));controls.length=0;
      const tags=[...v.matchAll(/<input\b([^>]*)>/g)].map(m=>['input',m[1],''])
        .concat([...v.matchAll(/<(select|textarea)\b([^>]*)>([\s\S]*?)<\/\1>/g)].map(m=>[m[1],m[2],m[3]]));
      for(const [tag,attrs,body] of tags){
        const id=attrs.match(/\bid="([^"]+)"/)?.[1];if(!id)continue;
        const c=element(tag);c.id=id;c.type=attrs.match(/\btype="([^"]+)"/)?.[1]||'text';
        c.value=attrs.match(/\bvalue="([^"]*)"/)?.[1]||'';
        if(tag==='select')c.value=body.match(/value="([^"]*)"[^>]*selected/)?.[1]||body.match(/value="([^"]*)"/)?.[1]||'';
        controls.push(c);nodes.set(id,c);
      }
    }});return e;
  }
  const container=element(),status=element(),panel=element();panel.className='active';container.id='accountProfileForm';nodes.set(container.id,container);nodes.set('accountStatus',status);nodes.set('accountPanelProfile',panel);
  doc.getElementById=id=>nodes.get(id)||null;doc.createElement=element;doc.addEventListener=(name,fn)=>{(events[name]||=[]).push(fn)};
  const c=vm.createContext({document:doc,hofAuth:{role,session:{user:{id:'qa-owner',email:'qa@example.test'}},accountProfile:{agent_name:'Saved Agent',preferred_title_company:'Saved Title',investor_entity_name:'Saved Entity'}},
    __hofAccountProfileEpoch:0,escapeAttr:v=>String(v??''),brokerageLicenseDefault:(name,license)=>license||'',setTimeout:fn=>fn(),console});c.window=c;
  vm.runInContext(source('  function profileValue(','  function escapeAttr('),c);
  let save=async()=>({saved:true});c.saveAccountProfile=(...a)=>save(...a);
  const helper=html.match(/<script id="hof-profile-edit-draft-v1">([\s\S]*?)<\/script>/)?.[1];if(helper)vm.runInContext(helper,c);
  c.renderAccountProfileForm();
  return {c,doc,status,container,panel,get:id=>nodes.get(id),setSave:fn=>{save=fn},edit(id,value){const e=nodes.get(id);assert.ok(e,id);e.value=value;e.focus();for(const fn of events.input||[])fn({target:e});},
    discard(){const notice=nodes.get('profileEditDraftNotice');assert.ok(notice);notice.children.find(e=>e.tagName==='BUTTON').click();}};
}
test('late rendering keeps edited name and fills untouched saved defaults',()=>{
  const x=setup();x.edit('profAgentName','QA Unsaved Name');x.c.hofAuth.accountProfile={agent_name:'Incoming Name',preferred_title_company:'Incoming Title'};
  x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'QA Unsaved Name');assert.equal(x.get('profTitleCompany').value,'Incoming Title');
});
test('deliberately empty optional values and zero values survive rerender',()=>{
  const x=setup();x.edit('profTitleCompany','');x.edit('profOptionFee','0');x.c.renderAccountProfileForm();
  assert.equal(x.get('profTitleCompany').value,'');assert.equal(x.get('profOptionFee').value,'0');
});
test('focus and cursor are retained when a background render replaces a touched input',()=>{
  const x=setup();x.edit('profAgentName','QA Editing Name');x.get('profAgentName').setSelectionRange(3,5);x.c.renderAccountProfileForm();
  assert.equal(x.doc.activeElement,x.get('profAgentName'));assert.equal(x.get('profAgentName').selectionStart,3);assert.equal(x.get('profAgentName').selectionEnd,5);
});
test('successful save clears the temporary edit draft',async()=>{
  const x=setup();x.edit('profAgentName','QA Saved Name');await x.c.saveAccountProfile();x.c.hofAuth.accountProfile.agent_name='Fresh Server Name';x.c.renderAccountProfileForm();
  assert.equal(x.get('profAgentName').value,'Fresh Server Name');assert.equal(x.get('profileEditDraftNotice'),undefined);
});
test('failed save retains edits',async()=>{
  const x=setup();x.edit('profAgentName','QA Retry Name');x.setSave(async()=>null);await x.c.saveAccountProfile();x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'QA Retry Name');
});
test('a rejected save retains the draft and preserves the error',async()=>{
  const x=setup();x.edit('profAgentName','QA Network Retry');x.setSave(async()=>{throw new Error('offline')});
  await assert.rejects(x.c.saveAccountProfile(),/offline/);x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'QA Network Retry');
});
test('an additional-default save error does not clear the draft',async()=>{
  const x=setup();x.edit('profAgentName','QA Still Editing');x.status.className='account-status show err';await x.c.saveAccountProfile();x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'QA Still Editing');
});
test('new edits made while saving survive the older save response',async()=>{
  const x=setup();let done;x.setSave(()=>new Promise(r=>{done=r}));x.edit('profAgentName','QA First');const saving=x.c.saveAccountProfile();
  x.edit('profAgentName','QA Newer');done({saved:true});await saving;x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'QA Newer');
});
test('discard restores saved defaults without saving or network calls',()=>{
  const x=setup();let saves=0;x.setSave(async()=>{saves++;return{}});x.edit('profAgentName','QA Discard');x.discard();assert.equal(x.get('profAgentName').value,'Saved Agent');assert.equal(saves,0);
});
test('changing accounts cannot restore another account edit',()=>{
  const x=setup();x.edit('profAgentName','QA Previous User');x.c.hofAuth.session={user:{id:'different-qa-owner'}};x.c.hofAuth.accountProfile={agent_name:'Different User'};x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'Different User');
});
test('investor profile edits stay scoped to their own schema',()=>{
  const x=setup('investor');x.edit('profInvestorEntity','QA New Entity');x.c.renderAccountProfileForm();assert.equal(x.get('profInvestorEntity').value,'QA New Entity');
  x.c.hofAuth.role='agent';x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'Saved Agent');
});
test('a background render does not focus a hidden Profile panel',()=>{
  const x=setup();x.edit('profAgentName','QA Hidden Name');const old=x.get('profAgentName');x.panel.className='';x.c.renderAccountProfileForm();
  assert.equal(x.doc.activeElement,old);
});
test('dropdown edits survive replacement of the actual rendered select',()=>{
  const x=setup();x.edit('profTitlePayer','buyer');x.c.hofAuth.accountProfile.default_title_payer='seller';x.c.renderAccountProfileForm();assert.equal(x.get('profTitlePayer').value,'buyer');
});
test('logout clearing cannot recapture another login profile draft',()=>{
  const x=setup();x.edit('profAgentName','QA Previous');x.c.hofAuth.session=null;x.c.hofClearProfileEditDraft();
  x.c.hofAuth.session={user:{id:'different-qa-owner'}};x.c.hofAuth.accountProfile={agent_name:'Different Saved'};x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'Different Saved');
});
test('a same-account new-session epoch cannot restore an older edit',()=>{
  const x=setup();x.edit('profAgentName','QA Old Session');x.c.__hofAccountProfileEpoch++;x.c.hofAuth.accountProfile.agent_name='Fresh Session';x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'Fresh Session');
});
test('an older successful save cannot clear a newer account draft',async()=>{
  const x=setup();let done;x.setSave(()=>new Promise(r=>{done=r}));x.edit('profAgentName','QA Old Owner');const saving=x.c.saveAccountProfile();
  x.c.hofAuth.session={user:{id:'other-qa-owner'}};x.c.hofAuth.accountProfile={agent_name:'Different Saved'};x.c.renderAccountProfileForm();x.edit('profAgentName','QA Other Editing');
  done({saved:true});await saving;x.c.renderAccountProfileForm();assert.equal(x.get('profAgentName').value,'QA Other Editing');
});
