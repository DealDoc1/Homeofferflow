const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{test}=require('node:test');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const script=html.match(/<script id="hof-standalone-agreement-signing-v1">([\s\S]*?)<\/script>/)?.[1];
assert.ok(script);
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {resolve,reject,promise};}
const tick=()=>new Promise(setImmediate);
const pdfHeaders={get:()=> 'application/pdf'};
const samplePdf = new Blob(['%PDF-1.7\nfixture'], {type:'application/pdf'});
const newerPdf = new Blob(['%PDF-1.7\nnewer fixture'], {type:'application/pdf'});
function setup(){
  const reads=[],previews=[],downloads=[],notices=[];
  const timers=new Map();
  let nextTimer=0;
  const root={hofAuth:{session:{user:{id:'actor'},access_token:'qa-token'}},
    hofShowPdfPreview:(blob,code)=>previews.push({blob,code}),announceWorkspaceStatus:message=>notices.push(message),setTimeout:()=>{}};
  const document={readyState:'loading',addEventListener:()=>{},body:{appendChild:()=>{}},
    createElement:()=>({click(){downloads.push(this.download);},remove(){}})};
  const context=vm.createContext({window:root,document,console:{error(){}},AbortController,
    setTimeout:(callback,ms)=>{assert.equal(ms,60000);timers.set(++nextTimer,callback);return nextTimer;},
    clearTimeout:id=>timers.delete(id),
    URL:{createObjectURL:()=> 'blob:fictional',revokeObjectURL:()=>{}},
    fetch:(url,options)=>{const pending=deferred();reads.push({url,options,...pending});return pending.promise;}});
  const instrumented=script.replace('  const previous = root.renderAccountDashboard;',
    '  root.queueQa={previewAgreementPdf,downloadCompletedAgreementPdf};\n  const previous = root.renderAccountDashboard;');
  vm.runInContext(instrumented,context);
  const button={isConnected:true,disabled:false,textContent:'Preview'};
  return {root,reads,previews,downloads,notices,button,timers};
}
test('a stalled completed preview restores the button and can be retried',async()=>{
  const x=setup();
  const agreement={id:'owned',form_code:'TXR-1507',status:'signed',signwell_document_id:'qa-doc'};
  const pending=x.root.queueQa.previewAgreementPdf(agreement,x.button);
  const {signal}=x.reads[0].options;
  assert.equal(x.button.textContent,'Opening PDF…');
  x.reads[0].resolve({ok:true,headers:pdfHeaders,blob:()=>new Promise((_,reject)=>{
    signal.addEventListener('abort',()=>reject(signal.reason),{once:true});
  })});
  await tick();
  x.timers.values().next().value();
  await pending;
  assert.deepEqual(x.previews,[]);
  assert.match(x.notices[0],/took too long/);
  assert.equal(x.button.disabled,false);
  assert.equal(x.button.textContent,'Preview');
  assert.equal(x.timers.size,0);
  const retry=x.root.queueQa.previewAgreementPdf(agreement,x.button);
  x.reads[1].resolve({ok:true,headers:pdfHeaders,blob:async()=>samplePdf});
  await retry;
  assert.deepEqual(x.previews,[{blob:samplePdf,code:'TXR-1507'}]);
  assert.equal(x.timers.size,0);
});
for(const operation of ['previewAgreementPdf','downloadCompletedAgreementPdf']){
  test(`${operation}: an old account response cannot show or download its document in a new account`,async()=>{
    const x=setup(),pending=x.root.queueQa[operation]({id:'owned-draft',form_code:'TXR-1101',status:'draft'},x.button);
    x.root.hofAuth.session.user.id='other-actor';
    x.reads[0].resolve({ok:true,headers:pdfHeaders,blob:async()=>samplePdf});await pending;
    assert.deepEqual(x.previews,[]);assert.deepEqual(x.downloads,[]);assert.deepEqual(x.notices,[]);
  });
  test(`${operation}: account change while the PDF body is loading is also discarded`,async()=>{
    const x=setup(),content=deferred(),pending=x.root.queueQa[operation]({id:'owned-draft',form_code:'TXR-1101',status:'draft'},x.button);
    x.reads[0].resolve({ok:true,headers:pdfHeaders,blob:()=>content.promise});await tick();x.root.__hofAccountProfileEpoch=1;
    content.resolve(samplePdf);await pending;
    assert.deepEqual(x.previews,[]);assert.deepEqual(x.downloads,[]);
  });
  test(`${operation}: a stale failed request cannot replace the next account’s status`,async()=>{
    const x=setup(),pending=x.root.queueQa[operation]({id:'owned-draft',form_code:'TXR-1101',status:'draft'},x.button);
    x.root.hofAuth.session.user.id='other-actor';x.reads[0].reject(new Error('Synthetic connection loss'));await pending;
    assert.deepEqual(x.notices,[]);assert.equal(x.button.disabled,false);
  });
}
test('the current agent can still preview its own prepared listing agreement',async()=>{
  const x=setup(),pending=x.root.queueQa.previewAgreementPdf({id:'owned-draft',form_code:'TXR-1101',status:'draft'},x.button);
  x.reads[0].resolve({ok:true,headers:pdfHeaders,blob:async()=>samplePdf});await pending;
  assert.deepEqual(x.previews,[{blob:samplePdf,code:'TXR-1101'}]);assert.equal(x.button.disabled,false);
});
test('the current agent can still download its own completed agreement',async()=>{
  const x=setup(),pending=x.root.queueQa.downloadCompletedAgreementPdf({id:'owned-draft',form_code:'TXR-1101',status:'signed'},x.button);
  x.reads[0].resolve({ok:true,headers:pdfHeaders,blob:async()=>samplePdf});await pending;
  assert.deepEqual(x.downloads,['TXR-1101-completed.pdf']);assert.equal(x.button.disabled,false);
});

test('a stalled signed download can be retried without starting a duplicate download',async()=>{
  const x=setup();
  const agreement={id:'owned',form_code:'TXR-1507',status:'signed'};
  const pending=x.root.queueQa.downloadCompletedAgreementPdf(agreement,x.button);
  const {signal}=x.reads[0].options;
  assert.equal(x.button.textContent,'Preparing…');
  x.reads[0].resolve({ok:true,headers:pdfHeaders,blob:()=>new Promise((_,reject)=>{
    signal.addEventListener('abort',()=>reject(signal.reason),{once:true});
  })});
  await tick();
  x.timers.values().next().value();
  await pending;
  assert.deepEqual(x.downloads,[]);
  assert.match(x.notices[0],/took too long/);
  assert.equal(x.button.disabled,false);
  assert.equal(x.button.textContent,'Preview');
  assert.equal(x.timers.size,0);
  const retry=x.root.queueQa.downloadCompletedAgreementPdf(agreement,x.button);
  x.reads[1].resolve({ok:true,headers:pdfHeaders,blob:async()=>samplePdf});
  await retry;
  assert.deepEqual(x.downloads,['TXR-1507-completed.pdf']);
  assert.match(x.notices.at(-1),/Download started/);
  assert.equal(x.timers.size,0);
});

for(const operation of ['previewAgreementPdf','downloadCompletedAgreementPdf']){
  for (const invalid of ['', '<html>Temporary error</html>']) {
    test(operation + ' refuses invalid bytes labeled as a PDF', async () => {
      const x = setup();
      const pending = x.root.queueQa[operation]({id:'qa',status:'signed',signwell_document_id:'qa-doc'},x.button);
      x.reads[0].resolve({ok:true,headers:pdfHeaders,blob:async()=>new Blob([invalid])});
      await pending;
      assert.deepEqual(x.previews,[]);
      assert.deepEqual(x.downloads,[]);
      assert.match(x.notices[0],/Please try again/);
      assert.equal(x.button.disabled,false);
    });
  }
  test(operation + ' discards a PDF body that resolves after the deadline', async () => {
    const x = setup(), content = deferred();
    const pending = x.root.queueQa[operation]({id:'qa',status:'signed',signwell_document_id:'qa-doc'},x.button);
    x.reads[0].resolve({ok:true,headers:pdfHeaders,blob:()=>content.promise});
    await tick();
    x.timers.values().next().value();
    content.resolve(samplePdf);
    await pending;
    assert.deepEqual(x.previews,[]);
    assert.deepEqual(x.downloads,[]);
    assert.match(x.notices[0],/took too long/);
    assert.equal(x.button.disabled,false);
  });
  test(`${operation}: a successful HTML response shows recovery guidance`,async()=>{
    const x=setup(),pending=x.root.queueQa[operation]({id:'qa',status:'signed',signwell_document_id:'qa-doc'},x.button);
    x.reads[0].resolve({ok:true,headers:{get:()=> 'text/html'}});
    await pending;
    assert.deepEqual(x.previews,[]);
    assert.deepEqual(x.downloads,[]);
    assert.match(x.notices[0],/Please try again/);
    assert.equal(x.button.disabled,false);
  });
}
test('an older preview cannot replace the most recently requested document',async()=>{
  const x=setup();
  const older=x.root.queueQa.previewAgreementPdf({id:'older',form_code:'TXR-1101'},x.button);
  const newer=x.root.queueQa.previewAgreementPdf({id:'newer',form_code:'TXR-1506'},{...x.button});
  x.reads[1].resolve({ok:true,headers:pdfHeaders,blob:async()=>newerPdf});
  await newer;
  x.reads[0].resolve({ok:true,headers:pdfHeaders,blob:async()=>samplePdf});
  await older;
  assert.deepEqual(x.previews,[{blob:newerPdf,code:'TXR-1506'}]);
});
