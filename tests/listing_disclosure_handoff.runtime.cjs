const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('  let listingDisclosureHandoffRevision = 0;');
const end = html.indexOf('  root.filterSellerDisclosureDrafts', start);
assert.ok(start >= 0 && end > start);
const handoff = html.slice(start, end);
const nextStart = html.indexOf('  function renderListingWorkspaceNextStep(workspace)');
const nextEnd = html.indexOf('  function listingWorkspaceLabel', nextStart);
assert.ok(nextStart >= 0 && nextEnd > nextStart);
const nextStep = html.slice(nextStart, nextEnd);

function element(value = '') {
  return {value, dataset: {}, options: [], disabled: false, children: [], handlers: {},
    textContent: '', attributes: {},
    appendChild(child) { this.children.push(child); if (child.value) this.options.push(child); },
    setAttribute(key, val) { this.attributes[key] = val; },
    addEventListener(key, fn) { this.handlers[key] = fn; },
    focus() { this.focused = true; }, scrollIntoView() { this.scrolled = true; },
  };
}

function setup({kind = 'sale', sellers = ['Ana García', 'Wei Chen'], address = '101 QA Lane', confirm = true} = {}) {
  const fields = new Map();
  for (const id of ['hofSellerDisclosureWorkspace', 'hofSellerAddress', 'hofSeller1', 'hofSeller2',
    'hofSellerEmail', 'hofSeller2Email', 'hofBuyer1', 'hofBuyer2', 'hofWaterSource', 'hofSellerDraftStatus',
    'hofSellerWorkspace', 'hofSendSellerReview', 'hofSaveSellerDraft']) fields.set(id, element());
  const responses = [element(), element()];
  const card = element();
  card.querySelectorAll = () => responses;
  fields.set('hofSellerDisclosureCard', card);
  const calls = [], queries = [], timers = [];
  const user = {id: 'agent-one'};
  const listing = {id: 'listing-one', agent_user_id: user.id, listing_kind: kind, property_address: address, seller_names: sellers};
  let result = {data: [listing], error: null};
  const offer={id:'offer-one',user_id:user.id,property_address:'202 Fictional Offer Lane',offer_data:{
    seller1Name:'Offer Seller',seller1Email:'seller@example.test',buyer1Name:'Do not copy buyer',defect_roof:'N'}};
  let offerResult={data:offer,error:null};
  let resolvePending;
  let pending = false;
  const query = {select: value => {queries.push(['select', value]); return query;},
    eq: (key, value) => {queries.push(['eq', key, value]); return query;},
    is:(key,value)=>{queries.push(['is',key,value]);return query;},maybeSingle:()=>Promise.resolve(offerResult),
    limit: count => {queries.push(['limit', count]); return pending ? new Promise(resolve => {resolvePending = resolve;}) : Promise.resolve(result);},
  };
  const root = {hofAuth: {session: {user}}, getSupabaseClient: () => ({from: table => {
    queries.push(['from', table]);
    return query;
  }}),
    setTimeout: fn => {timers.push(fn);},
  };
  const choices = [];
  const document = {getElementById: id => fields.get(id), createElement: () => {
    const modal = element();
    const keep = element(), replace = element();
    modal.remove = () => {modal.removed = true;};
    modal.querySelector = selector => selector === '[data-listing-keep]' ? keep : replace;
    modal.controls = {keep, replace};
    choices.push(modal);
    return modal;
  }, body: {appendChild: modal => {
    calls.push(['confirm', modal.innerHTML]);
    if (confirm !== null) queueMicrotask(() => modal.controls[confirm ? 'replace' : 'keep'].handlers.click());
  }}};
  vm.runInNewContext(handoff, {root, window: root, document, active: () => true,
    renderCard: async () => {}, syncDisclosureDetails:()=>{}, syncWaterRightsVisibility: () => {calls.push(['water']);}});
  return {root, fields, card, responses, calls, queries, listing, timers, choices,
    setResult: value => {result = value;}, waitForQuery: () => {pending = true;}, resolve: value => resolvePending(value),
    offer,setOfferResult:value=>{offerResult=value;},
  };
}

test('offer handoff reads the owner row, reuses contacts, and never infers seller answers or buyers',async()=>{
 const p=setup();await p.root.startOfferSellerDisclosure('offer-one');
 assert.equal(p.fields.get('hofSellerAddress').value,'202 Fictional Offer Lane');
 assert.equal(p.fields.get('hofSeller1').value,'Offer Seller');
 assert.equal(p.fields.get('hofSellerEmail').value,'seller@example.test');
 assert.equal(p.fields.get('hofBuyer1').value,'');assert.ok(p.responses.every(f=>f.value===''));
 assert.deepEqual(p.queries.filter(q=>q[0]==='eq'),[['eq','id','offer-one'],['eq','user_id','agent-one']]);
 assert.deepEqual(p.queries.find(q=>q[0]==='is'),['is','deleted_at',null]);
 assert.equal(p.fields.get('hofSendSellerReview').disabled,true);
});
test('foreign offer read cannot populate the questionnaire',async()=>{
 const p=setup();p.setOfferResult({data:{...p.offer,user_id:'other-owner'},error:null});
 await p.root.startOfferSellerDisclosure('offer-one');
 assert.equal(p.fields.get('hofSellerAddress').value,'');assert.equal(p.fields.get('hofSeller1').value,'');
});
test('offer handoff preserves current disclosure when the user keeps it',async()=>{
 const p=setup({confirm:false});p.fields.get('hofSellerAddress').value='Existing disclosure';
 await p.root.startOfferSellerDisclosure('offer-one');
 assert.equal(p.fields.get('hofSellerAddress').value,'Existing disclosure');
});

test('saved sale listing carries address and one/two seller names through an owner-scoped read, without saving or sending', async () => {
  const p = setup();
  assert.equal(await p.root.openSellerDisclosureDraftWorkspace('listing-one'), true);
  assert.equal(p.fields.get('hofSellerAddress').value, '101 QA Lane');
  assert.equal(p.fields.get('hofSeller1').value, 'Ana García');
  assert.equal(p.fields.get('hofSeller2').value, 'Wei Chen');
  assert.equal(p.fields.get('hofSellerWorkspace').value, 'listing-one');
  assert.deepEqual(p.fields.get('hofSellerWorkspace').options.map(o => o.textContent), ['101 QA Lane']);
  assert.equal(p.fields.get('hofSellerDisclosureWorkspace').open, true);
  assert.equal(p.fields.get('hofSendSellerReview').disabled, true);
  assert.equal(p.calls.some(c => c[0] === 'confirm'), false);
  assert.deepEqual(p.queries.filter(q => q[0] === 'eq'), [['eq', 'id', 'listing-one'], ['eq', 'agent_user_id', 'agent-one']]);
  assert.deepEqual(p.queries.at(-1), ['limit', 1]);
  assert.ok(!/\.insert\(|\.update\(|\.delete\(|fetch\(/.test(handoff));
});

test('one seller does not introduce a second seller, buyer or contact information', async () => {
  const p = setup({sellers: ['Only Seller']});
  await p.root.openSellerDisclosureDraftWorkspace('listing-one');
  for (const id of ['hofSeller2', 'hofBuyer1', 'hofBuyer2', 'hofSellerEmail', 'hofSeller2Email']) assert.equal(p.fields.get(id).value, '');
});

test('existing saved disclosure and unsaved answers remain untouched when agent keeps current work', async () => {
  const p = setup({confirm: false});
  p.card.dataset.loadedDraftId = 'saved-draft';
  p.card.dataset.sellerDraftId = 'saved-draft';
  p.fields.get('hofSellerAddress').value = 'Previous property';
  p.fields.get('hofSeller1').value = 'Previous Seller';
  p.fields.get('hofSellerWorkspace').value = 'previous-listing';
  p.responses[0].value = 'Y';
  assert.equal(await p.root.openSellerDisclosureDraftWorkspace('listing-one'), false);
  assert.equal(p.fields.get('hofSellerAddress').value, 'Previous property');
  assert.equal(p.fields.get('hofSellerWorkspace').value, 'previous-listing');
  assert.equal(p.responses[0].value, 'Y');
  assert.equal(p.card.dataset.loadedDraftId, 'saved-draft');
  assert.equal(p.card.dataset.sellerDraftId, 'saved-draft');
  assert.equal(p.calls.filter(c => c[0] === 'confirm').length, 1);
});

test('explicit new-disclosure choice clears old answers and draft ID instead of updating the old property', async () => {
  const p = setup();
  p.card.dataset.loadedDraftId = 'saved-draft';
  p.card.dataset.sellerDraftId = 'saved-draft';
  p.fields.get('hofBuyer1').value = 'Old Buyer';
  p.fields.get('hofSellerEmail').value = 'old@example.test';
  p.fields.get('hofWaterSource').value = 'old-water-form';
  p.responses[0].value = 'Y';
  assert.equal(await p.root.openSellerDisclosureDraftWorkspace('listing-one'), true);
  assert.equal(p.card.dataset.loadedDraftId, undefined);
  assert.equal(p.card.dataset.sellerDraftId, undefined);
  assert.equal(p.fields.get('hofBuyer1').value, '');
  assert.equal(p.fields.get('hofSellerEmail').value, '');
  assert.equal(p.fields.get('hofWaterSource').value, '');
  assert.equal(p.responses[0].value, '');
});

test('account change while the replacement choice is open does not clear or transfer previous work', async () => {
  const p = setup({confirm: null});
  p.fields.get('hofSellerAddress').value = 'Previous property';
  const pending = p.root.openSellerDisclosureDraftWorkspace('listing-one');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(p.choices.length, 1);
  p.root.hofAuth.session.user = {id: 'second-agent'};
  p.choices[0].controls.replace.handlers.click();
  assert.equal(await pending, false);
  assert.equal(p.fields.get('hofSellerAddress').value, 'Previous property');
});

test('replacement choice is an accessible in-page dialog with Keep as the default focus', async () => {
  const p = setup({confirm: null});
  p.fields.get('hofSeller1').value = 'Edited seller';
  const pending = p.root.openSellerDisclosureDraftWorkspace('listing-one');
  await new Promise(resolve => setImmediate(resolve));
  const modal = p.choices[0];
  assert.match(modal.innerHTML, /role="dialog" aria-modal="true" aria-labelledby=/);
  assert.equal(modal.controls.keep.focused, true);
  assert.equal(modal.controls.replace.focused, undefined);
  let prevented = false;
  modal.handlers.keydown({key: 'Escape', preventDefault: () => {prevented = true;}});
  assert.equal(await pending, false);
  assert.equal(prevented, true);
  assert.equal(modal.removed, true);
  assert.equal(p.fields.get('hofSeller1').value, 'Edited seller');
  assert.ok(!/root\.confirm\(/.test(handoff));
});

for (const [name, result] of [
  ['missing row', {data: []}],
  ['foreign owner', {data: [{id: 'listing-one', agent_user_id: 'other-agent'}]}],
  ['wrong listing', {data: [{id: 'other-listing', agent_user_id: 'agent-one'}]}],
  ['query failure', {data: [], error: new Error('read failed')}],
]) test(`${name} cannot prefill the disclosure`, async () => {
  const p = setup(); p.setResult(result);
  await assert.rejects(p.root.openSellerDisclosureDraftWorkspace('listing-one'));
  assert.equal(p.fields.get('hofSellerAddress').value, '');
  assert.equal(p.fields.get('hofSellerWorkspace').value, '');
});

test('late listing response cannot leak across account changes', async () => {
  const p = setup(); p.waitForQuery();
  const result = p.root.openSellerDisclosureDraftWorkspace('listing-one');
  p.root.hofAuth.session.user = {id: 'second-agent'};
  p.resolve({data: [p.listing]});
  assert.equal(await result, false);
  assert.equal(p.fields.get('hofSellerAddress').value, '');
  assert.equal(p.fields.get('hofSellerDraftStatus').textContent, '');
});

test('a newer listing request wins over an older delayed result', async () => {
  const p = setup(); p.waitForQuery();
  const first = p.root.openSellerDisclosureDraftWorkspace('listing-one');
  p.resolve({data: [p.listing]});
  // Starting the next request before the first continuation runs invalidates it.
  const second = p.root.openSellerDisclosureDraftWorkspace('listing-two');
  assert.equal(await first, false);
  assert.equal(p.fields.get('hofSellerAddress').value, '');
  p.resolve({data: [{...p.listing, id: 'listing-two', property_address: '202 QA Lane'}]});
  assert.equal(await second, true);
  assert.equal(p.fields.get('hofSellerAddress').value, '202 QA Lane');
});

for (const [name, options] of [
  ['lease listing', {kind: 'lease'}],
  ['three sellers', {sellers: ['A', 'B', 'C']}],
  ['empty property', {address: ''}],
]) test(`${name} is not silently converted or truncated`, async () => {
  const p = setup(options);
  assert.equal(await p.root.openSellerDisclosureDraftWorkspace('listing-one'), false);
  assert.equal(p.fields.get('hofSellerAddress').value, '');
  assert.equal(p.fields.get('hofSellerWorkspace').value, '');
});

test('saving an existing disclosure prevents a simultaneous new-listing handoff', async () => {
  const p = setup(); p.fields.get('hofSaveSellerDraft').disabled = true;
  assert.equal(await p.root.openSellerDisclosureDraftWorkspace('listing-one'), false);
  assert.match(p.fields.get('hofSellerDraftStatus').textContent, /saving/);
  assert.equal(p.calls.some(c => c[0] === 'confirm'), false);
});

test('ordinary disclosure navigation remains available without any listing read', async () => {
  const p = setup();
  assert.equal(await p.root.openSellerDisclosureDraftWorkspace(), true);
  assert.equal(p.queries.length, 0);
});

for (const kind of ['sale', 'lease']) test(`${kind} next-step card offers only appropriate actions and keeps planning available`, () => {
  const controls = {'[data-listing-planning]': element(), button: element()};
  if (kind === 'sale') controls['[data-listing-disclosure]'] = element();
  const card = element(); card.querySelector = selector => controls[selector];
  const fields = new Map([['listingWorkspaceStartCard', {insertAdjacentElement: (position, node) => {assert.equal(position, 'afterend'); assert.equal(node, card);}}]]);
  const opened = [];
  const window = {openSellerDisclosureDraftWorkspace: async id => opened.push(id)};
  const document = {getElementById: id => fields.get(id), createElement: () => card};
  const context = {window, document, openListingWorkspaceSection: id => opened.push(id), platformStatus: () => {},
    escapeAttr: v => String(v).replaceAll('<', '&lt;').replaceAll('>', '&gt;')};
  vm.createContext(context); vm.runInContext(nextStep, context);
  context.renderListingWorkspaceNextStep({id: 'listing-one', listing_kind: kind, property_address: '<script>QA</script>'});
  assert.match(card.innerHTML, /Question 3/);
  assert.equal(card.innerHTML.includes('data-listing-disclosure'), kind === 'sale');
  assert.ok(!card.innerHTML.includes('<script>QA</script>'));
  controls['[data-listing-planning]'].handlers.click();
  assert.ok(opened.includes('listingWorkspaceTools'));
  assert.equal(card.scrolled, true);
});
