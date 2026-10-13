const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(require('node:path').join(__dirname, '..', 'index.html'), 'utf8');
function block(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert.ok(a >= 0 && b > a);
  return html.slice(a, b);
}
function deferred() { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; }
function harness() {
  const queue = [], panel = { innerHTML: '' }, dashboard = { innerHTML: '' };
  const pane = { active: false, classList: { contains(name) { return name === 'active' && pane.active; } } };
  const context = vm.createContext({ console: { warn() {} }, state: { data: {} },
    document: { getElementById: id => id === 'brokerageFoundationPanel' ? panel : id === 'brokerSafeDashboard' ? dashboard : id === 'accountPanelBrokerage' ? pane : null },
    safe: value => String(value || ''), brokerSummary: () => { const d = deferred(); queue.push({ table: 'summary', d }); return d.promise; } });
  context.root = context; context.window = context;
  context.hofAuth = { session: { user: { id: 'A' } } };
  context.hofPlatform = {};
  context.getSupabaseClient = () => ({ from(table) {
    const q = { select() { return q; }, eq() { return q; }, maybeSingle() {
      const d = deferred(); queue.push({ table, d }); return d.promise;
    } }; return q;
  } });
  vm.runInContext(block('  root.loadBrokerageFoundation = async function loadBrokerageFoundation()', '  async function brokerSummary()'), context);
  vm.runInContext(block('  function resetProfileForSessionChange(session)', '  function beginAccountProfileLoad()'), context);
  vm.runInContext(block('  root.renderBrokerageFoundationPanel = async function renderBrokerageFoundationPanel()', '  root.openBrokerageMembershipRequest ='), context);
  return { c: context, queue, panel, dashboard, pane };
}
async function profile(h, result = { data: { id: 'A', brokerage_id: 'BA', role: 'agent' } }) {
  h.queue.shift().d.resolve(result); await Promise.resolve(); await Promise.resolve();
}
function finish(h, name = 'Current firm', membership = { role: 'agent', status: 'active' }) {
  h.queue.shift().d.resolve({ data: { id: 'BA', name } }); h.queue.shift().d.resolve({ data: membership });
}
test('successful load commits the complete brokerage state', async () => {
  const h = harness(), p = h.c.loadBrokerageFoundation(); await profile(h); finish(h);
  assert.equal((await p).name, 'Current firm'); assert.equal(h.c.hofPlatform.brokerageMembership.status, 'active');
});
test('profile response from a signed-out session is ignored', async () => {
  const h = harness(), p = h.c.loadBrokerageFoundation(); h.c.hofAuth.session = null; await profile(h);
  const extraRequests = h.queue.length; if (extraRequests) finish(h);
  assert.equal(await p, null); assert.equal(extraRequests, 0); assert.equal(h.c.hofAuth.authoritativeProfile, undefined);
});
test('brokerage response cannot restore old account state after switching', async () => {
  const h = harness(), p = h.c.loadBrokerageFoundation(); await profile(h);
  h.c.resetProfileForSessionChange({ user: { id: 'B' } }); h.c.hofAuth.session = { user: { id: 'B' } }; finish(h, 'Old firm');
  assert.equal(await p, null); assert.equal(h.c.hofPlatform.brokerage, null); assert.equal(h.c.hofAuth.authoritativeProfile, null);
});
test('same user returning after sign-out does not revive an earlier request', async () => {
  const h = harness(), p = h.c.loadBrokerageFoundation(); await profile(h);
  h.c.resetProfileForSessionChange(null); h.c.hofAuth.session = null;
  h.c.resetProfileForSessionChange({ user: { id: 'A' } }); h.c.hofAuth.session = { user: { id: 'A' } }; finish(h);
  assert.equal(await p, null); assert.equal(h.c.hofPlatform.brokerage, null);
});
test('latest request wins when requests resolve out of order', async () => {
  const h = harness(), old = h.c.loadBrokerageFoundation(), olderProfile = h.queue.shift();
  h.c.hofAuth.session = { user: { id: 'B' } };
  const fresh = h.c.loadBrokerageFoundation(); await profile(h, { data: { id: 'B', brokerage_id: 'BA' } }); finish(h, 'Fresh firm'); await fresh;
  olderProfile.d.resolve({ data: { brokerage_id: 'OLD' } });
  await Promise.resolve(); await Promise.resolve(); if (h.queue.length) finish(h, 'Old firm');
  assert.equal(await old, null); assert.equal(h.c.hofPlatform.brokerage.name, 'Fresh firm'); assert.equal(h.queue.length, 0);
});
test('failed refresh removes cached brokerage and provides a retry state', async () => {
  const h = harness(); h.c.hofPlatform.brokerage = { name: 'Stale firm' }; h.c.hofPlatform.brokerageMembership = { role: 'owner' };
  const p = h.c.loadBrokerageFoundation(); await profile(h, { error: new Error('private failure') }); await p;
  assert.equal(h.c.hofPlatform.brokerage, null); assert.equal(h.c.hofPlatform.brokerageMembership, null);
  assert.ok(h.c.hofPlatform.brokerageLoadError); assert.ok(!h.c.hofPlatform.brokerageLoadError.includes('private failure'));
});
test('unconnected profile clears old membership without claiming an error', async () => {
  const h = harness(); h.c.hofPlatform.brokerageMembership = { role: 'owner' };
  const p = h.c.loadBrokerageFoundation(); await profile(h, { data: { id: 'A', brokerage_id: null } }); await p;
  assert.equal(h.c.hofPlatform.brokerageMembership, null); assert.equal(h.c.hofPlatform.brokerageLoadError, '');
});
test('session reset clears cached roster and brokerage display', () => {
  const h = harness(); h.c.hofPlatform.brokerage = { name: 'Old' }; h.c.hofPlatform.brokerageAgents = [{ email: 'old' }]; h.panel.innerHTML = 'Old roster';
  h.c.resetProfileForSessionChange(null);
  assert.equal(h.c.hofPlatform.brokerage, null); assert.deepEqual(Array.from(h.c.hofPlatform.brokerageAgents), []); assert.equal(h.panel.innerHTML.includes('Old'), false);
});
test('late broker summary cannot update the next account roster or display', async () => {
  const h = harness(); h.c.hofPlatform.brokerage = { name: 'Old' }; h.c.hofPlatform.brokerageMembership = { role: 'owner' };
  const p = h.c.renderBrokerageFoundationPanel(); const response = h.queue.shift();
  h.c.resetProfileForSessionChange(null); h.c.hofAuth.session = null; h.dashboard.innerHTML = 'New view';
  response.d.resolve({ agents: [{ email: 'old' }] }); await p;
  assert.deepEqual(Array.from(h.c.hofPlatform.brokerageAgents), []); assert.equal(h.dashboard.innerHTML, 'New view');
});
test('late broker error cannot overwrite a newer account dashboard', async () => {
  const h = harness(); h.c.hofPlatform.brokerage = { name: 'Old' }; h.c.hofPlatform.brokerageMembership = { role: 'owner' };
  h.c.brokerSummary = async () => { h.c.resetProfileForSessionChange(null); h.c.hofAuth.session = null; throw new Error('old error'); };
  h.dashboard.innerHTML = 'New view'; await h.c.renderBrokerageFoundationPanel();
  assert.equal(h.dashboard.innerHTML, 'New view');
});
test('brokerage or membership errors never publish a partial profile', async () => {
  const h = harness(), p = h.c.loadBrokerageFoundation(); await profile(h);
  h.queue.shift().d.resolve({ data: { name: 'Firm' } }); h.queue.shift().d.resolve({ error: new Error('RLS') }); await p;
  assert.equal(h.c.hofAuth.authoritativeProfile, null); assert.equal(h.c.hofPlatform.brokerage, null);
  assert.ok(h.c.hofPlatform.brokerageLoadError);
});
test('obsolete failure cannot erase the newer successful result', async () => {
  const h = harness(), p = h.c.loadBrokerageFoundation(); const old = h.queue.shift();
  h.c.hofAuth.session = { user: { id: 'B' } };
  const fresh = h.c.loadBrokerageFoundation(); await profile(h, { data: { id: 'B', brokerage_id: 'BA' } }); finish(h, 'Fresh'); await fresh;
  old.d.resolve({ error: new Error('old failure') }); await p;
  assert.equal(h.c.hofPlatform.brokerage.name, 'Fresh'); assert.equal(h.c.hofPlatform.brokerageLoadError, '');
});
test('failed load shows retry rather than a false missing-brokerage notice', async () => {
  const h = harness(), p = h.c.renderBrokerageFoundationPanel(); await profile(h, { error: new Error('timeout') }); await p;
  assert.match(h.panel.innerHTML, /Try again/); assert.match(h.panel.innerHTML, /role="status"/);
  assert.equal(h.panel.innerHTML.includes('not connected'), false); assert.equal(h.panel.innerHTML.includes('timeout'), false);
});
test('retry recovers into the correct agent workspace', async () => {
  const h = harness(); h.c.hofPlatform.brokerageLoadError = 'Failed';
  const p = h.c.retryBrokerageWorkspace(); await profile(h); finish(h, 'Recovered firm'); await p;
  assert.match(h.panel.innerHTML, /Recovered firm/); assert.equal(h.panel.innerHTML.includes('Try again'), false);
});
test('ordinary unconnected account retains its dedicated enrollment link', async () => {
  const h = harness(), p = h.c.renderBrokerageFoundationPanel(); await profile(h, { data: { id: 'A' } }); await p;
  assert.match(h.panel.innerHTML, /not connected/); assert.match(h.panel.innerHTML, /href="\/ondemand/);
});
test('signing out during retry does not render the next account', async () => {
  const h = harness(); let renders = 0; h.c.renderBrokerageFoundationPanel = async () => { renders++; };
  const p = h.c.retryBrokerageWorkspace(); h.c.resetProfileForSessionChange(null); h.c.hofAuth.session = null;
  await profile(h); await p; assert.equal(renders, 0);
});
test('same-user profile refresh does not discard brokerage cache', () => {
  const h = harness(); h.c.hofPlatform.brokerage = { name: 'Current' };
  h.c.resetProfileForSessionChange({ user: { id: 'A' } }); assert.equal(h.c.hofPlatform.brokerage.name, 'Current');
});
test('a failed explicit retry makes only one load attempt', async () => {
  const h = harness(), p = h.c.retryBrokerageWorkspace();
  await profile(h, { error: new Error('timeout') }); await Promise.resolve(); await Promise.resolve();
  const extra = h.queue.length; if (extra) await profile(h, { error: new Error('timeout') });
  await p; assert.equal(extra, 0); assert.match(h.panel.innerHTML, /Try again/);
});
test('startup and tab rendering share the in-flight load without showing false disconnection', async () => {
  const h = harness(), startup = h.c.loadBrokerageFoundation(), tab = h.c.renderBrokerageFoundationPanel();
  assert.equal(h.queue.length, 1);
  await profile(h); finish(h, 'OnDemand'); await Promise.all([startup, tab]);
  assert.match(h.panel.innerHTML, /OnDemand/); assert.equal(h.panel.innerHTML.includes('not connected'), false);
});
test('a later startup read refreshes the still-visible connection automatically', async () => {
  const h = harness(); h.c.hofAuth.session = null; h.pane.active = true;
  await h.c.renderBrokerageFoundationPanel();
  h.c.hofAuth.session = { user: { id: 'A' } }; const p = h.c.loadBrokerageFoundation();
  await profile(h); finish(h, 'OnDemand'); await p;
  assert.match(h.panel.innerHTML, /OnDemand/); assert.equal(h.panel.innerHTML.includes('not connected'), false);
});
test('late startup does not touch an inactive Brokerage pane', async () => {
  const h = harness(); h.panel.innerHTML = 'Hidden previous view';
  const p = h.c.loadBrokerageFoundation(); await profile(h); finish(h, 'OnDemand'); await p;
  assert.equal(h.panel.innerHTML, 'Hidden previous view');
});
test('late startup failure refreshes only the visible pane with a truthful retry', async () => {
  const h = harness(); h.pane.active = true; h.panel.innerHTML = 'Stale connection';
  const p = h.c.loadBrokerageFoundation(); await profile(h, { error: new Error('timeout') }); await p;
  assert.match(h.panel.innerHTML, /Try again/); assert.equal(h.panel.innerHTML.includes('Stale connection'), false); assert.equal(h.queue.length, 0);
});
