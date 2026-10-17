const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const html = fs.readFileSync(process.env.HOF_BROKERAGE_SAVE_SOURCE || path.join(__dirname, '../index.html'), 'utf8');
function block(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a);
  assert.ok(a >= 0 && b > a, start);
  return html.slice(a, b);
}
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return {promise, resolve, reject};
}
async function tick() { for (let i = 0; i < 6; i++) await Promise.resolve(); }
async function drainWrites(h) {
  for (let i = 0; i < 5; i++) {
    for (const call of h.calls) call.resolve({data:{id:'BA', name:'Example Firm A'}});
    await tick();
  }
}
function harness() {
  const calls = [], requests = [], statuses = [], nodes = {};
  for (const id of ['saveBrokerageFoundationButton', 'saveBrokerageSharedDefaultsButton', 'brokerageDefaultsResult',
                    'brokerageDefaultTitleCompany', 'brokerageDefaultTitleContact']) {
    nodes[id] = {disabled:false, textContent:'', value:'', setAttribute() {}};
  }
  nodes.brokerageDefaultTitleCompany.value = 'Example Title A';
  const c = vm.createContext({Date, console:{error() {}},
    document:{getElementById:id => nodes[id] || null},
    getVal:id => ({brandBrokerageName:'Example Firm A', brandLicense:'12345'}[id] || ''),
    platformCustomerError:(_error, fallback) => fallback,
    platformStatus:(id, message, tone) => statuses.push({id, message, tone})});
  c.root = c; c.window = c;
  c.hofAuth = {session:{user:{id:'A', email:'a@example.test'}, access_token:'fictional-A'}};
  c.__hofAccountProfileEpoch = 1;
  c.hofPlatform = {brokerage:{id:'BA', name:'Example Firm A'}};
  c.platformUser = () => c.hofAuth.session?.user || null;
  c.renderBrokerageFoundationPanel = async () => { c.renderCount = (c.renderCount || 0) + 1; };
  c.fetch = (_url, options) => { const d = deferred(); requests.push({options, ...d}); return d.promise; };
  c.getSupabaseClient = () => ({from(table) {
    const d = deferred(), record = {table, ...d, filters:[]};
    const q = {update(payload) { record.payload = payload; record.method = 'update'; calls.push(record); return q; },
      insert(payload) { record.payload = payload; record.method = 'insert'; calls.push(record); return q; },
      eq(key, value) { record.filters.push([key,value]); return q; }, select() { return q; },
      single() { return d.promise; }, then(yes,no) { return d.promise.then(yes,no); }};
    return q;
  }});
  vm.runInContext(block('  function brokerageLicenseDefault(', '  function applyBrokerageLicenseDefaults('), c);
  vm.runInContext(block('  async function saveBrokerageFoundation()', '  function renderSellerFoundationPanel()'), c);
  vm.runInContext(block('  root.saveBrokerageSharedDefaults =', '  root.applyBrokerageSharedDefaults ='), c);
  return {c, calls, requests, statuses, nodes};
}
function switchAccount(h, id = 'B', brokerageId = 'BB') {
  h.c.hofAuth.session = {user:{id, email:id.toLowerCase()+'@example.test'}, access_token:'fictional-'+id};
  h.c.__hofAccountProfileEpoch++;
  h.c.hofPlatform.brokerage = {id:brokerageId, name:'Current firm'};
}
function sharedResponse(request, defaults = {defaultTitleCompany:'Example Title A'}) {
  request.resolve({ok:true, json:async () => ({defaults})});
}
test('shared default response cannot replace the next account brokerage', async () => {
  const h = harness(), p = h.c.saveBrokerageSharedDefaults(); switchAccount(h);
  sharedResponse(h.requests[0]); await p;
  assert.equal(h.c.hofPlatform.brokerage.id, 'BB'); assert.equal(h.c.renderCount || 0, 0);
});
test('shared default response cannot cross a same-user sign-out epoch', async () => {
  const h = harness(), p = h.c.saveBrokerageSharedDefaults(); switchAccount(h, 'A');
  sharedResponse(h.requests[0]); await p;
  assert.equal(h.c.hofPlatform.brokerage.id, 'BB');
});
test('same account changing brokerage ignores an earlier default response', async () => {
  const h = harness(), p = h.c.saveBrokerageSharedDefaults();
  h.c.hofPlatform.brokerage = {id:'BB'}; sharedResponse(h.requests[0]); await p;
  assert.equal(h.c.hofPlatform.brokerage.id, 'BB');
});
test('obsolete shared-default failure does not show an error in the new account', async () => {
  const h = harness(), p = h.c.saveBrokerageSharedDefaults(); switchAccount(h);
  h.nodes.brokerageDefaultsResult.textContent = 'Current account';
  h.requests[0].reject(new Error('private old failure')); await p;
  assert.equal(h.nodes.brokerageDefaultsResult.textContent, 'Current account');
});
test('ordinary shared-default save keeps its original token, updates settings and restores the button', async () => {
  const h = harness(), p = h.c.saveBrokerageSharedDefaults();
  assert.equal(h.requests[0].options.headers.Authorization, 'Bearer fictional-A');
  await h.c.saveBrokerageSharedDefaults(); assert.equal(h.requests.length, 1);
  sharedResponse(h.requests[0]); await p;
  assert.equal(h.c.hofPlatform.brokerage.default_title_company, 'Example Title A');
  assert.equal(h.c.renderCount, 1); assert.equal(h.nodes.saveBrokerageSharedDefaultsButton.disabled, false);
});
test('branding result after sign-out cannot publish stale state or start a profile write', async () => {
  const h = harness(), p = h.c.saveBrokerageFoundation(); switchAccount(h);
  h.calls[0].resolve({data:{id:'BA', name:'Old firm'}}); await drainWrites(h); await p;
  assert.equal(h.c.hofPlatform.brokerage.id, 'BB'); assert.equal(h.calls.length, 1);
  assert.equal(h.statuses.length, 0);
});
test('branding column fallback cannot launch after account context changes', async () => {
  const h = harness(), p = h.c.saveBrokerageFoundation(); switchAccount(h);
  h.calls[0].resolve({error:{message:'column does not exist'}}); await drainWrites(h); await p;
  assert.equal(h.calls.length, 1); assert.equal(h.c.hofPlatform.brokerage.id, 'BB');
});
test('branding fallback in the same context retains the originally selected brokerage', async () => {
  const h = harness(), p = h.c.saveBrokerageFoundation();
  h.calls[0].resolve({error:{message:'column does not exist'}}); await tick();
  assert.deepEqual(h.calls[1].filters, [['id','BA']]);
  h.calls[1].resolve({data:{id:'BA', name:'Example Firm A'}}); await tick();
  h.calls[2].resolve({data:{id:'A', brokerage_id:'BA'}}); await p;
  assert.equal(h.statuses.at(-1).tone, 'ok');
});
test('late profile-link completion does not show success in the next account', async () => {
  const h = harness(), p = h.c.saveBrokerageFoundation();
  h.calls[0].resolve({data:{id:'BA', name:'Example Firm A'}}); await tick();
  switchAccount(h); h.calls[1].resolve({data:{id:'A', brokerage_id:'BA'}}); await p;
  assert.equal(h.c.hofPlatform.brokerage.id, 'BB'); assert.equal(h.statuses.length, 0);
});
test('profile-link error is visible rather than a false completed setup', async () => {
  const h = harness(), p = h.c.saveBrokerageFoundation();
  h.calls[0].resolve({data:{id:'BA', name:'Example Firm A'}}); await tick();
  h.calls[1].resolve({error:{message:'private database error'}}); await p;
  assert.equal(h.statuses.at(-1).tone, 'err'); assert.doesNotMatch(h.statuses.at(-1).message, /private database/);
});
test('a repeated branding tap does not start a second write', async () => {
  const h = harness(), p = h.c.saveBrokerageFoundation(), duplicate = h.c.saveBrokerageFoundation();
  const writes = h.calls.length;
  for (const call of h.calls) call.resolve({data:{id:'BA'}});
  await tick(); for (const call of h.calls) call.resolve({data:{id:'A', brokerage_id:'BA'}});
  await Promise.all([p,duplicate]); assert.equal(writes, 1);
  assert.equal(h.nodes.saveBrokerageFoundationButton.disabled, false);
});
test('a silently empty profile-link response cannot claim setup succeeded', async () => {
  const h = harness(), p = h.c.saveBrokerageFoundation();
  h.calls[0].resolve({data:{id:'BA', name:'Example Firm A'}}); await tick();
  h.calls[1].resolve({data:null}); await p;
  assert.equal(h.statuses.at(-1).tone, 'err');
});
test('a new brokerage whose profile link failed is retained for retry instead of inserted twice', async () => {
  const h = harness(); h.c.hofPlatform.brokerage = null;
  const first = h.c.saveBrokerageFoundation(); assert.equal(h.calls[0].method, 'insert');
  h.calls[0].resolve({data:{id:'NEW', name:'Example Firm A'}}); await tick();
  h.calls[1].resolve({error:{message:'temporary failure'}}); await first;
  assert.equal(h.c.hofPlatform.brokerage.id, 'NEW'); assert.equal(h.statuses.at(-1).tone, 'err');
  const second = h.c.saveBrokerageFoundation();
  assert.equal(h.calls[2].method, 'update'); assert.deepEqual(h.calls[2].filters, [['id','NEW']]);
  h.calls[2].resolve({data:{id:'NEW', name:'Example Firm A'}}); await tick();
  h.calls[3].resolve({data:{id:'A', brokerage_id:'NEW'}}); await second;
  assert.equal(h.statuses.at(-1).tone, 'ok');
});
