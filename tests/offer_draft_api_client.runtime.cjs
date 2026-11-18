const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const assert=require('node:assert/strict'), {test}=require('node:test');
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const start=html.indexOf('  root.hofSaveAgentOfferDraft = async function(offerId, offer, expectedUpdatedAt)');
const end=html.indexOf('  root.hofLoadAgentOfferHistory',start);
assert.ok(start>=0&&end>start,'draft API client helper exists');
const helper=html.slice(start,end);

test('draft API helper sends only the authenticated action and draft payload',async()=>{
  const calls=[];
  const window={hofAuth:{session:{access_token:'test-token'}}};
  const context=vm.createContext({window,AbortSignal,fetch:async(...args)=>{
    calls.push(args); return {ok:true,status:201,json:async()=>({ok:true,offer:{id:'draft-id',saved:true,created:true}})};
  }});
  vm.runInContext(`(()=>{const root=window;${helper}})()`,context);
  const result=await window.hofSaveAgentOfferDraft(null,{role:'agent',property_address:'QA',offer_data:{}});
  assert.equal(result.id,'draft-id');
  assert.equal(calls.length,1);
  assert.equal(calls[0][0],'/api/admin-dashboard');
  assert.equal(calls[0][1].headers.Authorization,'Bearer test-token');
  assert.deepEqual(JSON.parse(calls[0][1].body),{
    action:'save_agent_offer_draft',offerId:null,offer:{role:'agent',property_address:'QA',offer_data:{}}
  });
});

test('prepared-packet copy recovery is returned without treating it as a write',async()=>{
  const window={hofAuth:{session:{access_token:'test-token'}}};
  const context=vm.createContext({window,AbortSignal,fetch:async()=>({
    ok:true,status:200,json:async()=>({ok:true,offer:{id:'draft-id',saved:false,created:false,copyRequired:true}})
  })});
  vm.runInContext(`(()=>{const root=window;${helper}})()`,context);
  const result=await window.hofSaveAgentOfferDraft('draft-id',{role:'agent'});
  assert.equal(result.copyRequired,true);
  assert.equal(result.saved,false);
});

test('existing drafts send the exact revision they opened with',async()=>{
  const window={hofAuth:{session:{access_token:'test-token'}}};
  const version='2026-11-18T14:00:00.123456+00:00';
  const context=vm.createContext({window,AbortSignal,fetch:async(_url,options)=>{
    assert.equal(JSON.parse(options.body).expectedUpdatedAt,version);
    return {ok:true,status:200,json:async()=>({ok:true,offer:{id:'draft-id',saved:false,copyRequired:true,conflict:true}})};
  }});
  vm.runInContext(`(()=>{const root=window;${helper}})()`,context);
  const result=await window.hofSaveAgentOfferDraft('draft-id',{role:'agent'},version);
  assert.equal(result.conflict,true);
  assert.equal(result.saved,false);
});

test('draft API failures reach the existing cloud-save recovery',async()=>{
  const window={hofAuth:{session:{access_token:'test-token'}}};
  const context=vm.createContext({window,AbortSignal,fetch:async()=>({
    ok:false,status:413,json:async()=>({error:'Draft is too large.'})
  })});
  vm.runInContext(`(()=>{const root=window;${helper}})()`,context);
  await assert.rejects(window.hofSaveAgentOfferDraft(null,{role:'agent'}),/Draft is too large/);
});
