const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{test}=require('node:test');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const script=html.match(/<script id="hof-standalone-agreement-signing-v1">([\s\S]*?)<\/script>/)?.[1];
assert.ok(script);
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {resolve,reject,promise};}
const tick=()=>new Promise(setImmediate);
function setup(){
  const reads=[],previews=[],downloads=[],notices=[];
  const root={hofAuth:{session:{user:{id:'actor'},access_token:'qa-token'}},
    hofShowPdfPreview:(blob,code)=>previews.push({blob,code}),announceWorkspaceStatus:message=>notices.push(message),setTimeout:()=>{}};
  const document={readyState:'loading',addEventListener:()=>{},body:{appendChild:()=>{}},
    createElement:()=>({click(){downloads.push(this.download);},remove(){}})};
  const context=vm.createContext({window:root,document,console:{error(){}},
    URL:{createObjectURL:()=> 'blob:fictional',revokeObjectURL:()=>{}},
    fetch:(url,options)=>{const pending=deferred();reads.push({url,options,...pending});return pending.promise;}});
  const instrumented=script.replace('  const previous = root.renderAccountDashboard;',
    '  root.queueQa={previewAgreementPdf,downloadCompletedAgreementPdf};\n  const previous = root.renderAccountDashboard;');
  vm.runInContext(instrumented,context);
  const button={disabled:false,textContent:'Preview'};
  return {root,reads,previews,downloads,notices,button};
}
for(const operation of ['previewAgreementPdf','downloadCompletedAgreementPdf']){
  test(`${operation}: an old account response cannot show or download its document in a new account`,async()=>{
    const x=setup(),pending=x.root.queueQa[operation]({id:'owned-draft',form_code:'TXR-1101',status:'draft'},x.button);
    x.root.hofAuth.session.user.id='other-actor';
    x.reads[0].resolve({ok:true,blob:async()=>({fictional:true})});await pending;
    assert.deepEqual(x.previews,[]);assert.deepEqual(x.downloads,[]);assert.deepEqual(x.notices,[]);
  });
  test(`${operation}: account change while the PDF body is loading is also discarded`,async()=>{
    const x=setup(),content=deferred(),pending=x.root.queueQa[operation]({id:'owned-draft',form_code:'TXR-1101',status:'draft'},x.button);
    x.reads[0].resolve({ok:true,blob:()=>content.promise});await tick();x.root.__hofAccountProfileEpoch=1;
    content.resolve({fictional:true});await pending;
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
  x.reads[0].resolve({ok:true,blob:async()=> 'fictional-pdf'});await pending;
  assert.deepEqual(x.previews,[{blob:'fictional-pdf',code:'TXR-1101'}]);assert.equal(x.button.disabled,false);
});
test('the current agent can still download its own completed agreement',async()=>{
  const x=setup(),pending=x.root.queueQa.downloadCompletedAgreementPdf({id:'owned-draft',form_code:'TXR-1101',status:'signed'},x.button);
  x.reads[0].resolve({ok:true,blob:async()=> 'fictional-pdf'});await pending;
  assert.deepEqual(x.downloads,['TXR-1101-completed.pdf']);assert.equal(x.button.disabled,false);
});
