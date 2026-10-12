const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');
const html = fs.readFileSync(path.resolve(__dirname,'..','index.html'),'utf8');
function section(start,end) {
  const from=html.indexOf(start), to=html.indexOf(end,from);
  assert.ok(from>=0 && to>from);
  return html.slice(from,to);
}
function deferred() { let resolve,reject; const promise=new Promise((a,b)=>{resolve=a;reject=b}); return {promise,resolve,reject}; }
function node(tab) {
  const classes=new Set(),attrs=new Map();
  return {dataset:{accountTab:tab},innerHTML:'',classList:{add:k=>classes.add(k),remove:k=>classes.delete(k),contains:k=>classes.has(k),toggle:(k,on)=>on?classes.add(k):classes.delete(k)},
    setAttribute:(k,v)=>attrs.set(k,v),removeAttribute:k=>attrs.delete(k),getAttribute:k=>attrs.get(k),querySelector:()=>({focus(){}})};
}
function setup(profiles=[deferred()]) {
  const tabs=['dashboard','profile','offers','brokerage','seller','relationships','partners','ai','admin'];
  const buttons=tabs.map(node), panels=new Map(tabs.map(t=>['accountPanel'+t[0].toUpperCase()+t.slice(1),node()]));
  const modal=node(), calls=[];
  const context=vm.createContext({
    hofAuth:{client:{},session:{user:{id:'qa-owner'}},role:'agent'},state:{data:{userType:'agent'}},
    window:{__hofAccountProfileEpoch:0,setHofModalIsolation(){},setTimeout(){}},
    document:{getElementById:id=>id==='accountModal'?modal:panels.get(id),querySelectorAll:s=>s==='[data-account-tab]'?buttons:[...panels.values()]},
    setTimeout(){}, sessionStorage:{getItem:()=>null,removeItem(){}},console:{error(){}},
    initSupabaseAuth:async()=>{},openAuthModal:()=>calls.push('auth'),
    loadAccountProfile:()=>{calls.push('profile-load');return profiles.shift().promise},
    loadOrCreateSubscription:async()=>calls.push('subscription'),loadCurrentUsage:async()=>calls.push('usage'),loadMyOffers:async()=>calls.push('offers-load'),
    renderAccountDashboard:()=>calls.push('render-dashboard'),renderAccountProfileForm:()=>calls.push('render-profile'),
    renderBrokerageFoundationPanel(){},renderSellerFoundationPanel(){},renderRelationshipDraftsPanel(){},renderPartnerFoundationPanel(){},renderAiFoundationPanel(){},loadAdminDashboard(){},
    setAccountStatus(){},renderSubscriptionCheckoutRecovery(){}
  });
  const globals=html.match(/  let accountTabSelectionRevision = 0;\n  let accountWorkspaceOpenRevision = 0;\n/)?.[0]||'';
  vm.runInContext(globals+section('  function showAccountTab(', '  function renderRelationshipDraftsPanel(')
    +section('  async function openAccountDashboard(', '  function getBillingMonth('),context);
  return {context,modal,panels,calls,active:()=>buttons.find(b=>b.classList.contains('active'))?.dataset.accountTab};
}

for(const tab of ['profile','offers','brokerage','relationships','admin']) {
  test(`loading completion retains a user's ${tab} selection`,async()=>{
    const profile=deferred(),x=setup([profile]);
    const opening=x.context.openAccountDashboard();
    assert.ok(x.modal.classList.contains('active'));
    assert.equal(x.active(),'dashboard');
    x.context.showAccountTab(tab);
    profile.resolve();await opening;
    assert.equal(x.active(),tab);
    assert.equal(x.panels.get('accountPanelDashboard').getAttribute('aria-busy'),'false');
  });
}
test('explicit shortcuts are honored when no later tab choice occurs',async()=>{
  const p=deferred(),x=setup([p]);const opening=x.context.openAccountDashboard({tab:'ai'});
  p.resolve();await opening;assert.equal(x.active(),'ai');
});
test('even a deliberate Dashboard click overrides an earlier shortcut',async()=>{
  const p=deferred(),x=setup([p]);const opening=x.context.openAccountDashboard({tab:'ai'});
  x.context.showAccountTab('dashboard');p.resolve();await opening;assert.equal(x.active(),'dashboard');
});
test('a failure retains navigation and shows the existing recovery card',async()=>{
  const p=deferred(),x=setup([p]);const opening=x.context.openAccountDashboard();
  x.context.showAccountTab('profile');p.reject(new Error('offline'));await opening;
  assert.equal(x.active(),'profile');assert.match(x.panels.get('accountPanelDashboard').innerHTML,/Workspace needs a refresh/);
});
test('an older startup cannot render or clear a newer startup loading state',async()=>{
  const a=deferred(),b=deferred(),x=setup([a,b]);
  const first=x.context.openAccountDashboard({tab:'ai'}),second=x.context.openAccountDashboard({tab:'offers'});
  a.resolve();await first;
  assert.equal(x.calls.filter(c=>c==='render-dashboard').length,0);
  assert.equal(x.panels.get('accountPanelDashboard').getAttribute('aria-busy'),'true');
  b.resolve();await second;assert.equal(x.active(),'offers');
  assert.equal(x.calls.filter(c=>c==='render-dashboard').length,1);
});
test('closing during startup does not revive or render the closed workspace',async()=>{
  const p=deferred(),x=setup([p]);const opening=x.context.openAccountDashboard({tab:'ai'});
  x.context.closeAccountDashboard();p.resolve();await opening;
  assert.equal(x.modal.classList.contains('active'),false);
  assert.equal(x.calls.includes('render-dashboard'),false);
  assert.equal(x.calls.includes('subscription'),false);
});
test('changing accounts during startup cannot select or render the stale workspace',async()=>{
  const p=deferred(),x=setup([p]);const opening=x.context.openAccountDashboard({tab:'ai'});
  x.context.hofAuth.session={user:{id:'different-qa-owner'}};x.context.window.__hofAccountProfileEpoch++;
  p.resolve();await opening;
  assert.equal(x.calls.includes('render-dashboard'),false);assert.equal(x.calls.includes('subscription'),false);
});
