const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const between = (start, end, source = html) => {
  const from = source.indexOf(start);
  const to = source.indexOf(end, from);
  assert.ok(from >= 0 && to > from, `Missing source boundary: ${start}`);
  return source.slice(from, to);
};
const roleScript = between('<script id="hof-broker-role-v14-js">', '</script>');
const roleHelpers = between('  function normalizeAccountRole(', '  function safeEscape(', roleScript);
const updateAuthUI = between('  root.updateAuthUI = function updateAuthUI(){', '  root.ensureProfileShell', roleScript);
const roleInit = between('  // Refresh UI once this enhancement loads.', '})();', roleScript);
const defaults = between('  function applyProfileDefaultsToWizard(', '  function resetWizardForFreshOffer(');
const authorityScript = between('<script id="hof-ondemand-brokerage-launch-v1">', '</script>');
const authoritativeProfile = between('  root.ensureProfileShell = async function', '  root.loadOrCreateSubscription', authorityScript);
const explicitRole = between('  root.setAuthRole = function', '  const oldOpenAuthModal', roleScript);
const accountOffer = between('  function startAccountOffer() {', '  // Keep the first dashboard action');
const accountOfferWrapper = between('  const oldStartAccountOffer = root.startAccountOffer;', '  // Refresh UI once', roleScript);
const investorRoute = between(
  '    // Investor and agent workspaces keep different saved defaults.',
  "    if (params().get('partner_onboarding'))"
);

function setup(audience, accountRole = 'agent') {
  const writes = [];
  const user = {id:'test-user', email:'test@example.com', user_metadata:{role:accountRole}};
  const state = {data:audience ? {userType:audience, offerPrice:'350000'} : {}};
  const hofAuth = {role:accountRole, session:{user}, accountProfile:{agent_name:'Saved Agent', investor_entity_name:'Saved LLC', default_title_payer:'seller'}};
  const root = {state, hofAuth};
  const context = vm.createContext({
    root, state, hofAuth, window:{innerWidth:1280}, console,
    ROLE_LABELS:{agent:'Agent', broker:'Broker / Team Lead', investor:'Investor'},
    localStorage:{getItem:()=>accountRole, setItem:()=>{}},
    document:{getElementById:()=>null, querySelector:()=>null, querySelectorAll:()=>[]},
    normalizedRole:value=>value==='investor'?'investor':value==='brokerage_admin'?'broker':'agent',
    nowIso:()=> '2026-09-10T00:00:00Z',
    setInputIfEmpty:(...args)=>writes.push(args),
    setRadioValue:(...args)=>writes.push(args),
    syncAgentQuickFields:()=>writes.push(['syncAgent']),
  });
  vm.runInContext(roleHelpers + updateAuthUI + defaults + authoritativeProfile, context);
  root.loadAccountProfile = async () => {
    root.updateAuthUI();
    vm.runInContext('applyProfileDefaultsToWizard()', context);
  };
  const loads = [];
  for (const name of ['loadOrCreateSubscription', 'loadCurrentUsage', 'loadBrokerageFoundation']) {
    root[name] = async () => loads.push(name);
  }
  const query = {select:()=>query, eq:()=>query, maybeSingle:async()=>({data:{id:user.id,email:user.email,role:accountRole},error:null})};
  root.getSupabaseClient = () => ({from:name=>{assert.equal(name,'hof_profiles');return query;}});
  return {context, root, writes, loads, query};
}

for (const audience of ['homebuyer','agent','investor','fsbo']) {
  for (const accountRole of ['agent','investor','broker']) {
    test(`${audience} stays selected when ${accountRole} account controls refresh`, () => {
      const {root} = setup(audience, accountRole);
      root.updateAuthUI();
      root.updateAuthUI(); // Refocus/token refresh must be just as safe.
      assert.equal(root.state.data.userType, audience);
      assert.equal(root.state.data.offerPrice, '350000');
      assert.equal(root.hofAuth.role, accountRole);
    });
  }
  test(`${audience} survives authoritative agent profile restoration`, async () => {
    const {root, writes, loads} = setup(audience);
    await root.ensureProfileShell();
    assert.equal(root.state.data.userType, audience);
    assert.equal(root.hofAuth.authoritativeRole, 'agent');
    assert.equal(root.hofAuth.profileReady, true);
    assert.equal(loads.length, 3);
    assert.equal(writes.length > 0, audience === 'agent');
  });
  test(`${audience} stays selected without an authenticated session`, () => {
    const {root} = setup(audience);
    root.hofAuth.session = null;
    root.updateAuthUI();
    assert.equal(root.state.data.userType, audience);
  });
}

test('a customer choice made while the profile loads wins over the account default', async () => {
  const {root, query, writes} = setup('agent');
  let resolve;
  query.maybeSingle = () => new Promise(done=>{resolve=done;});
  const pending = root.ensureProfileShell();
  root.state.data.userType = 'homebuyer';
  resolve({data:{id:'test-user',email:'test@example.com',role:'agent'},error:null});
  await pending;
  assert.equal(root.state.data.userType,'homebuyer');
  assert.equal(root.hofAuth.role,'agent');
  assert.deepEqual(writes,[]);
});

test('saved role initialization only supplies an absent public path', () => {
  for (const audience of ['', 'homebuyer','agent','investor','fsbo']) {
    const {root, context} = setup(audience);
    vm.runInContext(roleInit, context);
    assert.equal(root.state.data.userType,audience || 'homebuyer');
  }
});

test('investor defaults are applied only to an investor interview', () => {
  for (const audience of ['homebuyer','agent','investor','fsbo']) {
    const {writes,context} = setup(audience,'investor');
    vm.runInContext('applyProfileDefaultsToWizard(true)',context);
    assert.equal(writes.length>0,audience==='investor');
  }
});

for (const role of ['agent', 'broker', 'investor']) {
  const expectedAudience = role === 'investor' ? 'investor' : 'agent';
  test(`explicitly choosing the ${role} account path still selects its interview`, () => {
    const {root, context} = setup('homebuyer');
    vm.runInContext(explicitRole, context);
    root.setAuthRole(role);
    assert.equal(root.hofAuth.role, role);
    assert.equal(root.state.data.userType, expectedAudience);
  });

  test(`starting a new offer from the ${role} account opens the intended interview`, () => {
    const {root, context} = setup('homebuyer', role);
    const actions = [];
    Object.assign(context, {
      resumeLocalAccountOfferDraft: selected => { actions.push(['resume', selected]); return false; },
      resetWizardForFreshOffer: selected => { root.state.data = {userType:selected}; actions.push(['reset', selected]); },
      setAudience: selected => { root.state.data.userType = selected; },
      closeAccountDashboard: () => actions.push(['close account']),
      closeAuthModal: () => actions.push(['close auth']),
      openWizard: fresh => actions.push(['open', fresh]),
      setTimeout: callback => callback(),
      applySmartDefaults: () => {},
      restoreConditionalSections: () => {},
    });
    vm.runInContext(accountOffer + '\nroot.startAccountOffer = startAccountOffer;\n' + accountOfferWrapper, context);
    root.startAccountOffer();
    assert.equal(root.state.data.userType, expectedAudience);
    assert.equal(root.hofAuth.role, role);
    assert.deepEqual(actions, [
      ['resume', expectedAudience], ['reset', expectedAudience],
      ['close account'], ['close auth'], ['open', true],
    ]);
  });
}

function runInvestorRouteFor(role) {
  const actions = [];
  const inserted = [];
  const heroPriceNote = {insertAdjacentElement: (position, element) => inserted.push([position, element])};
  const document = {
    title: 'HomeOfferFlow',
    getElementById: id => id === 'heroPriceNote' ? heroPriceNote : null,
    createElement: () => ({setAttribute: () => {}}),
  };
  const window = {
    hofAuth: {session: {user: {id: 'test-user'}}, role},
    location: {href: 'https://www.homeofferflow.com/?investor=1'},
    setAudience: audience => actions.push(['audience', audience]),
    openAccountDashboard: options => actions.push(['dashboard', options]),
    logOfferEvent: (...args) => actions.push(['event', args]),
  };
  const context = vm.createContext({
    window, document, console, URL,
    history: {replaceState: () => actions.push(['clean-url'])},
    params: () => ({get: key => key === 'investor' ? '1' : ''}),
    continueAfterAuthResolution: callback => callback(),
    setTimeout: callback => callback(),
  });
  vm.runInContext(investorRoute, context);
  return {actions, inserted};
}

test('an agent session preserves the investor page instead of opening an agent dashboard', () => {
  const {actions, inserted} = runInvestorRouteFor('agent');
  assert.equal(actions.some(([kind]) => kind === 'dashboard'), false);
  assert.equal(actions.some(([kind, audience]) => kind === 'audience' && audience === 'investor'), true);
  assert.equal(inserted.length, 1);
  assert.match(inserted[0][1].innerHTML, /Investor workspaces keep saved deal details separate/);
});

test('an investor session still opens the investor workspace directly', () => {
  const {actions, inserted} = runInvestorRouteFor('investor');
  const dashboards = actions.filter(([kind]) => kind === 'dashboard');
  assert.equal(dashboards.length, 1);
  assert.equal(dashboards[0][1].tab, 'dashboard');
  assert.equal(inserted.length, 0);
});
