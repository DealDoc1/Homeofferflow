const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'directory.html'), 'utf8');
const source = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('const labels ='));
const profile = fs.readFileSync(path.join(root, 'assets/partner-profile.js'), 'utf8');
const fixture = {id:'22222222-2222-4222-8222-222222222222',partner_type:'roofing',partner_name:'Test Roofing',partner_program:'beta',placement_tier:'founding',market_area:'Test market',website_url:'https://example.com/',logo_url:'https://example.com/logo.jpg',public_contact_name:'Test Contact',public_contact_phone:'+19725550123',public_description:'First approved sentence. Second approved sentence. '+ 'More approved details. '.repeat(15)};
const tick = () => new Promise(resolve => setImmediate(resolve));
function deferred() { let resolve, reject; const promise = new Promise((a,b) => {resolve=a;reject=b;}); return {promise,resolve,reject}; }
function setup({legacyProfile=false,strictPortrait=false}={}) {
  const requests=[], events=[], timers=new Map(), elements={};
  let timerId=0;
  for(const id of ['category','market','filters','status','results']) {
    const classes=new Set(), listeners={};
    elements[id]={value:'',innerHTML:'',textContent:'',attributes:{},listeners,
      setAttribute(k,v){this.attributes[k]=v;},
      addEventListener(k,fn){listeners[k]=fn;},querySelector(){return null;},
      classList:{remove:k=>classes.delete(k),toggle(k,on){on?classes.add(k):classes.delete(k);},contains:k=>classes.has(k)}};
  }
  const button={disabled:false,attributes:{},textContent:'Search providers',setAttribute(k,v){this.attributes[k]=v;}};
  elements.filters.querySelector=()=>button;
  const store=new Map();
  const window={location:{search:'',href:'https://www.homeofferflow.com/directory',origin:'https://www.homeofferflow.com'},va(){}};
  const context=vm.createContext({window,URL,URLSearchParams,AbortController,
    document:{addEventListener(){},getElementById:id=>elements[id],querySelectorAll:()=>[]},
    sessionStorage:{getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v)},
    history:{replaceState(){}},
    setTimeout(fn){const id=++timerId;timers.set(id,fn);return id;},clearTimeout:id=>timers.delete(id),
    fetch(url,options={}){
      if(options.method==='POST'){events.push(JSON.parse(options.body));return Promise.resolve({ok:true,json:async()=>({ok:true})});}
      const pending=deferred();requests.push({url,options,...pending});return pending.promise;
    }});
  vm.runInContext(profile,context);
  if(legacyProfile)context.window.hofPartnerProfile={...context.window.hofPartnerProfile,portrait:undefined};
  const renderSource=strictPortrait?source.replace('(window.hofPartnerProfile.portrait?.(provider, esc) || "")','window.hofPartnerProfile.portrait(provider, esc)'):source;
  vm.runInContext(renderSource,context);
  const respond=(index,partners=[fixture],ok=true)=>requests[index].resolve({ok,json:async()=>({ok,partners})});
  const search=category=>{elements.category.value=category;return elements.category.listeners.change({preventDefault(){}});};
  return {requests,events,timers,elements,button,respond,search};
}
async function run() {
  {
    const broken=setup({legacyProfile:true,strictPortrait:true});broken.respond(0);await tick();
    assert(broken.elements.results.innerHTML.includes('data-directory-retry'));
    const fixed=setup({legacyProfile:true});fixed.respond(0);await tick();
    assert(fixed.elements.results.innerHTML.includes('Test Roofing'));
    assert(fixed.elements.results.innerHTML.includes('tel:+19725550123'));
    assert(!fixed.elements.results.innerHTML.includes('data-directory-retry'));
  }
  {
    const s=setup();s.respond(0);await tick();
    assert(s.elements.results.classList.contains('single-provider'));
    const result=s.elements.results.innerHTML;
    assert(result.includes('First approved sentence. Second approved sentence.'));
    assert(result.includes('<details class="provider-description">'));
    assert(result.includes(fixture.public_description.trim()));
    assert(result.includes('tel:+19725550123'));
    assert(result.includes('Beta partner · Core Partner'));
    assert.equal(s.button.disabled,false);assert.equal(s.timers.size,0);
  }
  {
    const s=setup();const latest=s.search('roofing');
    assert(s.requests[0].options.signal.aborted);
    s.respond(0,[]);await tick();
    assert.equal(s.elements.results.innerHTML,'');assert.equal(s.button.disabled,true);
    assert.equal(s.elements.results.attributes['aria-busy'],'true');
    assert(!s.events.some(e=>e.event_type==='partner_directory_empty_search'));
    s.respond(1);await latest;assert(s.elements.results.innerHTML.includes('Test Roofing'));
  }
  {
    const s=setup();const latest=s.search('inspection');
    s.respond(1,[{...fixture,partner_name:'Latest Inspector',partner_type:'inspection'}]);await latest;
    s.respond(0);await tick();
    assert(s.elements.results.innerHTML.includes('Latest Inspector'));
    assert(!s.elements.results.innerHTML.includes('Test Roofing'));
    assert.equal(s.events.filter(e=>e.event_type==='partner_directory_impression').length,1);
  }
  {
    const s=setup(), body=deferred();
    s.requests[0].resolve({ok:true,json:()=>body.promise});await tick();
    const latest=s.search('roofing');s.respond(1);await latest;
    body.resolve({ok:true,partners:[]});await tick();
    assert(s.elements.results.innerHTML.includes('Test Roofing'));
    assert(!s.events.some(e=>e.event_type==='partner_directory_empty_search'));
  }
  {
    const s=setup();const latest=s.search('roofing');s.respond(1);await latest;
    s.requests[0].reject(new Error('Old network failure'));await tick();
    assert(s.elements.results.innerHTML.includes('Test Roofing'));
    assert.equal(s.button.disabled,false);
  }
  {
    const s=setup();s.requests[0].reject(new Error('Network failure'));await tick();
    assert(s.elements.results.innerHTML.includes('data-directory-retry'));
    assert.equal(s.button.disabled,false);assert.equal(s.timers.size,0);
    const retry=s.search('roofing');s.respond(1);await retry;
    assert(s.elements.results.innerHTML.includes('Test Roofing'));
  }
  {
    const s=setup();s.requests[0].resolve({ok:true,json:async()=>({ok:false,partners:[fixture]})});await tick();
    assert(s.elements.results.innerHTML.includes('data-directory-retry'));
    assert(!s.elements.results.innerHTML.includes('Test Roofing'));
  }
  {
    const s=setup();[...s.timers.values()][0]();
    assert(s.requests[0].options.signal.aborted);
    s.requests[0].reject(new DOMException('Timeout','AbortError'));await tick();
    assert.equal(s.button.disabled,false);assert.equal(s.elements.results.attributes['aria-busy'],'false');
    assert(s.elements.results.innerHTML.includes('data-directory-retry'));
  }
  {
    const s=setup();s.respond(0,[fixture,{...fixture,id:'33333333-3333-4333-8333-333333333333',partner_name:'Second provider'}]);await tick();
    assert(!s.elements.results.classList.contains('single-provider'));
    assert.equal((s.elements.results.innerHTML.match(/<article/g)||[]).length,2);
  }
  {
    const s=setup();s.respond(0,[{...fixture,logo_url:'javascript:alert(1)',partner_name:'<img src=x onerror=alert(1)>',public_description:'<script>bad</script>',website_url:'https://user:password@example.com/'}]);await tick();
    const result=s.elements.results.innerHTML;
    assert(result.includes('class="card no-logo"'));
    assert(result.includes('&lt;img'));assert(!result.includes('<script>'));
    assert(!result.includes('javascript:'));assert(!result.includes('user:password'));
  }
  console.log('12 actual-source provider search cases passed, including cached-library reproduction and recovery');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
