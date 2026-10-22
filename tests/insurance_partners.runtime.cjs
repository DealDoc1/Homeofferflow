const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const {test} = require('node:test'), assert = require('node:assert/strict');
const profileSource = fs.readFileSync(path.join(__dirname,'../assets/partner-profile.js'),'utf8');
const source = fs.readFileSync(path.join(__dirname,'../assets/insurance-partners.js'),'utf8');
const provider = {id:'22222222-2222-4222-8222-222222222222',partner_type:'insurance',placement_tier:'exclusive_market',partner_program:'beta',partner_name:'Fictional QA Insurance',website_url:'https://example.com/agent',logo_url:'https://example.com/logo.jpg',market_area:'North Texas; Texas excluding coastal areas',public_contact_name:'QA Agent',public_contact_phone:'+19034362470'};
test('optional public portrait leaves insurance choice and contact routing intact',async()=>{
 const p=setup({providers:[{...provider,public_headshot_url:'https://example.com/portrait.jpg'}]});await p.flush();
 assert.match(p.target.innerHTML,/has-portrait/);assert.match(p.target.innerHTML,/hof-partner-headshot/);
 assert.match(p.target.innerHTML,/tel:\+19034362470/);assert.match(p.target.innerHTML,/not shared automatically/);
});
function setup({active=true,open=true,providers=[provider],fail=false,deferred=false,missing=false,legacyProfile=false}={}) {
  let activeStep=active, resolveRequest, observer, toggle;
  const calls=[], handlers=[];
  const target={hidden:true,innerHTML:'',querySelectorAll(){return [...this.innerHTML.matchAll(/<a\b[^>]*>/g)].map(match=>{
    const markup=match[0],id=(markup.match(/data-partner-id="([^"]+)"/)||[])[1],brand=(markup.match(/data-insurance-brand="([^"]+)"/)||[])[1];
    return {dataset:{partnerId:id,insuranceBrand:brand},addEventListener:(_,fn)=>handlers.push({markup,fn})};
  });}};
  const step={classList:{contains:()=>activeStep}}, planner={open,addEventListener:(_,fn)=>{toggle=fn;}};
  const sandbox={window:{},URL,URLSearchParams,Date,Promise,Set,document:{readyState:'complete',addEventListener(){},getElementById:id=>missing?null:({step4:step,paymentCalcCard:planner,hofInsurancePartners:target}[id])},
    MutationObserver:class{constructor(fn){observer=fn;}observe(){}},fetch:async(url,options)=>{
      calls.push({url,options}); if(options) return {ok:true,json:async()=>({ok:true})};
      if(fail)throw Error('unavailable');
      if(deferred)return new Promise(resolve=>{resolveRequest=()=>resolve({ok:true,json:async()=>({ok:true,partners:providers})});});
      return {ok:true,json:async()=>({ok:true,partners:providers})};
    }};
  vm.createContext(sandbox);vm.runInContext(profileSource,sandbox);
  if(legacyProfile)sandbox.window.hofPartnerProfile={...sandbox.window.hofPartnerProfile,portrait:undefined};
  vm.runInContext(source,sandbox);
  return {target,calls,handlers,open:value=>{planner.open=value;toggle();},active:value=>{activeStep=value;observer();},resolve:()=>resolveRequest(),flush:()=>new Promise(resolve=>setImmediate(resolve))};
}
test('cached pre-portrait helper preserves insurance planning and contact routing',async()=>{
 const p=setup({legacyProfile:true});await p.flush();assert.equal(p.target.hidden,false);
 assert.match(p.target.innerHTML,/Fictional QA Insurance/);assert.match(p.target.innerHTML,/tel:\+19034362470/);
});
test('renders approved central insurance profile with separate website and call actions and choice',async()=>{
  const p=setup();await p.flush();assert.equal(p.target.hidden,false);
  for(const text of ['Fictional QA Insurance','Home insurance · Beta partner · Premier Partner','North Texas','excluding coastal','tel:+19034362470','Visit website','Optional service providers','not shared automatically']){
    assert.ok(p.target.innerHTML.includes(text),text);
  }
  assert.equal(p.calls.filter(c=>!c.options).length,1);
});
test('no lookup before both finance step and optional planner are open',async()=>{
  const p=setup({active:false,open:false});await p.flush();assert.equal(p.calls.length,0);
  p.open(true);await p.flush();assert.equal(p.calls.length,0);
  p.active(true);await p.flush();assert.equal(p.target.hidden,false);
});
test('closing planner during lookup does not show or count a hidden card, reopening reuses cache',async()=>{
  const p=setup({deferred:true});p.open(false);p.resolve();await p.flush();
  assert.equal(p.target.hidden,true);assert.equal(p.calls.filter(c=>c.options).length,0);
  p.open(true);await p.flush();assert.equal(p.target.hidden,false);assert.equal(p.calls.filter(c=>!c.options).length,1);
});
test('unavailable directory, wrong category and bad websites stay hidden without blocking',async()=>{
  for(const options of [{missing:true},{fail:true},{providers:[]},{providers:[{...provider,partner_type:'roofing'}]},{providers:[{...provider,website_url:'javascript:evil'}]}]){
    const p=setup(options);await p.flush();assert.equal(p.target.hidden,true);assert.equal(p.calls.filter(c=>c.options).length,0);
  }
});
test('escapes content and never falls back to private contact data or unsafe artwork',async()=>{
  const p=setup({providers:[{...provider,partner_name:'<script>evil</script>',market_area:'<img onerror=evil>',logo_url:'https://user:pass@example.com/logo.jpg',public_contact_phone:'',contact_phone:'+19034362470',contact_email:'private@example.test'}]});await p.flush();
  assert.match(p.target.innerHTML,/&lt;script&gt;/);assert.doesNotMatch(p.target.innerHTML,/<script>|<img onerror|user:pass|private@example|tel:/);
});
test('click/impression analytics contain placement metadata only and impressions deduplicate',async()=>{
  const p=setup();await p.flush();p.handlers.find(h=>h.markup.includes('tel:')).fn();await p.flush();
  const events=p.calls.filter(c=>c.options).map(c=>JSON.parse(c.options.body));
  assert.deepEqual(events.map(e=>e.event_type),['partner_directory_impression','partner_directory_outbound_click']);
  for(const event of events){assert.equal(event.directory_surface,'insurance_planning');assert.deepEqual(Object.keys(event).sort(),['directory_surface','event_type','partner_id','partner_type','placement_tier','request_type'].sort());}
  p.open(false);p.open(true);await p.flush();assert.equal(p.calls.filter(c=>c.options).length,2);
});
