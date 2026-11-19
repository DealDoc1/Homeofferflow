const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createHandler, MAX_BUYER_NAME_LENGTH } = require('../lib/offer-draft-handler.js');
const checkoutSource = fs.readFileSync(path.join(__dirname, '../api/create-checkout.js'), 'utf8');

test('stable offer-draft route marker dispatches to the shared Vercel Node function', async () => {
  const moduleObject = { exports: {} };
  let statusCode = 0;
  let payload = null;
  const draftHandler = createHandler({
    supabaseUrl: 'https://project.example',
    serviceRoleKey: 'service-secret',
    fetchImpl: async () => response({ id: ownerId })
  });
  vm.runInNewContext(checkoutSource, {
    module: moduleObject,
    URL,
    process: { env: {} },
    console: { error() {} },
    require(name) {
      if (name === '../lib/offer-draft-handler') return draftHandler;
      if (name === 'stripe') return () => null;
      if (name === '../lib/checkout_payload') return {};
      throw new Error(`Unexpected require: ${name}`);
    }
  });
  await moduleObject.exports({ method: 'POST', query: { __hof_route: 'offer-draft' }, headers: {}, body: {} }, {
    status(code) { statusCode = code; return this; },
    json(value) { payload = value; return this; }
  });
  assert.equal(statusCode, 401);
  assert.equal(payload.error, 'Please sign in again to save this draft.');
});

const ownerId = '11111111-1111-4111-8111-111111111111';
const otherId = '22222222-2222-4222-8222-222222222222';
const offerId = '33333333-3333-4333-8333-333333333333';

function response(data, status = 200) {
  return { ok: status >= 200 && status < 300, status, text: async () => JSON.stringify(data), json: async () => data };
}

function setup({ current = { id: offerId, user_id: ownerId, status: 'Draft', last_updated: '2026-10-23T10:00:00.000Z', offer_data: {} }, patchRows = [{ id: offerId, status: 'Draft', last_updated: '2026-10-23T10:05:00.000Z' }], idempotentRows = [], authStatus = 200, profileRole = 'agent' } = {}) {
  const calls = [];
  const handler = createHandler({
    supabaseUrl: 'https://project.example', serviceRoleKey: 'service-secret', now: () => '2026-10-23T10:05:00.000Z',
    fetchImpl: async (url, options = {}) => {
      calls.push({ url, options });
      if (url.includes('/auth/v1/user')) return response(authStatus === 200 ? { id: ownerId } : {}, authStatus);
      if (url.includes('/rest/v1/hof_profiles')) return response(profileRole ? [{ role: profileRole }] : []);
      if (new URL(url).searchParams.has('offer_data->>_hof_native_draft_request_id')) return response(idempotentRows);
      if (options.method === 'POST') return response([{ id: offerId, status: 'Draft', last_updated: options.body && JSON.parse(options.body).last_updated }], 201);
      if (options.method === 'PATCH') return response(patchRows);
      return response(current ? [current] : []);
    }
  });
  const invoke = async (body, { method = 'POST', authorization = 'Bearer user-access-token' } = {}) => {
    let result;
    const res = { status(code) { this.statusCode = code; return this; }, json(value) { result = value; return value; }, setHeader(name, value) { this[name] = value; } };
    await handler({ method, headers: { authorization }, body }, res);
    return { status: res.statusCode, result, res };
  };
  return { calls, invoke };
}

function concurrentNativeCreateSetup() {
  const calls = [];
  const offers = new Map();
  let initialLookups = 0;
  let releaseLookups;
  const allInitialLookups = new Promise(resolve => { releaseLookups = resolve; });
  const handler = createHandler({
    supabaseUrl: 'https://project.example', serviceRoleKey: 'service-secret', now: () => '2026-10-23T10:05:00.000Z',
    fetchImpl: async (url, options = {}) => {
      calls.push({ url, options });
      if (url.includes('/auth/v1/user')) return response({ id: ownerId });
      const query = new URL(url).searchParams;
      if (url.includes('/rest/v1/hof_profiles')) return response([{ role: 'agent' }]);
      if (query.has('offer_data->>_hof_native_draft_request_id') && !query.has('id')) {
        initialLookups += 1;
        if (initialLookups === 2) releaseLookups();
        await allInitialLookups;
        return response([]);
      }
      if (options.method === 'POST') {
        const body = JSON.parse(options.body);
        if (offers.has(body.id)) return response({ code: '23505', message: 'duplicate key' }, 409);
        const saved = { ...body, status: 'Draft' };
        offers.set(body.id, saved);
        return response([{ id: saved.id, status: saved.status, last_updated: saved.last_updated }], 201);
      }
      if (query.has('id')) {
        const id = query.get('id').replace(/^eq\./, '');
        const saved = offers.get(id);
        const requestKey = query.get('offer_data->>_hof_native_draft_request_id')?.replace(/^eq\./, '');
        if (saved?.user_id === query.get('user_id')?.replace(/^eq\./, '') &&
            saved.offer_data?._hof_native_draft_request_id === requestKey) {
          return response([{
            id: saved.id, status: saved.status, last_updated: saved.last_updated,
            buyer_name: saved.buyer_name, buyer2_name: saved.buyer2_name, offer_price: saved.offer_price
          }]);
        }
        return response([]);
      }
      return response([]);
    }
  });
  const invoke = async body => {
    let result;
    const res = { status(code) { this.statusCode = code; return this; }, json(value) { result = value; return value; } };
    await handler({ method: 'POST', headers: { authorization: 'Bearer user-access-token' }, body }, res);
    return { status: res.statusCode, result };
  };
  return { calls, offers, invoke };
}

function draft(overrides = {}) {
  return {
    user_id: otherId, role: 'agent', property_address: '123 QA Road', buyer_name: 'QA Buyer',
    offer_price: 400000, status: 'Buyer Signed', generated_at: 'forged',
    offer_data: { repairsText: 'Agreed repairs', _hof_signature_delivery: { secret: true }, _hof_native_draft_request_id: 'forged', signwell: { document_id: 'forged' } },
    ...overrides
  };
}

test('requires POST and a verified bearer account', async () => {
  const method = setup();
  const methodResult = await method.invoke({}, { method: 'GET' });
  assert.equal(methodResult.status, 405);
  assert.equal(methodResult.res['Cache-Control'], 'private, no-store');
  const missing = setup();
  const missingResult = await missing.invoke({}, { authorization: '' });
  assert.equal(missingResult.status, 401);
  assert.equal(missingResult.res['Cache-Control'], 'private, no-store');
  assert.equal(missing.calls.length, 0);
  const invalid = setup({ authStatus: 401 });
  assert.equal((await invalid.invoke({ draft: draft() })).status, 401);
  assert.equal(invalid.calls.length, 1);
});

test('new drafts bind to the verified owner and strip client signing state', async () => {
  const { calls, invoke } = setup();
  const result = await invoke({ offerId: null, draft: draft() });
  assert.equal(result.status, 201);
  assert.equal(result.res['Cache-Control'], 'private, no-store');
  const insert = calls.find(({ options }) => options.method === 'POST');
  const body = JSON.parse(insert.options.body);
  assert.equal(body.user_id, ownerId);
  assert.equal(body.role, 'agent');
  assert.equal(body.status, 'Draft');
  assert.equal(body.last_updated, '2026-10-23T10:05:00.000Z');
  assert.equal(body.property_address, '123 QA Road');
  assert.equal(body.offer_data.repairsText, 'Agreed repairs');
  assert.equal('_hof_signature_delivery' in body.offer_data, false);
  assert.equal('_hof_native_draft_request_id' in body.offer_data, false);
  assert.equal('signwell' in body.offer_data, false);
  assert.equal('generated_at' in body, false);
  assert.equal('status' in JSON.parse(calls.find(({ options }) => options.method !== 'POST' && options.method !== 'PATCH').options.body || '{}'), false);
});

test('shared draft API rejects malformed, negative, fractional-cent, and unsafe prices before storage writes', async () => {
  const invalidDrafts = [
    draft({ offer_price: '$1,2' }), draft({ offer_price: '12,34,567' }),
    draft({ offer_price: '-1' }), draft({ offer_price: '0' }), draft({ offer_price: 0 }),
    draft({ offer_price: '1.234' }),
    draft({ offer_price: '90071992547409.92' })
  ];
  const nestedOnlyInvalid = draft({ offer_data: { price: '$1,2' } });
  delete nestedOnlyInvalid.offer_price;
  invalidDrafts.push(nestedOnlyInvalid);
  invalidDrafts.push(draft({ offer_price: null, offer_data: { price: '0' } }));
  for (const invalidDraft of invalidDrafts) {
    const { calls, invoke } = setup();
    const result = await invoke({ offerId: null, draft: invalidDraft });
    assert.equal(result.status, 422, JSON.stringify(invalidDraft));
    assert.equal(result.result.code, 'invalid_draft');
    assert.equal(calls.some(({ options }) => options.method === 'POST' || options.method === 'PATCH'), false);
  }
});

test('shared draft API normalizes valid grouped prices and permits an omitted optional price', async () => {
  const grouped = setup();
  const result = await grouped.invoke({ offerId: null, draft: draft({ offer_price: '$1,234,567.80' }) });
  assert.equal(result.status, 201);
  const groupedWrite = grouped.calls.find(({ options }) => options.method === 'POST');
  assert.equal(JSON.parse(groupedWrite.options.body).offer_price, 1234567.8);

  const nested = setup();
  const nestedResult = await nested.invoke({ offerId: null, draft: draft({
    offer_price: 1234.5, offer_data: { price: '$1,234.50', offerPrice: '1,234.50' }
  }) });
  assert.equal(nestedResult.status, 201);
  const nestedWrite = nested.calls.find(({ options }) => options.method === 'POST');
  const nestedSaved = JSON.parse(nestedWrite.options.body);
  assert.equal(nestedSaved.offer_price, 1234.5);
  assert.equal(nestedSaved.offer_data.price, 1234.5);
  assert.equal(nestedSaved.offer_data.offerPrice, 1234.5);

  const nestedOnly = setup();
  const nestedOnlyResult = await nestedOnly.invoke({ offerId: null, draft: (() => {
    const value = draft({ offer_data: { price: '$2,345.67' } });
    delete value.offer_price;
    return value;
  })() });
  assert.equal(nestedOnlyResult.status, 201);
  const nestedOnlyWrite = nestedOnly.calls.find(({ options }) => options.method === 'POST');
  const nestedOnlySaved = JSON.parse(nestedOnlyWrite.options.body);
  assert.equal(nestedOnlySaved.offer_price, 2345.67);
  assert.equal(nestedOnlySaved.offer_data.price, 2345.67);

  const empty = setup();
  const emptyResult = await empty.invoke({ offerId: null, draft: draft({ offer_price: '' }) });
  assert.equal(emptyResult.status, 201);
  const emptyWrite = empty.calls.find(({ options }) => options.method === 'POST');
  assert.equal(JSON.parse(emptyWrite.options.body).offer_price, null);
});

test('native quick drafts accept and persist an optional co-buyer name', async () => {
  const { calls, invoke } = setup();
  const result = await invoke({ offerId: null, draft: draft({ buyer2_name: 'QA Co-buyer' }) });
  assert.equal(result.status, 201);
  const insert = calls.find(({ options }) => options.method === 'POST');
  const body = JSON.parse(insert.options.body);
  assert.equal(body.buyer2_name, 'QA Co-buyer');
  assert.equal(body.offer_data.buyer2, 'QA Co-buyer');
  assert.equal(body.offer_data.buyer2Name, 'QA Co-buyer');
});

test('overlong buyer names fail validation before reading or writing the offer row', async () => {
  assert.equal(MAX_BUYER_NAME_LENGTH, 180);
  const { calls, invoke } = setup();
  const result = await invoke({ offerId: null, draft: draft({ buyer_name: 'A'.repeat(181) }) });
  assert.equal(result.status, 422);
  assert.equal(result.result.code, 'invalid_draft');
  assert.match(result.result.error, /180 characters or fewer/);
  assert.equal(calls.some(({ url }) => url.includes('/rest/v1/hof_offers')), false);
  assert.equal(calls.some(({ options }) => ['POST', 'PATCH'].includes(options.method)), false);
});

test('overlong co-buyer names fail validation before reading or writing the offer row', async () => {
  const { calls, invoke } = setup();
  const result = await invoke({ offerId: null, draft: draft({ buyer2_name: 'B'.repeat(181) }) });
  assert.equal(result.status, 422);
  assert.equal(result.result.code, 'invalid_draft');
  assert.match(result.result.error, /co-buyer name to 180 characters or fewer/);
  assert.equal(calls.some(({ url }) => url.includes('/rest/v1/hof_offers')), false);
  assert.equal(calls.some(({ options }) => ['POST', 'PATCH'].includes(options.method)), false);
});

test('native create retries return the previously saved draft without inserting another', async () => {
  const requestId = '44444444-4444-4444-8444-444444444444';
  const { calls, invoke } = setup({ idempotentRows: [{ id: offerId, status: 'Draft', last_updated: '2026-10-23T10:05:00.000Z', buyer_name: 'QA Buyer', offer_price: 400000 }] });
  const result = await invoke({ offerId: null, clientRequestId: requestId, draft: draft() });
  assert.equal(result.status, 200);
  assert.equal(result.result.recovered, true);
  assert.equal(result.result.draft.id, offerId);
  assert.deepEqual(Object.keys(result.result.draft).sort(), ['id', 'last_updated', 'status']);
  assert.equal(calls.some(({ options }) => options.method === 'POST'), false);
  const lookup = calls.find(({ url }) => new URL(url).searchParams.has('offer_data->>_hof_native_draft_request_id'));
  assert.match(new URL(lookup.url).searchParams.get('user_id'), new RegExp(`^eq\\.${ownerId}$`));
  assert.equal(new URL(lookup.url).searchParams.get('offer_data->>_hof_native_draft_request_id'), `eq.${requestId}`);
});

test('reusing a native request key with changed draft details requires review instead of creating a duplicate', async () => {
  const requestId = '44444444-4444-4444-8444-444444444444';
  const { calls, invoke } = setup({ idempotentRows: [{ id: offerId, status: 'Draft', buyer_name: 'Earlier Buyer', offer_price: 400000 }] });
  const result = await invoke({ offerId: null, clientRequestId: requestId, draft: draft({ buyer_name: 'Changed Buyer' }) });
  assert.equal(result.status, 409);
  assert.equal(result.result.code, 'draft_request_conflict');
  assert.match(result.result.error, /Refresh your offers and review it/);
  assert.equal(calls.some(({ options }) => options.method === 'POST'), false);
});

test('reusing a native request key with a changed co-buyer requires review', async () => {
  const requestId = '44444444-4444-4444-8444-444444444444';
  const { calls, invoke } = setup({ idempotentRows: [{
    id: offerId, status: 'Draft', buyer_name: 'QA Buyer', buyer2_name: 'Earlier Co-buyer', offer_price: 400000
  }] });
  const result = await invoke({ offerId: null, clientRequestId: requestId, draft: draft({ buyer2_name: 'Changed Co-buyer' }) });
  assert.equal(result.status, 409);
  assert.equal(result.result.code, 'draft_request_conflict');
  assert.equal(calls.some(({ options }) => options.method === 'POST'), false);
});

test('native create stores the request key privately for a later lost-response retry', async () => {
  const requestId = '44444444-4444-4444-8444-444444444444';
  const { calls, invoke } = setup();
  const result = await invoke({ offerId: null, clientRequestId: requestId, draft: draft() });
  assert.equal(result.status, 201);
  const insert = calls.find(({ options }) => options.method === 'POST');
  assert.equal(JSON.parse(insert.options.body).offer_data._hof_native_draft_request_id, requestId);
});

test('concurrent native creates with the same request key recover through the offer primary key', async () => {
  const requestId = '44444444-4444-4444-8444-444444444444';
  const { calls, offers, invoke } = concurrentNativeCreateSetup();
  const body = { offerId: null, clientRequestId: requestId, draft: draft() };
  const [first, second] = await Promise.all([invoke(body), invoke(body)]);

  assert.deepEqual([first.status, second.status].sort(), [200, 201]);
  assert.equal(offers.size, 1);
  assert.equal(offers.get(requestId).id, requestId);
  assert.equal(offers.get(requestId).offer_data._hof_native_draft_request_id, requestId);
  assert.equal(calls.filter(({ options }) => options.method === 'POST').length, 2);
  const recovered = [first, second].find(result => result.status === 200);
  assert.equal(recovered.result.recovered, true);
  assert.equal(recovered.result.draft.id, requestId);
});

test('concurrent native creates with changed details return a review conflict', async () => {
  const requestId = '44444444-4444-4444-8444-444444444444';
  const { offers, invoke } = concurrentNativeCreateSetup();
  const [first, second] = await Promise.all([
    invoke({ offerId: null, clientRequestId: requestId, draft: draft() }),
    invoke({ offerId: null, clientRequestId: requestId, draft: draft({ buyer_name: 'Changed Buyer' }) })
  ]);

  assert.deepEqual([first.status, second.status].sort(), [201, 409]);
  assert.equal(offers.size, 1);
  const conflict = [first, second].find(result => result.status === 409);
  assert.equal(conflict.result.code, 'draft_request_conflict');
  assert.match(conflict.result.error, /Refresh your offers and review it/);
});

test('concurrent native creates with a changed co-buyer return a review conflict', async () => {
  const requestId = '44444444-4444-4444-8444-444444444444';
  const { offers, invoke } = concurrentNativeCreateSetup();
  const [first, second] = await Promise.all([
    invoke({ offerId: null, clientRequestId: requestId, draft: draft({ buyer2_name: 'First Co-buyer' }) }),
    invoke({ offerId: null, clientRequestId: requestId, draft: draft({ buyer2_name: 'Second Co-buyer' }) })
  ]);

  assert.deepEqual([first.status, second.status].sort(), [201, 409]);
  assert.equal(offers.size, 1);
  const conflict = [first, second].find(result => result.status === 409);
  assert.equal(conflict.result.code, 'draft_request_conflict');
});

test('native create rejects malformed retry keys before a write', async () => {
  const { calls, invoke } = setup();
  const result = await invoke({ offerId: null, clientRequestId: 'not-a-uuid', draft: draft() });
  assert.equal(result.status, 400);
  assert.equal(calls.some(({ options }) => options.method === 'POST'), false);
});

test('accounts without agent-capable profiles cannot write offer drafts', async () => {
  const { calls, invoke } = setup({ profileRole: 'homebuyer' });
  const result = await invoke({ offerId: null, draft: draft() });
  assert.equal(result.status, 403);
  assert.equal(calls.some(({ options }) => ['POST', 'PATCH'].includes(options.method)), false);
});

test('draft role comes from the verified profile, not the request', async () => {
  const { calls, invoke } = setup({ profileRole: 'investor' });
  const result = await invoke({ offerId: null, draft: draft({ role: 'brokerage_admin' }) });
  assert.equal(result.status, 201);
  const insert = calls.find(({ options }) => options.method === 'POST');
  assert.equal(JSON.parse(insert.options.body).role, 'investor');
});

test('updates are scoped to the verified owner and never write packet status', async () => {
  const { calls, invoke } = setup();
  const result = await invoke({ offerId, draft: draft() });
  assert.equal(result.status, 200);
  const read = calls.find(({ url, options }) => url.includes('/rest/v1/hof_offers') && !options.method);
  assert.match(read.url, new RegExp(`id=eq\\.${offerId}`));
  assert.match(read.url, new RegExp(`user_id=eq\\.${ownerId}`));
  const patch = calls.find(({ options }) => options.method === 'PATCH');
  const body = JSON.parse(patch.options.body);
  assert.equal(body.user_id, ownerId);
  assert.equal(body.status, undefined);
  assert.equal(body.signwell_document_id, undefined);
  assert.equal(body.offer_data._hof_native_draft_request_id, undefined);
  assert.match(patch.url, /last_updated=eq\./);
  const filters = new URL(patch.url).searchParams;
  assert.equal(filters.get('status'), 'eq.Draft');
  assert.equal(filters.get('generated_at'), 'is.null');
  assert.equal(filters.get('signwell_document_id'), 'is.null');
});

test('native buyer and price edits update interview answers without replacing other draft details', async () => {
  const current = {
    id: offerId, user_id: ownerId, status: 'Draft', last_updated: '2026-10-23T10:00:00.000Z',
    offer_data: { buyer1: 'Earlier Primary', buyer2: 'Earlier Buyer', buyer2Name: 'Earlier Buyer',
      buyer2Email: 'second@example.com', repairsText: 'Keep this detail', price: 395000, offer_price: 395000 }
  };
  const { calls, invoke } = setup({ current });
  const result = await invoke({ offerId, draft: { buyer_name: 'QA Buyer', buyer2_name: 'Updated Co-buyer', offer_price: 400000 } });
  assert.equal(result.status, 200);
  const patch = calls.find(({ options }) => options.method === 'PATCH');
  const saved = JSON.parse(patch.options.body);
  assert.equal(saved.buyer2_name, 'Updated Co-buyer');
  assert.deepEqual(saved.offer_data, {
    buyer1: 'QA Buyer', buyer2: 'Updated Co-buyer', buyer2Name: 'Updated Co-buyer',
    buyer2Email: 'second@example.com', repairsText: 'Keep this detail', price: 400000, offerPrice: 400000
  });
});

test('clearing an optional co-buyer removes only its name aliases from offer data', async () => {
  const current = {
    id: offerId, user_id: ownerId, status: 'Draft', last_updated: '2026-10-23T10:00:00.000Z',
    offer_data: { buyer2: 'Earlier Buyer', buyer2Name: 'Earlier Buyer', buyer2Email: 'second@example.com', repairsText: 'Keep this detail' }
  };
  const { calls, invoke } = setup({ current });
  const result = await invoke({ offerId, draft: { buyer_name: 'QA Buyer', buyer2_name: '', offer_price: null } });
  assert.equal(result.status, 200);
  const patch = calls.find(({ options }) => options.method === 'PATCH');
  const saved = JSON.parse(patch.options.body);
  assert.equal(saved.buyer2_name, '');
  assert.equal(saved.buyer2_email, null);
  assert.deepEqual(saved.offer_data, { repairsText: 'Keep this detail', buyer1: 'QA Buyer', price: null, offerPrice: null });
});

test('native update rejects a draft version that changed after the form opened', async () => {
  const { calls, invoke } = setup({ current: { id: offerId, user_id: ownerId, status: 'Draft', last_updated: '2026-10-23T10:05:00.000Z', offer_data: {} } });
  const result = await invoke({ offerId, expectedLastUpdated: '2026-10-23T10:00:00.000Z', draft: draft() });
  assert.equal(result.status, 409);
  assert.equal(result.result.code, 'offer_draft_conflict');
  assert.match(result.result.error, /Your changes were not saved/);
  assert.equal(calls.some(({ options }) => options.method === 'PATCH'), false);
});

test('native update accepts the captured null version only while the row is still null', async () => {
  const current = { id: offerId, user_id: ownerId, status: 'Draft', last_updated: null, offer_data: {} };
  const { calls, invoke } = setup({ current });
  const result = await invoke({ offerId, expectedLastUpdated: null, draft: draft() });
  assert.equal(result.status, 200);
  assert.ok(calls.some(({ options }) => options.method === 'PATCH'));
});

test('invalid native draft versions are rejected before an offer lookup or write', async () => {
  const { calls, invoke } = setup();
  const result = await invoke({ offerId, expectedLastUpdated: { timestamp: 'forged' }, draft: draft() });
  assert.equal(result.status, 400);
  assert.equal(calls.some(({ url }) => url.includes('/rest/v1/hof_offers')), false);
});

test('prepared packets cannot be edited in place', async () => {
  const { calls, invoke } = setup({ current: { id: offerId, user_id: ownerId, status: 'Buyer Signed', last_updated: 'v1', offer_data: {} } });
  const result = await invoke({ offerId, draft: draft() });
  assert.equal(result.status, 409);
  assert.equal(result.result.code, 'offer_prepared');
  assert.equal(calls.some(({ options }) => options.method === 'PATCH'), false);
});

test('optimistic write races return a retryable conflict', async () => {
  const { invoke } = setup({ patchRows: [] });
  const result = await invoke({ offerId, draft: draft() });
  assert.equal(result.status, 409);
  assert.equal(result.result.code, 'offer_draft_conflict');
  assert.match(result.result.error, /changed while you were editing/);
});

test('missing, empty, and oversized draft requests fail before storage writes', async () => {
  const noDraft = setup();
  assert.equal((await noDraft.invoke({ offerId: null })).status, 400);
  const empty = setup();
  const emptyResult = await empty.invoke({ offerId: null, draft: draft({ property_address: 'Untitled offer', buyer_name: 'Unnamed buyer', offer_price: null }) });
  assert.equal(emptyResult.status, 422);
  const incomplete = setup();
  const incompleteResult = await incomplete.invoke({ offerId: null, draft: {} });
  assert.equal(incompleteResult.status, 422);
  assert.equal(incomplete.calls.some(({ options }) => options.method === 'POST'), false);
  const large = setup();
  const largeResult = await large.invoke('x'.repeat(4 * 1024 * 1024 + 1));
  assert.equal(largeResult.status, 413);
  assert.equal(large.calls.length, 0);
});

test('drafts with a buyer but no property can continue into the web address interview', async () => {
  const { calls, invoke } = setup();
  const result = await invoke({ offerId: null, draft: { buyer_name: 'QA Buyer' } });
  assert.equal(result.status, 201);
  const insert = calls.find(({ options }) => options.method === 'POST');
  assert.equal(JSON.parse(insert.options.body).buyer_name, 'QA Buyer');
  assert.equal(JSON.parse(insert.options.body).property_address, undefined);
});
