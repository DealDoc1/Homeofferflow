const fs = require('node:fs');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const test = require('node:test');
const assert = require('node:assert/strict');
const html = process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git', ['show', process.env.HOF_TEST_SOURCE_REF + ':index.html'], {encoding:'utf8', maxBuffer:8*1024*1024})
  : fs.readFileSync('index.html', 'utf8');
function source(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert.ok(a >= 0 && b > a);
  return html.slice(a, b);
}
function deferred() {
  let resolve, reject;
  const promise = new Promise((a,b) => {resolve=a; reject=b;});
  return {promise, resolve, reject};
}
function file(name, phase='body', size=100) {
  const gate = deferred();
  const pdf = Uint8Array.from([37,80,68,70]).buffer;
  return {name, type:'application/pdf', size, gate,
    slice:()=>({arrayBuffer:()=>phase==='header' ? gate.promise : Promise.resolve(pdf)}),
    body:phase==='body' ? gate.promise : Promise.resolve('JVBERg=='), pdf};
}
async function tick() { await new Promise(resolve=>setImmediate(resolve)); }
function setup() {
  const input = {value:'selected', attrs:{}, setAttribute(k,v){this.attrs[k]=v;}, focus(){}};
  const ack = {checked:true};
  const x = {window:{hofUploadedDisclosureDocs:[]}, state:{data:{}}, hofAuth:{session:{user:{id:'one'}}},
    document:{getElementById:id=>id==='uploadedDisclosureDocs'?input:id==='uploadedDisclosureAck'?ack:null},
    console:{error(){}}, Uint8Array, statuses:[], reviews:0,
    getCurrentSteps:()=>['step5'], showStep(){}, saveDraft(){}, escapeHtml:s=>s};
  vm.createContext(x);
  vm.runInContext(source('  const uploadedDisclosureTypes =', '  function renderUploadedDocsList()'), x);
  x.setUploadedDisclosureStatus = message=>x.statuses.push(message);
  x.renderUploadedDocsList = ()=>{};
  x.renderReview = ()=>x.reviews++;
  x.readFileAsBase64 = f=>f.body;
  vm.runInContext(source('  async function handleUploadedDisclosureDocs(', '  function controlledLaunchUnsupportedPaths('),x);
  x.input=input; x.ack=ack;
  x.names=()=>Array.from(x.window.hofUploadedDisclosureDocs, d=>d.name);
  return x;
}
for (const phase of ['header','body']) {
  for (const change of ['offer','account','signout','epoch','reset']) {
    test(`late ${phase} completion is ignored after ${change}`, async()=>{
      const x=setup(), f=file('private.pdf',phase);
      const pending=x.handleUploadedDisclosureDocs([f]); await tick();
      if(change==='offer') x.state.data={};
      if(change==='account') x.hofAuth.session.user.id='two';
      if(change==='signout') x.hofAuth.session=null;
      if(change==='epoch') x.window.__hofAccountProfileEpoch=1;
      if(change==='reset') x.resetUploadedDisclosureDraftForOffer({});
      const statuses=x.statuses.length;
      f.gate.resolve(phase==='header'?f.pdf:'JVBERg=='); await pending;
      assert.deepEqual(x.names(),[]);
      assert.equal(x.statuses.length,statuses);
      assert.equal(x.reviews,0);
      if(change==='reset') assert.equal(x.input.attrs['aria-busy'],'false');
    });
  }
}
test('same-account token refresh preserves the upload', async()=>{
  const x=setup(),f=file('survey.pdf');const p=x.handleUploadedDisclosureDocs([f]);await tick();
  x.hofAuth.session={user:{id:'one'},access_token:'replacement'};
  f.gate.resolve('JVBERg==');await p;assert.deepEqual(x.names(),['survey.pdf']);
});
test('overlapping selections append in selection order', async()=>{
  const x=setup(),a=file('one.pdf'),b=file('two.pdf');
  const p=x.handleUploadedDisclosureDocs([a]);await tick();
  const q=x.handleUploadedDisclosureDocs([b]);b.gate.resolve('JVBERg==');await tick();
  assert.deepEqual(x.names(),[]);a.gate.resolve('JVBERg==');await Promise.all([p,q]);
  assert.deepEqual(x.names(),['one.pdf','two.pdf']);assert.equal(x.input.attrs['aria-busy'],'false');
});
test('removal and reordering during file read are preserved', async()=>{
  const x=setup();x.window.hofUploadedDisclosureDocs=['a','b','c'].map(name=>({name:name+'.pdf',size:100,base64:'JVBERg==',type:'other'}));
  const f=file('new.pdf'),p=x.handleUploadedDisclosureDocs([f]);await tick();
  x.removeUploadedDisclosure(1);x.moveUploadedDisclosure(1,-1);
  f.gate.resolve('JVBERg==');await p;assert.deepEqual(x.names(),['c.pdf','a.pdf','new.pdf']);
});
for(const mode of ['count','bytes']) test(`queued selections respect combined ${mode} limit`, async()=>{
  const x=setup();
  if(mode==='count')x.window.hofUploadedDisclosureDocs=[1,2,3,4].map(n=>({name:n+'.pdf',size:1}));
  const a=file('first.pdf','body',mode==='bytes'?1500000:100),b=file('second.pdf','body',mode==='bytes'?1500000:100);
  const p=x.handleUploadedDisclosureDocs([a]);await tick();const q=x.handleUploadedDisclosureDocs([b]);
  a.gate.resolve('JVBERg==');b.gate.resolve('JVBERg==');await Promise.all([p,q]);
  assert.ok(x.names().includes('first.pdf'));assert.ok(!x.names().includes('second.pdf'));
  assert.match(x.statuses.at(-1),mode==='bytes'?/2.5MB/:/up to 5/);
});
test('pending upload prevents submitting a packet before its files are ready', async()=>{
  const x=setup(),f=file('one.pdf'),p=x.handleUploadedDisclosureDocs([f]);await tick();
  assert.equal(x.validateUploadedDisclosureDocs(),false);
  f.gate.resolve('JVBERg==');await p;x.ack.checked=true;
  assert.equal(x.validateUploadedDisclosureDocs(),true);
});
test('old rejection cannot overwrite new offer status or clear its busy flag', async()=>{
  const x=setup(),a=file('old.pdf'),p=x.handleUploadedDisclosureDocs([a]);await tick();
  x.state.data={};x.resetUploadedDisclosureDraftForOffer({});
  const b=file('new.pdf'),q=x.handleUploadedDisclosureDocs([b]);await tick();
  const statuses=x.statuses.length;a.gate.reject(new Error('read failure'));await p;
  assert.equal(x.statuses.length,statuses);assert.equal(x.input.attrs['aria-busy'],'true');
  b.gate.resolve('JVBERg==');await q;assert.deepEqual(x.names(),['new.pdf']);
});
