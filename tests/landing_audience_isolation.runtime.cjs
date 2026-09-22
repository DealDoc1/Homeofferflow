const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const { test } = require('node:test');
const rootDir = path.resolve(__dirname, '..');
const html = process.env.HOF_TEST_SOURCE_REF
  ? execFileSync('git', ['show', `${process.env.HOF_TEST_SOURCE_REF}:index.html`], { cwd: rootDir, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 })
  : fs.readFileSync(path.join(rootDir, 'index.html'), 'utf8');
function source(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert.ok(a >= 0 && b > a, `source bounds: ${start}`);
  return html.slice(a, b);
}
const roles = ['homebuyer', 'agent', 'investor', 'fsbo'];
function setup({ active = false, draft = null, search = '' } = {}) {
  const nodes = new Map(), calls = [], pills = [];
  function node(id) {
    if (!nodes.has(id)) {
      const attrs = {}, classes = new Set();
      nodes.set(id, { dataset: {}, style: {}, value: 'untouched offer input', textContent: '', innerHTML: '',
        getAttribute: key => attrs[key], setAttribute: (key, value) => { attrs[key] = value; },
        classList: { contains: key => classes.has(key), add: key => classes.add(key), remove: key => classes.delete(key), toggle: (key, on) => on ? classes.add(key) : classes.delete(key) },
        focus: () => calls.push(['focus', id]),
      });
    }
    return nodes.get(id);
  }
  const c = { URLSearchParams, state: { data: { userType: 'agent', seenProperty: 'yes', buyerName: 'Saved buyer', _hofOfferId: 'saved-id' }, step: 5 },
    hofAuth: { role: 'agent', session: { user: { id: 'owner' } } },
    location: { search, assign: url => calls.push(['route', url]) },
    saveDraft: () => calls.push(['save']), showStep: step => calls.push(['step', step]),
    trackEvent: (...args) => calls.push(['event', ...args]),
    syncOnDemandHeroTrialCta: role => calls.push(['trial', role]),
    syncLandingPathContext: role => calls.push(['context', role]),
    syncLandingPathTrust: role => calls.push(['trust', role]),
    addLandingPathStrip: () => calls.push(['strip']),
    closeFsboSellerModal: options => calls.push(['closeSeller', options.restoreFocus]),
    openFsboSellerModal: () => calls.push(['seller']),
    resumableLocalOfferDraft: () => draft,
    resumeLocalOfferDraft: surface => calls.push(['resume', surface]),
    rememberHomebuyerCheckoutChannel: () => {}, startHomebuyerOffer: () => calls.push(['startBuyer']),
    document: { getElementById: node,
      querySelectorAll: selector => selector.startsWith('.pill') ? pills : [],
      querySelector: selector => selector.startsWith('.pill') ? pills.find(p => p.getAttribute('aria-checked') === 'true') : null },
  };
  c.window = c; c.root = c;
  vm.createContext(c);
  for (const role of roles) {
    const p = node(role);
    p.dataset.audience = role;
    p.setAttribute('aria-checked', role === 'homebuyer' ? 'true' : 'false');
    const tag = html.match(new RegExp(`<button[^>]+data-audience="${role}"[^>]*>`))[0];
    const handler = tag.match(/onclick="([^"]*)"/)[1];
    p.click = () => vm.runInContext(handler, c);
    pills.push(p);
  }
  node('wizardOverlay').classList.toggle('active', active);
  node('fsboSellerModal').setAttribute('aria-hidden', 'true');
  vm.runInContext(source('  function setAudience(', '  window.handleAudiencePickerKey'), c);
  c.oldSetAudience = c.setAudience;
  vm.runInContext(source('  root.setAudience = function setAudience(', '  const oldRenderDashboard'), c);
  vm.runInContext(source('  function selectedLandingAudience()', '  function startPrimaryOffer()'), c);
  vm.runInContext(source('  function refreshResumeOfferCtas()', '  function resumeLocalOfferDraft('), c);
  vm.runInContext(source('  window.handleAudiencePickerKey', "  document.addEventListener('click', function(e) {"), c);
  return { c, node, pills, calls };
}
function untouched(x, before, original) {
  assert.equal(JSON.stringify(x.c.state), before);
  assert.equal(x.c.state.data, original);
  assert.equal(x.node('buyerName').value, 'untouched offer input');
  assert.equal(x.node('showingHelper').style.display, undefined);
  assert.equal(x.calls.filter(row => row[0] === 'save' || row[0] === 'step').length, 0);
}
const labels = { homebuyer: 'Build Your Offer — No Payment to Start', agent: 'Start a Transaction', investor: 'Open Investor Workspace', fsbo: 'Start Your Free Plan' };
for (const role of roles) {
  for (const active of [false, true]) test(`${role} pill preserves ${active ? 'open' : 'closed'} offer and routes correctly`, () => {
    const x = setup({ active }), before = JSON.stringify(x.c.state), original = x.c.state.data;
    x.pills[roles.indexOf(role)].click();
    untouched(x, before, original);
    assert.equal(x.c.selectedLandingAudience(), role);
    assert.equal(x.node('heroCta').textContent, labels[role]);
    assert.equal(x.pills.filter(p => p.tabIndex === 0).length, 1);
    for (const hook of ['trial', 'context', 'trust']) assert.ok(x.calls.some(row => row[0] === hook && row[1] === role));
    x.c.beginOfferFrom('landing_hero_cta');
    const expected = role === 'homebuyer' ? 'startBuyer' : role === 'fsbo' ? 'seller' : 'route';
    assert.ok(x.calls.some(row => row[0] === expected));
    if (role === 'agent') assert.match(x.calls.find(row => row[0] === 'route')[1], /^\/agents\?/);
    if (role === 'investor') assert.match(x.calls.find(row => row[0] === 'route')[1], /^\/\?investor=1/);
  });
  test(`${role} explicit transaction selection still changes role and saves`, () => {
    const x = setup({ active: true });
    x.c.setAudience(role);
    assert.equal(x.c.state.data.userType, role);
    assert.equal(x.c.state.step, 0);
    assert.equal(x.c.state.data.seenProperty, role === 'homebuyer' ? 'yes' : '');
    assert.equal(x.calls.filter(row => row[0] === 'save').length, 1);
    assert.equal(x.calls.filter(row => row[0] === 'step').length, 1);
  });
  for (const parameter of ['audience', 'utm_content']) test(`${parameter}=${role} campaign changes presentation only`, () => {
    const x = setup({ search: `?${parameter}=${role}` }), before = JSON.stringify(x.c.state), original = x.c.state.data;
    vm.runInContext(source('    try {\n      // Campaign links', '    try { root.updateAuthUI'), x.c);
    untouched(x, before, original);
    assert.equal(x.c.selectedLandingAudience(), role);
    assert.equal(x.node('heroCta').textContent, labels[role]);
  });
}
for (const key of ['ArrowLeft', 'ArrowUp', 'ArrowRight', 'ArrowDown', 'Home', 'End']) test(`keyboard ${key} preserves offer`, () => {
  const x = setup({ active: true }), before = JSON.stringify(x.c.state), original = x.c.state.data;
  x.c.handleAudiencePickerKey({ key, currentTarget: x.pills[0], preventDefault() {} });
  untouched(x, before, original);
  assert.ok(x.calls.some(row => row[0] === 'focus'));
  const expected = ['ArrowLeft', 'ArrowUp', 'End'].includes(key) ? 'fsbo' : key === 'Home' ? 'homebuyer' : 'agent';
  assert.equal(x.c.selectedLandingAudience(), expected);
});
test('resume labels follow visible audience without mutating unrelated active role', () => {
  const x = setup({ draft: { userType: 'homebuyer', step: 4 } });
  x.node('homebuyer').click();
  assert.equal(x.c.state.data.userType, 'agent');
  assert.equal(x.node('heroCta').textContent, 'Resume Your Saved Offer →');
  x.c.beginOfferFrom('landing_hero_cta');
  assert.ok(x.calls.some(row => row[0] === 'resume'));
  x.node('investor').click();
  assert.equal(x.node('heroCta').textContent, labels.investor);
  assert.equal(x.node('heroCta').dataset.hofResumeLabel, undefined);
  x.node('homebuyer').click();
  assert.equal(x.node('heroCta').textContent, 'Resume Your Saved Offer →');
});
test('agent draft is not advertised as a homebuyer resume', () => {
  const x = setup({ draft: { userType: 'agent', step: 4 } });
  x.node('homebuyer').click();
  assert.equal(x.node('heroCta').textContent, labels.homebuyer);
});
test('changing audience still closes an unrelated seller modal', () => {
  const x = setup();
  x.node('fsboSellerModal').setAttribute('aria-hidden', 'false');
  x.node('agent').click();
  assert.deepEqual(x.calls.find(row => row[0] === 'closeSeller'), ['closeSeller', false]);
});
test('shared seller URL opens seller intake without modifying an offer', () => {
  const x = setup(), before = JSON.stringify(x.c.state), original = x.c.state.data;
  x.c.params = () => new URLSearchParams('?seller=1');
  x.c.setTimeout = callback => callback();
  vm.runInContext(source("    if (params().get('seller') === '1')", '    // The public homebuyer landing page'), x.c);
  untouched(x, before, original);
  assert.equal(x.c.selectedLandingAudience(), 'fsbo');
  assert.ok(x.calls.some(row => row[0] === 'seller'));
});
test('installed-app seller shortcut opens intake without modifying an offer', async () => {
  const x = setup({ active: true }), before = JSON.stringify(x.c.state), original = x.c.state.data;
  x.c.validActions = new Set(['seller_plan']);
  x.c.trackShortcut = (...args) => x.calls.push(['shortcut', ...args]);
  vm.runInContext(source('  async function runAction(action,', "    if (action === 'investor_workspace')") + '\n}', x.c);
  await x.c.runAction('seller_plan');
  untouched(x, before, original);
  assert.equal(x.c.selectedLandingAudience(), 'fsbo');
  assert.ok(x.calls.some(row => row[0] === 'seller'));
});
for (const [label, expected] of [['Build a HomeOfferFlow homebuyer offer with no payment to start', 'startBuyer'], ['Open the HomeOfferFlow investor workspace', 'route'], ['Start a HomeOfferFlow FSBO seller package request', 'seller']]) test(`${label} card preserves draft until explicit handoff`, () => {
  const x = setup(), before = JSON.stringify(x.c.state), original = x.c.state.data;
  const tag = html.match(new RegExp(`<(?:button|a)[^>]+aria-label="${label}"[^>]*>`))[0];
  x.c.event = { preventDefault() {} };
  vm.runInContext(tag.match(/onclick="([^"]*)"/)[1], x.c);
  untouched(x, before, original);
  assert.ok(x.calls.some(row => row[0] === expected));
});

function enableAuth(x, { enhanced = true } = {}) {
  const storage = new Map(), c = x.c;
  c.localStorage = c.sessionStorage = { getItem: key => storage.get(key) || null,
    setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key) };
  c.setTimeout = callback => callback();
  c.clearAuthStatus = () => {};
  c.updateAuthUI = () => x.calls.push(['authUI']);
  c.ROLE_LABELS = { agent: 'Agent', broker: 'Broker / Team Lead', investor: 'Investor' };
  vm.runInContext(source('  function setAuthRole(role)', '  function closeAuthModal()'), c);
  if (enhanced) {
    vm.runInContext(source('  function normalizeAccountRole(role)', '  function safeEscape('), c);
    vm.runInContext(source('  root.setAuthRole = function', '  root.updateAuthUI = function updateAuthUI(){'), c);
  }
  return storage;
}
for (const enhanced of [false, true]) for (const role of ['agent', 'broker', 'investor']) {
  test(`${enhanced ? 'enhanced' : 'base'} ${role} sign-in preserves homebuyer offer`, () => {
    const x = setup({ active: true });
    x.c.state.data.userType = 'homebuyer';
    const before = JSON.stringify(x.c.state), original = x.c.state.data;
    const store = enableAuth(x, { enhanced });
    x.c.openAuthModal(role);
    untouched(x, before, original);
    assert.equal(x.node('authModal').getAttribute('aria-hidden'), 'false');
    assert.equal(x.c.hofAuth.role, role === 'broker' && !enhanced ? 'agent' : role);
    assert.equal(store.get('hof_auth_role'), x.c.hofAuth.role);
    assert.ok(x.calls.some(row => row[0] === 'focus' && row[1] === 'authEmail'));
  });
}
for (const role of ['agent', 'broker', 'investor']) test(`${role} sign-in tab does not rewrite an offer`, () => {
  const x = setup();
  x.c.state.data.userType = 'homebuyer';
  const before = JSON.stringify(x.c.state), original = x.c.state.data;
  enableAuth(x);
  const tag = html.match(new RegExp(`<button[^>]+data-auth-role="${role}"[^>]*>`))[0];
  vm.runInContext(tag.match(/onclick="([^"]*)"/)[1], x.c);
  untouched(x, before, original);
  assert.equal(x.c.hofAuth.role, role);
});

function routeSetup(search, session = true, role = 'agent') {
  const x = setup({ active: true, search }), c = x.c, timers = [], readiness = [];
  enableAuth(x);
  c.state.data.userType = 'homebuyer';
  c.hofAuth.role = role;
  if (!session) c.hofAuth.session = null;
  c.URL = URL;
  c.location.href = 'https://www.homeofferflow.com/' + search;
  c.history = { replaceState: (_state, _title, url) => {
    c.location.href = new URL(url, c.location.href).href;
    c.location.search = new URL(c.location.href).search;
  } };
  c.params = () => new URLSearchParams(c.location.search);
  c.__hofDraftRestoreAuthReady = true;
  c.document.readyState = 'complete';
  c.document.title = 'HomeOfferFlow';
  c.setTimeout = callback => { timers.push(callback); };
  c.continueAfterAuthResolution = callback => { readiness.push(callback); };
  c.openAccountDashboard = opts => x.calls.push(['dashboard', opts.tab]);
  c.startAgentWorkflow = kind => x.calls.push(['workflow', kind]);
  c.openAgentTransactionPicker = () => x.calls.push(['picker']);
  c.logOfferEvent = () => {};
  c.showInvestorAccountRouteNotice = () => x.calls.push(['wrongAccount']);
  x.flush = () => {
    let loops = 0;
    while (timers.length) { assert.ok(++loops < 25, 'bounded timers'); timers.shift()(); }
  };
  x.ready = () => { while (readiness.length) readiness.shift()(); x.flush(); };
  return x;
}
function runAgentRoute(x, recovery = false) {
  if (!recovery) vm.runInContext(source("    if (params().get('agent') === '1')", '    // Investor acquisition'), x.c);
  else {
    const tag = '<script id="hof-agent-landing-route-recovery-v1">';
    vm.runInContext(source(tag, '</script>').slice(tag.length), x.c);
  }
}
for (const recovery of [false, true]) for (const session of [false, true]) {
  for (const workflow of ['purchase', 'sale_listing', 'lease_listing', 'lease_representation']) {
    test(`${recovery ? 'recovery' : 'normal'} ${session ? 'signed-in' : 'signed-out'} ${workflow} link preserves prior offer`, () => {
      const x = routeSetup(`?agent=1&workflow=${workflow}`, session), before = JSON.stringify(x.c.state), original = x.c.state.data;
      runAgentRoute(x, recovery);
      x.flush();
      untouched(x, before, original);
      x.ready();
      untouched(x, before, original);
      assert.equal(x.c.selectedLandingAudience(), 'agent');
      if (session) assert.deepEqual(x.calls.filter(row => row[0] === 'workflow'), [['workflow', workflow]]);
      else {
        assert.equal(x.node('authModal').getAttribute('aria-hidden'), 'false');
        assert.equal(x.c.localStorage.getItem('hof_agent_landing_package_workflow'), workflow);
        assert.equal(x.calls.some(row => row[0] === 'workflow'), false);
      }
    });
  }
  for (const workspace of ['', 'seller', 'relationship']) test(`${recovery ? 'recovery' : 'normal'} ${session ? 'signed-in' : 'signed-out'} workspace ${workspace || 'chooser'} link preserves offer`, () => {
    const x = routeSetup(`?agent=1&workspace=${workspace}`, session), before = JSON.stringify(x.c.state), original = x.c.state.data;
    runAgentRoute(x, recovery); x.flush(); x.ready();
    untouched(x, before, original);
    if (session) {
      assert.deepEqual(x.calls.filter(row => row[0] === 'dashboard'), [['dashboard', workspace === 'relationship' ? 'relationships' : workspace || 'dashboard']]);
      assert.equal(x.calls.some(row => row[0] === 'picker'), !workspace);
    } else assert.equal(x.node('authModal').getAttribute('aria-hidden'), 'false');
  });
}
for (const session of [false, true]) for (const accountRole of ['agent', 'investor']) test(`investor link with ${session ? 'signed-in' : 'signed-out'} ${accountRole} preserves offer`, () => {
  const x = routeSetup('?investor=1', session, accountRole), before = JSON.stringify(x.c.state), original = x.c.state.data;
  vm.runInContext(source("    if (params().get('investor') === '1')", "    if (params().get('partner_onboarding'))"), x.c);
  x.flush(); x.ready(); untouched(x, before, original);
  assert.equal(x.c.selectedLandingAudience(), 'investor');
  if (!session) {
    assert.equal(x.node('authModal').getAttribute('aria-hidden'), 'false');
    assert.equal(x.c.localStorage.getItem('hof_investor_landing_workspace'), '1');
  } else if (accountRole === 'investor') assert.ok(x.calls.some(row => row[0] === 'dashboard'));
  else assert.ok(x.calls.some(row => row[0] === 'wrongAccount'));
});
test('agent shared-context action preserves the offer before chooser handoff', () => {
  const x = setup({ active: true }), before = JSON.stringify(x.c.state), original = x.c.state.data;
  enableAuth(x);
  x.c.logOfferEvent = () => {};
  x.c.startAccountTransaction = () => x.calls.push(['chooser']);
  const share = process.env.HOF_TEST_SOURCE_REF
    ? execFileSync('git', ['show', `${process.env.HOF_TEST_SOURCE_REF}:assets/pwa-share-target.js`], { cwd: rootDir, encoding: 'utf8' })
    : fs.readFileSync(path.join(rootDir, 'assets/pwa-share-target.js'), 'utf8');
  const start = share.indexOf("    agentAction.addEventListener('click', () => {");
  const end = share.indexOf('    card.appendChild(agentAction);', start);
  x.c.agentAction = { addEventListener: (_name, callback) => callback() };
  vm.runInContext(share.slice(start, end), x.c);
  untouched(x, before, original);
  assert.ok(x.calls.some(row => row[0] === 'chooser'));
});

function assertBuyerHandoff(x, before, original) {
  // The fresh-offer implementation has its own reset tests. Here the handoff
  // is observed without letting a mocked destination conceal an early save.
  untouched(x, before, original);
  assert.equal(x.c.selectedLandingAudience(), 'homebuyer');
  assert.equal(x.c.__hofLandingAudienceUserSelected, true);
  assert.equal(x.calls.filter(row => row[0] === 'startBuyer').length, 1);
  assert.equal(x.calls.filter(row => row[0] === 'route').length, 0);
  assert.equal(x.node('authModal').getAttribute('aria-hidden'), undefined);
}
for (const accountRole of ['signed-out', 'agent', 'broker', 'investor']) {
  for (const entry of ['buyer_link', 'guide_link', 'app_shortcut', 'shared_context']) {
    test(`${entry} honors explicit buyer choice for ${accountRole}`, async () => {
      const search = entry === 'guide_link' ? '?buyer=1&utm_source=texas_homebuyer_offer_guide' : '?buyer=1';
      const x = routeSetup(search, accountRole !== 'signed-out', accountRole === 'signed-out' ? 'agent' : accountRole);
      const before = JSON.stringify(x.c.state), original = x.c.state.data;
      if (entry === 'buyer_link' || entry === 'guide_link') {
        x.c.fetch = () => Promise.resolve({ ok: true });
        vm.runInContext(source("    if (params().get('buyer') === '1')", '    // A direct workspace link'), x.c);
        x.flush();
        assert.equal(x.c.params().get('buyer'), null);
        assert.equal(x.c.__hofOfferEntrySurface, entry === 'guide_link' ? 'texas_homebuyer_offer_guide' : 'buyer_landing');
      } else if (entry === 'app_shortcut') {
        x.c.validActions = new Set(['buyer_offer']);
        x.c.recordBuyerOfferShortcut = () => x.calls.push(['buyerShortcut']);
        x.c.trackShortcut = () => {};
        vm.runInContext(source('  async function runAction(action,', "    const role = window.hofAuth?.role === 'investor' ? 'investor' : 'agent';") + '\n}', x.c);
        await x.c.runAction('buyer_offer');
        assert.equal(x.c.__hofOfferEntrySurface, 'pwa_buyer_offer');
        assert.equal(x.calls.filter(row => row[0] === 'buyerShortcut').length, 1);
      } else {
        const share = process.env.HOF_TEST_SOURCE_REF
          ? execFileSync('git', ['show', `${process.env.HOF_TEST_SOURCE_REF}:assets/pwa-share-target.js`], { cwd: rootDir, encoding: 'utf8' })
          : fs.readFileSync(path.join(rootDir, 'assets/pwa-share-target.js'), 'utf8');
        const start = share.indexOf("    action.addEventListener('click', () => {");
        const end = share.indexOf('    card.appendChild(action);', start);
        x.c.action = { addEventListener: (_event, callback) => callback() };
        vm.runInContext(share.slice(start, end), x.c);
        assert.equal(x.c.__hofOfferEntrySurface, 'pwa_share_target');
      }
      assertBuyerHandoff(x, before, original);
    });
  }
  for (const parameter of ['audience', 'utm_content']) test(`${parameter}=homebuyer campaign honors buyer path for ${accountRole}`, () => {
    const x = routeSetup(`?${parameter}=homebuyer`, accountRole !== 'signed-out', accountRole === 'signed-out' ? 'agent' : accountRole);
    const before = JSON.stringify(x.c.state), original = x.c.state.data;
    vm.runInContext(source('    try {\n      // Campaign links', '    try { root.updateAuthUI'), x.c);
    x.c.beginOfferFrom('landing_hero_cta');
    assertBuyerHandoff(x, before, original);
  });
}
for (const accountRole of ['agent', 'broker']) for (const search of ['', '?audience=invalid', '?utm_content=unknown']) {
  test(`ordinary homepage ${search || '(no campaign)'} still respects ${accountRole} account`, () => {
    const x = routeSetup(search, true, accountRole);
    vm.runInContext(source('    try {\n      // Campaign links', '    try { root.updateAuthUI'), x.c);
    x.c.beginOfferFrom('landing_hero_cta');
    assert.equal(x.calls.some(row => row[0] === 'startBuyer'), false);
    assert.match(x.calls.find(row => row[0] === 'route')[1], /^\/agents\?/);
    assert.notEqual(x.c.__hofLandingAudienceUserSelected, true);
  });
}
