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
        classList: { contains: key => classes.has(key), toggle: (key, on) => on ? classes.add(key) : classes.delete(key) },
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
  vm.runInContext(source('  window.handleAudiencePickerKey', "  document.getElementById('termsModal')"), c);
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
