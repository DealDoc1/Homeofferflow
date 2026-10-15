const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const assert=require('node:assert/strict'), {test}=require('node:test');
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
function source(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0&&b>a);return html.slice(a,b);}
function setup(role='homebuyer',{blank=false,storageFails=false}={}){
 const nodes=new Map(), stored=new Map(), timers=new Map(), events=[];let clock=0,next=1;
 function node(id){const classes=new Set();return {id,textContent:'Start',innerHTML:'Original price note',dataset:{},value:'',type:'text',style:{},
   classList:{add:x=>classes.add(x),remove:x=>classes.delete(x),contains:x=>classes.has(x)},
   setAttribute(k,v){this[k]=v;}};}
 const get=id=>{if(!nodes.has(id))nodes.set(id,node(id));return nodes.get(id);};
 get('wizardOverlay').classList.add('active');
 const inputs=[Object.assign(get('buyer1First'),{value:'Fictional Buyer'}),Object.assign(get('propAddress'),{value:'100 QA Example Lane'}),
   Object.assign(get('offerPrice'),{value:'0'}),{id:'',type:'radio',name:'financing',value:'cash',checked:true},
   {id:'keepSurvey',type:'checkbox',name:'surveyDocs',value:'survey',checked:true}];
 const c={state:{step:blank?0:2,data:blank?{userType:role}:{userType:role,_hofOfferId:'fictional-offer',buyer1:'Fictional Buyer'},termsOK:true},
   hofAuth:{session:{user:{id:'fictional-owner'}}},__hofRestoringDraft:false,__hofSaveDebounce:null,
   HOF_STORAGE_KEY:'draft',HOF_STORAGE_OWNER_KEY:'owner',HOF_WIZARD_ORDER_VERSION:'qa',
   document:{getElementById:get,querySelectorAll:()=>inputs,body:{style:{overflow:'hidden'}}},
   localStorage:{getItem:k=>stored.get(k)||null,setItem:(k,v)=>{if(storageFails)throw Error('Blocked storage');stored.set(k,v);},removeItem:k=>stored.delete(k)},
   navigator:{onLine:true},uploadedDisclosureDraftNames:()=>['QA survey.pdf'],
   selectedLandingAudience:()=>role,hasMeaningfulCloudDraft:()=>true,syncCloudDraftSave:()=>events.push('cloud'),
   updateSaveStatus:x=>events.push(x),console:{error:()=>events.push('storage error')},
   confirm:()=>{throw Error('Exit must not ask for confirmation');},
   setTimeout:(fn,delay)=>{const id=next++;timers.set(id,{fn,at:clock+delay});return id;},clearTimeout:id=>timers.delete(id),
   window:{setHofModalIsolation:(el,active)=>events.push(['isolation',active]),scrollTo:()=>events.push('home'),__hofAccountProfileEpoch:0}};
 vm.createContext(c);
 vm.runInContext(source('  function resumableLocalOfferDraft()', '  function resumableAccountOfferDraft('),c);
 vm.runInContext(source('  function refreshResumeOfferCtas()', '  function resumeLocalOfferDraft('),c);
 vm.runInContext(source('  function getDraftSnapshot()', '  function updateConnectionStatus()'),c);
 vm.runInContext(source('  function closeWizard()', '  function startNewOffer()'),c);
 const tick=time=>{clock=time;for(const [id,t]of [...timers].sort((a,b)=>a[1].at-b[1].at))if(t.at<=clock){timers.delete(id);t.fn();}};
 return {c,get,stored,events,tick,inputs};
}
for(const role of ['homebuyer','agent','investor'])test(`${role} exits without a prompt and preserves the actual saved answers`,()=>{
 const x=setup(role), before=JSON.stringify(x.c.state);x.c.closeWizard();
 assert.equal(x.get('wizardOverlay').classList.contains('active'),false);assert.equal(x.get('wizardOverlay')['aria-hidden'],'true');
 assert.equal(x.c.document.body.style.overflow,'');assert.deepEqual(x.events.slice(0,3),['Saving...',['isolation',false],'home']);
 x.tick(250);const draft=JSON.parse(x.stored.get('draft'));
 assert.equal(draft.wizardOpen,false);assert.equal(draft.step,2);assert.equal(draft.offerId,'fictional-offer');
 assert.equal(draft.fields.buyer1First,'Fictional Buyer');assert.equal(draft.fields.offerPrice,'0');
 assert.equal(draft.radios.financing,'cash');assert.deepEqual(draft.checkboxes.surveyDocs,['survey']);
 assert.deepEqual(draft.uploadedDocNames,['QA survey.pdf']);assert.equal(x.stored.get('owner'),'fictional-owner');
 x.tick(300);assert.equal(JSON.stringify(x.c.state),before);
 assert.equal(x.get('navCta').textContent,role==='homebuyer'?'Resume Offer →':'Start');
 assert.equal(x.events.includes('cloud'),role!=='homebuyer');
});
test('an untouched interview exits without creating an empty saved draft',()=>{const x=setup('homebuyer',{blank:true});x.c.closeWizard();x.tick(300);assert.equal(x.stored.size,0);assert.equal(x.get('navCta').textContent,'Start');});
for(const change of ['offer','account','epoch'])test(`a ${change} change during the debounce cannot save stale answers`,()=>{
 const x=setup();x.c.closeWizard();
 if(change==='offer')x.c.state.data={userType:'homebuyer',buyer1:'Different Buyer'};
 if(change==='account')x.c.hofAuth.session.user.id='different-owner';
 if(change==='epoch')x.c.window.__hofAccountProfileEpoch++;
 x.tick(300);assert.equal(x.stored.size,0);
});
test('storage failure leaves answers in memory and does not claim a saved Resume draft',()=>{
 const x=setup('homebuyer',{storageFails:true});x.c.closeWizard();x.tick(300);
 assert.equal(x.c.state.data.buyer1,'Fictional Buyer');assert.equal(x.inputs[0].value,'Fictional Buyer');
 assert.equal(x.get('navCta').textContent,'Start');assert.ok(x.events.includes('storage error'));assert.equal(x.stored.size,0);
});
test('another account and payment returns never receive the saved Resume entry',()=>{
 const x=setup();x.c.closeWizard();x.tick(250);x.c.hofAuth.session.user.id='different-owner';x.tick(300);
 assert.equal(x.get('navCta').textContent,'Start');x.c.hofAuth.session.user.id='fictional-owner';
 x.c.window.__hofPaymentReturn=true;x.c.refreshResumeOfferCtas();assert.equal(x.get('navCta').textContent,'Start');
});
