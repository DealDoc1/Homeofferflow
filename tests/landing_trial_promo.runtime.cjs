const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
function source(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert.ok(a >= 0 && b > a, 'Actual source boundary is present');
  return html.slice(a, b);
}
function setup({signedIn=false, status='inactive', audience='agent'}={}) {
  const nodes=new Map(), events=[];
  const c={root:null, hofAuth:{session:signedIn?{user:{id:'fictional'}}:null,subscription:{status}},
    oldUpdateAuthUI:()=>events.push('account-refresh'),
    syncAccountLandingAudience:()=>{},addEventListener:()=>{},
    recordOnDemandTrialEntry:surface=>events.push(surface),
    document:{getElementById:id=>nodes.get(id)||null,
      querySelector:selector=>selector==='.hero-actions'
        ? {appendChild:node=>nodes.set(node.id,node)} : {dataset:{audience}},
      createElement:()=>({attributes:{},listeners:{},
        setAttribute(name,value){this.attributes[name]=value;},
        addEventListener(name,callback){this.listeners[name]=callback;},
        remove(){nodes.delete(this.id);}})}};
  c.root=c;
  vm.createContext(c);
  vm.runInContext(source('  function syncOnDemandHeroTrialCta(type){','  const oldSetAudience'),c);
  vm.runInContext(source('  root.updateAuthUI = function updateAuthUI(){\n    if (typeof oldUpdateAuthUI',"  document.addEventListener('DOMContentLoaded', function(){\n    addLandingPathStrip();"),c);
  return {c,nodes,events};
}
test('a guest agent retains one explicit unchanged public trial invitation',()=>{
  const x=setup();
  x.c.syncOnDemandHeroTrialCta('agent');x.c.syncOnDemandHeroTrialCta('agent');
  assert.equal(x.nodes.size,1);
  const link=x.nodes.get('onDemandHeroTrialCta');
  assert.equal(link.textContent,'OnDemand agent? Start 60 days free');
  assert.match(link.href,/^\/ondemand\?/);
  assert.match(link.attributes['aria-label'],/card required/);
  link.listeners.click();
  assert.deepEqual(x.events,['agent_hero_secondary_cta']);
});
for (const status of ['active','trialing','free_admin','inactive','past_due','canceled','']) {
  test(`${status||'unresolved'} signed-in account has no duplicate acquisition CTA`,()=>{
    const x=setup({signedIn:true,status});
    const before=JSON.stringify(x.c.hofAuth);
    x.c.syncOnDemandHeroTrialCta('agent');
    assert.equal(x.nodes.size,0);
    assert.equal(JSON.stringify(x.c.hofAuth),before);
    assert.deepEqual(x.events,[]);
  });
}
test('real UI refresh removes a stale guest promotion when sign-in resolves',()=>{
  const x=setup();
  x.c.syncOnDemandHeroTrialCta('agent');
  x.c.hofAuth.session={user:{id:'fictional'}};
  x.c.updateAuthUI();
  assert.equal(x.nodes.has('onDemandHeroTrialCta'),false);
  assert.deepEqual(x.events,['account-refresh']);
  x.c.hofAuth.session=null;
  x.c.updateAuthUI();
  assert.equal(x.nodes.has('onDemandHeroTrialCta'),true);
});
for(const audience of ['homebuyer','investor','fsbo'])test(`${audience} stays free of agent trial promotion`,()=>{
  const x=setup({audience});
  x.c.syncOnDemandHeroTrialCta('agent');
  x.c.updateAuthUI();
  assert.equal(x.nodes.has('onDemandHeroTrialCta'),false);
});

for(const fullLabel of ['Build Your Offer →','Start a Transaction →','Open Investor Workspace →','Free Seller Plan →','Resume Offer →']) {
  test(`compact navigation preserves the full ${fullLabel} action`,()=>{
    const button={textContent:fullLabel,dataset:{},attributes:{},setAttribute(name,value){this.attributes[name]=value;}};
    const c={root:null,document:{getElementById:()=>button}};c.root=c;
    vm.createContext(c);
    vm.runInContext(source('  root.syncCompactNavLabel = function syncCompactNavLabel()', '  function syncLandingPathContext('),c);
    c.syncCompactNavLabel();
    assert.equal(button.textContent,fullLabel);
    assert.equal(button.attributes['aria-label'],fullLabel);
    assert.equal(button.dataset.compactLabel,fullLabel.startsWith('Resume')?'Resume →':'Start →');
  });
}
