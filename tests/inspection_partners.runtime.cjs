const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const {test} = require('node:test'), assert = require('node:assert/strict');
const profileSource = fs.readFileSync(path.join(__dirname,'../assets/partner-profile.js'),'utf8');
const bannerSource = fs.readFileSync(path.join(__dirname,'../assets/inspection-partners.js'),'utf8');
const provider = {id:'22222222-2222-4222-8222-222222222222',partner_type:'roofing',placement_tier:'exclusive_market',partner_program:'beta',
  partner_name:'Fictional QA Roofing',website_url:'https://example.com',logo_url:'https://example.com/logo.jpg',market_area:'DFW',public_contact_name:'QA Contact',public_contact_phone:'+19728376378'};
test('optional public portrait is available with or without a company logo',async()=>{
 for(const logo_url of [provider.logo_url,'']){
  const p=setup({providers:[{...provider,logo_url,public_headshot_url:'https://example.com/portrait.jpg'}]});await p.flush();
  assert.match(p.target.innerHTML,/has-portrait/);assert.match(p.target.innerHTML,/hof-partner-headshot/);
  assert.match(p.target.innerHTML,/tel:\+19728376378/);
  if(!logo_url)assert.match(p.target.innerHTML,/no-logo/);
 }
});

function setup({active = true, providers = [provider], fail = false, failOnce = false, deferred = false,legacyProfile=false} = {}) {
  let isActive = active, now = 1000, resolveRequest, failuresRemaining = failOnce ? 1 : 0;
  const calls = [], handlers = [];
  const target = {hidden:true,innerHTML:'',querySelectorAll(){
    return [...this.innerHTML.matchAll(/<a\b[^>]*>/g)].map(match => {
      const markup=match[0], id=(markup.match(/data-partner-id="([^"]+)"/)||[])[1], brand=(markup.match(/data-inspection-brand="([^"]+)"/)||[])[1];
      return {dataset:{partnerId:id,inspectionBrand:brand},addEventListener:(event,fn)=>handlers.push({event,fn,id:id||brand,markup})};
    });
  },querySelector(selector){
    return selector === '[data-partner-retry]' && this.innerHTML.includes('data-partner-retry')
      ? {disabled:false,textContent:'Try again',addEventListener:(event,fn)=>handlers.push({event,fn,retry:true})}
      : null;
  }};
  const step = {classList:{contains:()=>isActive}};
  let observer;
  const sandbox = {window:{},URL,URLSearchParams,AbortController,setTimeout,clearTimeout,Date:{now:()=>now},Promise,Set,
    document:{readyState:'complete',addEventListener(){},getElementById:id=>id==='step6'?step:target},
    MutationObserver:class {constructor(fn){observer=fn;}observe(){}},
    fetch:async(url, options)=>{
      calls.push({url,options});
      if(options?.method==='POST') return {ok:true,json:async()=>({ok:true})};
      if(fail || failuresRemaining > 0) { if(failuresRemaining > 0) failuresRemaining--; throw new Error('fixture unavailable'); }
      if(deferred) return new Promise(resolve=>{resolveRequest=()=>resolve({ok:true,json:async()=>({ok:true,partners:providers})});});
      return {ok:true,json:async()=>({ok:true,partners:providers})};
    },
  };
  vm.createContext(sandbox);vm.runInContext(profileSource,sandbox);
  if(legacyProfile)sandbox.window.hofPartnerProfile={...sandbox.window.hofPartnerProfile,portrait:undefined};
  vm.runInContext(bannerSource,sandbox);
  return {sandbox,target,calls,handlers,setActive:value=>{isActive=value;observer();},resolve:()=>resolveRequest(),setTime:value=>{now=value;},
    flush:()=>new Promise(resolve=>setImmediate(resolve))};
}

test('cached pre-portrait helper cannot hide an otherwise valid roofing banner',async()=>{
 const p=setup({legacyProfile:true});await p.flush();assert.equal(p.target.hidden,false);
 assert.match(p.target.innerHTML,/Fictional QA Roofing/);assert.match(p.target.innerHTML,/tel:\+19728376378/);
});

test('active inspection step uses central public profile, correct logo and separate website/call actions',async()=>{
  const p=setup();await p.flush();
  assert.equal(p.target.hidden,false);
  assert.match(p.target.innerHTML,/Fictional QA Roofing/);
  assert.match(p.target.innerHTML,/logo\.jpg/);
  assert.match(p.target.innerHTML,/Roofing · Sponsored · Premier Partner/);
  assert.match(p.target.innerHTML,/tel:\+19728376378/);
  assert.match(p.target.innerHTML,/Visit website/);
  assert.match(p.target.innerHTML,/Optional service providers/);
  assert.equal(p.calls.filter(c=>c.options?.method!=='POST').length,1);
});

test('no provider lookup or analytics happens before the inspection step is visible',async()=>{
  const p=setup({active:false});await p.flush();
  assert.equal(p.calls.length,0);assert.equal(p.target.hidden,true);
  p.setActive(true);await p.flush();
  assert.equal(p.target.hidden,false);
});

test('leaving the step during loading does not render or count a hidden impression',async()=>{
  const p=setup({deferred:true});
  p.setActive(false);p.resolve();await p.flush();
  assert.equal(p.target.hidden,true);
  assert.equal(p.calls.filter(c=>c.options?.method==='POST').length,0);
  p.setActive(true);await p.flush();
  assert.equal(p.target.hidden,false);
  assert.equal(p.calls.filter(c=>c.options?.method!=='POST').length,1);
});

test('temporary directory failure gives a non-blocking, accessible retry',async()=>{
  const p=setup({fail:true});await p.flush();assert.equal(p.target.hidden,false);
  assert.match(p.target.innerHTML,/role="status" aria-live="polite"/);
  assert.match(p.target.innerHTML,/continue without them/);assert.match(p.target.innerHTML,/data-partner-retry/);
  assert.equal(p.calls.filter(c=>c.options?.method==='POST').length,0);
});

test('retry after a temporary directory failure renders the provider card',async()=>{
  const p=setup({failOnce:true});await p.flush();assert.equal(p.target.hidden,false);
  p.handlers.find(handler=>handler.retry).fn();await p.flush();
  assert.equal(p.target.hidden,false);assert.match(p.target.innerHTML,/Fictional QA Roofing/);
  assert.equal(p.calls.filter(c=>c.options?.method!=='POST').length,2);
});

test('no active roofing profile stays hidden without blocking or showing an empty advertisement',async()=>{
  for(const options of [{providers:[]},{providers:[{...provider,partner_type:'lender'}]},{providers:[{...provider,website_url:'javascript:evil'}]}]){
    const p=setup(options);await p.flush();assert.equal(p.target.hidden,true);assert.equal(p.calls.filter(c=>c.options?.method==='POST').length,0);
  }
});

test('profile values cannot inject markup, credentials or private-contact fallback',async()=>{
  const p=setup({providers:[{...provider,partner_name:'<script>evil</script>',market_area:'<img onerror="evil">',logo_url:'https://user:pass@example.com/logo.jpg',public_contact_phone:'',contact_phone:'+19728376378',contact_email:'private@example.test'}]});await p.flush();
  assert.match(p.target.innerHTML,/&lt;script&gt;/);
  assert.doesNotMatch(p.target.innerHTML,/<script>|<img onerror=|user:pass|private@example|tel:/);
});

test('impression and clicks carry only allowed aggregate placement metadata, never customer or offer data',async()=>{
  const p=setup();await p.flush();
  p.handlers.find(h=>h.markup.includes('tel:')).fn();await p.flush();
  const events=p.calls.filter(c=>c.options?.method==='POST').map(c=>JSON.parse(c.options.body));
  assert.deepEqual(events.map(e=>e.event_type),['partner_directory_impression','partner_directory_outbound_click']);
  for(const event of events){
    assert.deepEqual(Object.keys(event).sort(),['directory_surface','event_type','partner_id','partner_type','placement_tier','request_type'].sort());
    assert.equal(event.directory_surface,'inspection_interview');
    assert.equal(event.partner_id,provider.id);
    assert.equal(event.placement_tier,'exclusive_market');
  }
  p.setActive(false);p.setActive(true);await p.flush();
  assert.equal(p.calls.filter(c=>c.options?.method==='POST').length,2);
});

test('inspection and follow-up share one pending/cached lookup, then refresh after five minutes',async()=>{
  const p=setup({deferred:true});
  const followup=p.sandbox.window.hofPartnerProfile.load('workflow');
  assert.equal(p.calls.length,1);p.resolve();await followup;await p.flush();
  await p.sandbox.window.hofPartnerProfile.load('workflow');assert.equal(p.calls.filter(c=>c.options?.method!=='POST').length,1);
  p.setTime(302000);
  const fresh=p.sandbox.window.hofPartnerProfile.load('workflow');
  assert.equal(p.calls.filter(c=>c.options?.method!=='POST').length,2);p.resolve();await fresh;
});

test('public directory cache permits a new attempt after an unsuccessful lookup',async()=>{
  const p=setup({active:false,fail:true});
  await assert.rejects(p.sandbox.window.hofPartnerProfile.load());
  await assert.rejects(p.sandbox.window.hofPartnerProfile.load());
  assert.equal(p.calls.length,2);
});

test('a confirmed empty response clears the previous retry message',async()=>{
  const p=setup({failOnce:true,providers:[]});await p.flush();
  assert.equal(p.target.hidden,false);
  p.handlers.find(handler=>handler.retry).fn();await p.flush();
  assert.equal(p.target.hidden,true);
  assert.equal(p.target.innerHTML,'');
});
