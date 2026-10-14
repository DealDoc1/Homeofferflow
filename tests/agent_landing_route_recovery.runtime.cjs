const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('<script id="hof-agent-landing-route-recovery-v1">');
const end = html.indexOf('</script>', start);
assert.ok(start >= 0 && end > start, 'Agent landing route recovery must be present');
const source = html.slice(html.indexOf('\n', start) + 1, end);
const directStart = html.indexOf("    if (params().get('agent') === '1')");
const directEnd = html.indexOf("    if (params().get('investor') === '1')", directStart);
assert.ok(directStart >= 0 && directEnd > directStart);
const directSource = html.slice(directStart, directEnd);

function setup({session, workflow = 'purchase', ready = true, openDashboard, workspaceOpen = false, direct = false} = {}) {
  const calls = [];
  const storage = new Map([['hof_agent_route_pending_v1', JSON.stringify({workflow, workspace:''})]]);
  const location = {
    search: `?agent=1&workflow=${workflow}&utm_source=agent_workspace`,
    href: `https://www.homeofferflow.com/?agent=1&workflow=${workflow}&utm_source=agent_workspace`,
  };
  const authTitle = {textContent:''};
  const authSubtitle = {textContent:''};
  const authRoleRow = {hidden:false};
  const authNote = {textContent:''};
  const window = {
    __hofDraftRestoreAuthReady: ready,
    __hofAccountRouteAuthPending: true,
    hofAuth: {session: session ? {user:{id:'agent'}} : null},
    location,
    setAudience: role => calls.push(['audience', role]),
    openAccountDashboard: options => {
      calls.push(['dashboard', options.tab]);
      return typeof openDashboard === 'function' ? openDashboard(options) : undefined;
    },
    startAgentWorkflow: choice => calls.push(['transaction', choice]),
    openAgentTransactionPicker: () => calls.push(['picker']),
    openAuthModal: role => calls.push(['auth', role]),
    logOfferEvent: (_id, event, status, _message, data) => calls.push(['event', event, status, data.workflow]),
    setTimeout: callback => callback(),
    addEventListener: () => {},
    history: {replaceState: (_state, _title, next) => { calls.push(['clean', next]); location.search = ''; location.href = `https://www.homeofferflow.com${next}`; }},
  };
  const context = vm.createContext({
    window, URLSearchParams, URL,
    document: {readyState:'complete', title:'HomeOfferFlow', getElementById:id => id === 'accountModal' ? {classList:{contains:()=>workspaceOpen}} : (id === 'authTitle' ? authTitle : (id === 'authSubtitle' ? authSubtitle : (id === 'authRoleRow' ? authRoleRow : (id === 'authNote' ? authNote : null))))},
    params:()=>new URLSearchParams(location.search), setTimeout: callback=>callback(), continueAfterAuthResolution: callback=>callback(),
    sessionStorage: {getItem:key => storage.get(key) || null, setItem:(key, value) => storage.set(key, value), removeItem:key => storage.delete(key)},
    localStorage: {getItem:key => storage.get(key) || null, setItem:(key, value) => storage.set(key, value), removeItem:key => storage.delete(key)},
  });
  vm.runInContext(direct ? directSource : source, context);
  return {calls, storage, window, authTitle, authSubtitle, authRoleRow, authNote};
}

test('a signed-in agent opens the preserved transaction exactly once', () => {
  const page = setup({session:true, workflow:'purchase'});
  assert.deepEqual(page.calls, [
    ['audience', 'agent'], ['clean', '/?utm_source=agent_workspace'],
    ['dashboard', 'dashboard'], ['transaction', 'purchase'],
    ['event', 'agent_landing_package_handoff', 'opened', 'purchase'],
  ]);
  assert.equal(page.window.__hofAgentLandingRouteProcessed, true);
  assert.equal(page.window.__hofAccountRouteAuthPending, false);
  assert.equal(page.storage.has('hof_agent_route_pending_v1'), false);
});

test('a slow authenticated workspace does not open the selected transaction early', async () => {
  let markWorkspaceReady;
  const workspaceReady = new Promise(resolve => { markWorkspaceReady = resolve; });
  const page = setup({session:true, workflow:'lease_listing', openDashboard: () => workspaceReady});

  assert.deepEqual(page.calls, [
    ['audience', 'agent'], ['clean', '/?utm_source=agent_workspace'],
    ['dashboard', 'dashboard'], ['event', 'agent_landing_package_handoff', 'opened', 'lease_listing'],
  ]);

  markWorkspaceReady();
  await workspaceReady;
  await Promise.resolve();
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(JSON.parse(JSON.stringify(page.calls)), [
    ['audience', 'agent'], ['clean', '/?utm_source=agent_workspace'],
    ['dashboard', 'dashboard'], ['event', 'agent_landing_package_handoff', 'opened', 'lease_listing'],
    ['transaction', 'lease_listing'],
  ]);
});

test('a signed-out agent sees the preserved workflow in the secure sign-in handoff', () => {
  const page = setup({session:false, workflow:'lease_representation'});
  assert.deepEqual(page.calls.slice(0, 3), [
    ['audience', 'agent'], ['clean', '/?utm_source=agent_workspace'], ['auth', 'agent'],
  ]);
  assert.equal(page.storage.get('hof_agent_landing_package_workflow'), 'lease_representation');
  assert.equal(page.authTitle.textContent, 'Continue to your tenant representation transaction');
  assert.match(page.authSubtitle.textContent, /open the next questions/i);
  assert.equal(page.authRoleRow.hidden, true);
  assert.match(page.authNote.textContent, /agent or broker profile/i);
  assert.match(page.authNote.textContent, /no password or brokerage seat is required/i);
  assert.equal(page.window.__hofAccountRouteAuthPending, true);
});

test('a route already handled by the DOM-ready path does not open another destination', () => {
  const page = setup({session:true});
  page.calls.length = 0;
  const context = vm.createContext({window:page.window, URLSearchParams, URL, document:{readyState:'complete', title:'HomeOfferFlow', getElementById:()=>null}, sessionStorage:{getItem:()=>null, removeItem:()=>{}}, localStorage:{getItem:()=>null, setItem:()=>{}, removeItem:()=>{}}});
  vm.runInContext(source, context);
  assert.deepEqual(page.calls, []);
});

for (const direct of [false, true]) {
  test(`${direct ? 'direct' : 'recovery'} generic route preserves an already open account selection`, () => {
    const page = setup({session:true, workflow:'', workspaceOpen:true, direct});
    assert.equal(page.calls.some(call=>['dashboard','picker','transaction'].includes(call[0])), false);
    assert.equal(page.calls.some(call=>call[0]==='event'), false);
    assert.equal(page.window.__hofAgentLandingRouteProcessed,true);
    assert.equal(page.window.__hofAccountRouteAuthPending,false);
    assert.equal(page.storage.has('hof_agent_route_pending_v1'),false);
  });
  test(`${direct ? 'direct' : 'recovery'} generic route opens a closed account normally`, () => {
    const page=setup({session:true,workflow:'',workspaceOpen:false,direct});
    assert.equal(page.calls.filter(call=>call[0]==='dashboard').length,1);
    assert.equal(page.calls.filter(call=>call[0]==='picker').length,1);
  });
  test(`${direct ? 'direct' : 'recovery'} explicit transaction still proceeds when an account is open`, () => {
    const page=setup({session:true,workflow:'purchase',workspaceOpen:true,direct});
    assert.equal(page.calls.filter(call=>call[0]==='dashboard').length,1);
    assert.equal(page.calls.filter(call=>call[0]==='transaction').length,1);
  });
}
