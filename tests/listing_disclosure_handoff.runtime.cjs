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
const readStart = html.indexOf('  window.hofLoadAgentListingWorkspaces =');
const readEnd = html.indexOf('  let listingWorkspaceLoadRevision', readStart);
assert.ok(readStart >= 0 && readEnd > readStart);
const listingRead = html.slice(readStart, readEnd);
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
  const calls = [], queries = [], timers = [], fetches = [], feedback = [];
  const user = {id: 'agent-one'};
  const listing = {id: 'listing-one', agent_user_id: user.id, listing_kind: kind, property_address: address, seller_names: sellers};
  let result = {data: [listing], error: null};
  const offer={id:'offer-one',user_id:user.id,property_address:'202 Fictional Offer Lane',offer_data:{
    seller1Name:'Offer Seller',seller1Email:'seller@example.test',buyer1Name:'Do not copy buyer',defect_roof:'N'}};
  let offerResult={data:offer,error:null};
  let readOffer;
  let resolvePending;
  let pending = false;
  const root = {hofAuth: {session: {user, access_token: 'fictional-token'}},
    setTimeout: fn => {timers.push(fn);},
    announceWorkspaceStatus: message => { if (message) feedback.push(message); },
    showAccountTab: tab => calls.push(['tab', tab]),
  };
  const listingResponse = value => ({ok: !value.error, json: async () => ({workspaces: value.data || []})});
  function fetch(url, options) {
    fetches.push([url, options]);
    const params = new URLSearchParams(String(url).split('?')[1] || '');
    if (params.get('scope') === 'agent_seller_disclosure_offer_context') {
      if (readOffer) return readOffer();
      const row = offerResult.data;
      const owns = row && row.id === params.get('offer_id') && row.user_id === user.id && !offerResult.error;
      const context = owns ? {offerId: row.id, propertyAddress: row.property_address,
        seller1Name: row.offer_data.seller1Name, seller2Name: row.offer_data.seller2Name || '',
        seller1Email: row.offer_data.seller1Email, seller2Email: row.offer_data.seller2Email || ''} : null;
      return Promise.resolve({ok: !!context, status: context ? 200 : 404, json: async () => ({context})});
    }
    if (pending) return new Promise(resolve => {resolvePending = value => resolve(listingResponse(value));});
    return Promise.resolve(listingResponse(result));
  }
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
  vm.runInNewContext(listingRead + handoff, {root, window: root, hofAuth: root.hofAuth, document, fetch, URLSearchParams,
    AbortController, AbortSignal, setTimeout: () => 1, clearTimeout: () => {}, active: () => true,
    renderCard: async () => {}, syncDisclosureDetails:()=>{}, syncWaterRightsVisibility: () => {calls.push(['water']);}});
  return {root, fields, card, responses, calls, queries, fetches, listing, timers, choices, feedback,
    setResult: value => {result = value;}, waitForQuery: () => {pending = true;}, resolve: value => resolvePending(value),
    offer,setOfferResult:value=>{offerResult=value;},
    setOfferRead: value => {readOffer = value;},
  };
}

test('offer handoff uses its owner-scoped API, reuses contacts, and never infers seller answers or buyers',async()=>{
 const p=setup();await p.root.startOfferSellerDisclosure('offer-one');
 assert.equal(p.fields.get('hofSellerAddress').value,'202 Fictional Offer Lane');
 assert.equal(p.fields.get('hofSeller1').value,'Offer Seller');
 assert.equal(p.fields.get('hofSellerEmail').value,'seller@example.test');
 assert.equal(p.fields.get('hofBuyer1').value,'');assert.ok(p.responses.every(f=>f.value===''));
 assert.match(p.fetches[0][0], /scope=agent_seller_disclosure_offer_context/);
 assert.match(p.fetches[0][0], /offer_id=offer-one/);
 assert.ok(!/getSupabaseClient|\.from\('hof_offers'\)/.test(handoff));
 assert.equal(p.fields.get('hofSendSellerReview').disabled,true);
});
test('foreign offer read cannot populate the questionnaire',async()=>{
 const p=setup();p.setOfferResult({data:{...p.offer,user_id:'other-owner'},error:null});
 await p.root.startOfferSellerDisclosure('offer-one');
 assert.equal(p.fields.get('hofSellerAddress').value,'');assert.equal(p.fields.get('hofSeller1').value,'');
 assert.match(p.feedback[0], /Refresh My Offers/);
 assert.ok(!p.calls.some(([action]) => action === 'tab'));
});
test('a failed lookup keeps the view and draft intact and the same button can retry', async () => {
 const p = setup({confirm: true});
 const button = element();
 button.textContent = 'Seller’s disclosure';
 p.fields.get('hofSellerAddress').value = 'Existing disclosure';
 p.responses[0].value = 'Y';
 let finish;
 p.setOfferRead(() => new Promise(resolve => {finish = resolve;}));
 const request = p.root.startOfferSellerDisclosure('offer-one', button);
 assert.equal(button.disabled, true);
 assert.equal(button.textContent, 'Opening disclosure…');
 await p.root.startOfferSellerDisclosure('offer-one', button);
 assert.equal(p.fetches.length, 1);
 finish({ok: false, status: 503, json: async () => ({})});
 await request;
 assert.equal(button.disabled, false);
 assert.equal(button.textContent, 'Seller’s disclosure');
 assert.equal(p.fields.get('hofSellerAddress').value, 'Existing disclosure');
 assert.equal(p.responses[0].value, 'Y');
 assert.ok(!p.calls.some(([action]) => action === 'tab'));
 assert.match(p.feedback[0], /try again/);
 p.setOfferRead(null);
 await p.root.startOfferSellerDisclosure('offer-one', button);
 assert.equal(p.fields.get('hofSellerAddress').value, '202 Fictional Offer Lane');
});
test('an offer response cannot open the disclosure after an account change and return', async () => {
 const p = setup();
 let finish;
 p.setOfferRead(() => new Promise(resolve => {finish = resolve;}));
 const request = p.root.startOfferSellerDisclosure('offer-one');
 p.root.__hofAccountProfileEpoch = 2;
 finish({ok: true, status: 200, json: async () => ({context: {offerId: 'offer-one', seller1Name: 'Stale'}})});
 await request;
 assert.equal(p.fields.get('hofSeller1').value, '');
 assert.ok(!p.calls.some(([action]) => action === 'tab'));
 assert.deepEqual(p.feedback, []);
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
  assert.equal(p.queries.length, 0);
  const [url, options] = p.fetches[0];
  const params = new URL(url, 'https://qa.example').searchParams;
  assert.equal(params.get('scope'), 'agent_listing_workspaces');
  assert.equal(params.get('workspace_id'), 'listing-one');
  assert.equal(params.get('limit'), '1');
  assert.equal(options.headers.Authorization, 'Bearer fictional-token');
  assert.ok(!/\.insert\(|\.update\(|\.delete\(/.test(handoff));
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
  assert.equal(p.fetches.length, 0);
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
