const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict'), {test}=require('node:test');
const root=path.join(__dirname,'..');
const html=process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git',['show',process.env.HOF_TEST_SOURCE_REF+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024})
  : fs.readFileSync(path.join(root,'index.html'),'utf8');
function source(start,end){const a=html.indexOf(start),b=html.indexOf(end,a); assert.ok(a>=0&&b>a,start);return html.slice(a,b);}
function deferred(){let resolve,reject;const promise=new Promise((y,n)=>{resolve=y;reject=n;});return {promise,resolve,reject};}
const tick=()=>new Promise(setImmediate);
function setup(){
  const requests=[],timers=new Map(),marked=[],docListeners={}; let timer=0,token=0;
  class Element {
    constructor(){this.value='';this.dataset={};this.attrs={};this.handlers={};this.children=[];this.style={};this.isConnected=true;this.classList={add(){},remove(){}};}
    setAttribute(k,v){this.attrs[k]=v;} removeAttribute(k){delete this.attrs[k];}
    addEventListener(k,fn){(this.handlers[k]??=[]).push(fn);}
    dispatchEvent(e){e.target=this;for(const fn of this.handlers[e.type]||[])fn(e);return true;}
    appendChild(child){this.children.push(child);child.parent=this;}
    remove(){if(this.parent)this.parent.children=this.parent.children.filter(x=>x!==this);this.isConnected=false;}
    querySelectorAll(){return this.children.filter(x=>x.attrs.role==='option');}
    getBoundingClientRect(){return {left:10,bottom:40,width:300};}
    closest(){return null;}
    blur(){if(document.activeElement===this){document.activeElement=null;this.dispatchEvent({type:'blur'});}}
  }
  const document={activeElement:null,body:new Element(),createElement:()=>new Element(),addEventListener:(k,fn)=>(docListeners[k]??=[]).push(fn)};
  const window={addEventListener(){},setTimeout:(fn)=>{timers.set(++timer,fn);return timer;},_AutocompleteSessionToken:class{constructor(){this.id=++token;}},
    _AutocompleteSuggestion:{fetchAutocompleteSuggestions:request=>{const d=deferred();requests.push({request,...d});return d.promise;}}};
  const c=vm.createContext({window,document,console:{error(){}},Event:class{constructor(type){this.type=type;}},
    setTimeout:window.setTimeout,clearTimeout:id=>timers.delete(id),markGoogleAddressSelected:input=>marked.push(input)});
  vm.runInContext(source('  let _autocompleteService =','  const _headCallback'),c);
  const start=html.includes('  function _addressInputState(')?'  function _addressInputState(':'  function _wireGoogleAutocomplete(';
  vm.runInContext(source(start,'  function markGoogleAddressSelected('),c);
  vm.runInContext(source('  function _debounce(','  function fillBuyerMailAddressField('),c);
  const input=(callback=null)=>{const el=new Element();c._wireGoogleAutocomplete(el,callback);return el;};
  const type=(el,value)=>{document.activeElement=el;el.value=value;el.dispatchEvent({type:'input'});};
  const flush=async()=>{const pending=[...timers.values()];timers.clear();pending.forEach(fn=>fn());await tick();};
  const shown=()=>document.body.children.flatMap(dd=>dd.children.map(option=>option.children[0]?.textContent));
  const reply=async(index,label)=>{requests[index].resolve({suggestions:[{placePrediction:{mainText:label,text:label}}]});await tick();};
  return {c,document,requests,marked,input,type,flush,shown,reply,docListeners};
}
test('late suggestions cannot replace newer results',async()=>{
  const x=setup(),input=x.input();x.type(input,'123 Old');await x.flush();x.type(input,'456 New');await x.flush();
  await x.reply(1,'456 New Street');await x.reply(0,'123 Old Street');assert.deepEqual(x.shown(),['456 New Street']);
});
test('typing invalidates a pending result before the next debounce expires',async()=>{
  const x=setup(),input=x.input();x.type(input,'123 Old');await x.flush();x.type(input,'456 New');
  await x.reply(0,'123 Old Street');assert.deepEqual(x.shown(),[]);
});
test('clearing the field immediately invalidates old suggestions',async()=>{
  const x=setup(),input=x.input();x.type(input,'123 Old');await x.flush();x.type(input,'');
  await x.reply(0,'123 Old Street');assert.deepEqual(x.shown(),[]);await x.flush();assert.equal(x.requests.length,1);
});
test('a previous field cannot replace the active field results',async()=>{
  const x=setup(),a=x.input(),b=x.input();x.type(a,'123 Property');await x.flush();x.type(b,'456 Mailing');await x.flush();
  await x.reply(1,'456 Mailing Street');await x.reply(0,'123 Property Street');assert.deepEqual(x.shown(),['456 Mailing Street']);
});
test('old failures cannot close the latest results',async()=>{
  const x=setup(),input=x.input();x.type(input,'123 Old');await x.flush();x.type(input,'456 New');await x.flush();
  await x.reply(1,'456 New Street');x.requests[0].reject(new Error('old failure'));await tick();assert.deepEqual(x.shown(),['456 New Street']);
});
for(const action of ['blur','escape','remove'])test(`${action} prevents pending suggestions reopening`,async()=>{
  const x=setup(),input=x.input();x.type(input,'123 Pending');await x.flush();
  if(action==='blur')input.blur();if(action==='remove')input.isConnected=false;
  if(action==='escape')input.dispatchEvent({type:'keydown',key:'Escape',preventDefault(){}});
  await x.reply(0,'123 Pending Street');assert.deepEqual(x.shown(),[]);
});
function prediction(d){const place={formattedAddress:'123 Formatted Street',addressComponents:[{longText:'123',shortText:'123',types:['street_number']}],fetchFields:()=>d.promise};return {text:'123 Suggested Street',toPlace:()=>place};}
for(const failed of [false,true])test(`manual correction survives ${failed?'failed':'successful'} delayed details`,async()=>{
  const x=setup(),d=deferred(),callbacks=[],input=x.input(v=>callbacks.push(v));x.document.activeElement=input;
  const result=x.c._selectPrediction(prediction(d),'123',input,v=>callbacks.push(v));x.type(input,'123 Corrected Apt 4');
  if(failed)d.reject(new Error('network'));else d.resolve();await result;
  assert.equal(input.value,'123 Corrected Apt 4');assert.equal(callbacks.length,0);assert.equal(x.marked.length,0);
});
test('removed fields ignore completed details and side effects',async()=>{
  const x=setup(),d=deferred(),input=x.input(),callbacks=[];x.document.activeElement=input;
  const result=x.c._selectPrediction(prediction(d),'123',input,v=>callbacks.push(v));input.isConnected=false;d.resolve();await result;
  assert.equal(input.value,'123 Suggested Street');assert.equal(callbacks.length,0);assert.equal(x.marked.length,0);
});
test('selection updates listeners but does not issue another suggestion request',async()=>{
  const x=setup(),d=deferred(),input=x.input(),events=[];x.document.activeElement=input;
  input.addEventListener('input',()=>events.push('input'));input.addEventListener('change',()=>events.push('change'));
  const result=x.c._selectPrediction(prediction(d),'123',input,null);await x.flush();assert.equal(x.requests.length,0);
  d.resolve();await result;await x.flush();assert.equal(x.requests.length,0);assert.equal(input.value,'123 Formatted Street');
  assert.deepEqual(events,['input','change','input','change']);assert.equal(x.marked.length,1);
});
test('sessions are isolated by field and refreshed after a selection',async()=>{
  const x=setup(),a=x.input(),b=x.input();x.type(a,'123 First');await x.flush();x.type(a,'123 First More');await x.flush();
  assert.equal(x.requests[0].request.sessionToken,x.requests[1].request.sessionToken);
  x.type(b,'456 Second');await x.flush();assert.notEqual(x.requests[0].request.sessionToken,x.requests[2].request.sessionToken);
  const d=deferred();const pending=x.c._selectPrediction(prediction(d),'123',a,null);d.resolve();await pending;
  x.type(a,'789 Next');await x.flush();assert.notEqual(x.requests[0].request.sessionToken,x.requests[3].request.sessionToken);
});
test('typing a burst still makes only one debounced request',async()=>{
  const x=setup(),input=x.input();for(const value of ['1','12','123','123 Main'])x.type(input,value);
  await x.flush();assert.equal(x.requests.length,1);assert.equal(x.requests[0].request.input,'123 Main');
});
test('escape cancels a queued request before it uses Google',async()=>{
  const x=setup(),input=x.input();x.type(input,'123 Main');input.dispatchEvent({type:'keydown',key:'Escape',preventDefault(){}});
  await x.flush();assert.equal(x.requests.length,0);
});
test('unavailable Google leaves the typed address usable',async()=>{
  const x=setup(),input=x.input();x.type(input,'123 Manual Street');await x.flush();x.requests[0].reject(new Error('unavailable'));await tick();
  assert.equal(input.value,'123 Manual Street');assert.deepEqual(x.shown(),[]);
});
test('successful selection fills components and notifies listeners without more searches',async()=>{
  const x=setup(),d=deferred(),input=x.input(),components=[];x.document.activeElement=input;
  const result=x.c._selectPrediction(prediction(d),'123',input,values=>{
    components.push(...values);input.value='123 Short Street';input.dispatchEvent({type:'input'});
  });d.resolve();await result;await x.flush();
  assert.equal(components[0].long_name,'123');assert.equal(components[0].short_name,'123');
  assert.equal(components[0].types[0],'street_number');assert.equal(input.value,'123 Short Street');
  assert.equal(x.requests.length,0);assert.equal(x.marked.length,1);
});
test('failed details retain the selected fallback without claiming verification',async()=>{
  const x=setup(),d=deferred(),input=x.input();x.document.activeElement=input;
  const result=x.c._selectPrediction(prediction(d),'123',input,null);d.reject(new Error('unavailable'));await result;await x.flush();
  assert.equal(input.value,'123 Suggested Street');assert.equal(x.marked.length,0);assert.equal(x.requests.length,0);
});
test('new selection wins even when old details return last',async()=>{
  const x=setup(),a=deferred(),b=deferred(),input=x.input();x.document.activeElement=input;
  const first=x.c._selectPrediction(prediction(a),'123',input,null);
  const next={text:'456 Selected Street',toPlace:()=>({formattedAddress:'456 Formatted Street',fetchFields:()=>b.promise})};
  const second=x.c._selectPrediction(next,'456',input,null);b.resolve();await second;a.resolve();await first;
  assert.equal(input.value,'456 Formatted Street');assert.equal(x.marked.length,1);
});
test('a suggestion cannot be selected twice through pointer events',async()=>{
  const x=setup(),d=deferred(),input=x.input();let fetched=0;x.type(input,'123 Main');await x.flush();
  const pred={mainText:'123 Main',text:'123 Main',toPlace:()=>{fetched++;return {fetchFields:()=>d.promise};}};
  x.requests[0].resolve({suggestions:[{placePrediction:pred}]});await tick();
  const option=x.document.body.children[0].children[0];option._hofSelect();option._hofSelect();
  assert.equal(fetched,1);d.resolve();await tick();
});
test('opening more address dialogs does not add global click listeners',()=>{
  const x=setup();for(let n=0;n<20;n++)x.input();assert.equal(x.docListeners.click.length,1);
});
test('clicking the active address does not cancel its search due to other fields',async()=>{
  const x=setup(),a=x.input();x.input();x.type(a,'123 Active');await x.flush();
  for(const fn of x.docListeners.click)fn({target:a});await x.reply(0,'123 Active Street');
  assert.deepEqual(x.shown(),['123 Active Street']);
});
test('clicking outside dismisses an in-flight search',async()=>{
  const x=setup(),input=x.input();x.type(input,'123 Pending');await x.flush();
  for(const fn of x.docListeners.click)fn({target:{closest:()=>null}});
  await x.reply(0,'123 Pending Street');assert.deepEqual(x.shown(),[]);
});
