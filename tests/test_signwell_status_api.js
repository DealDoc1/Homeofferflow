const assert = require('node:assert/strict');
const test = require('node:test');
const path = require('node:path');

process.env.SUPABASE_URL = 'https://example.supabase.co';
process.env.SUPABASE_SERVICE_ROLE_KEY = 'service-role-test-key';
process.env.SIGNWELL_API_KEY = 'signwell-test-key';
process.env.ADMIN_EMAILS = 'platform-admin@example.com';

const handler = require(path.join(__dirname, '..', 'api', 'signwell-status.js'));

function responseRecorder() {
  const result = { statusCode: null, body: null };
  return {
    result,
    status(statusCode) {
      result.statusCode = statusCode;
      return this;
    },
    json(body) {
      result.body = body;
    }
  };
}

function jsonResponse(status, body) {
  const text = JSON.stringify(body);
  return {
    ok: status >= 200 && status < 300,
    status,
    async text() {
      return text;
    },
    async json() {
      return body;
    }
  };
}

function refreshRequest(body, token = 'valid-token') {
  return {
    method: 'POST',
    headers: token ? { authorization: `Bearer ${token}` } : {},
    body: JSON.stringify(body)
  };
}

test('requires a signed-in session before any offer or SignWell lookup', async () => {
  const originalFetch = global.fetch;
  const originalConsoleError = console.error;
  let calls = 0;
  console.error = () => {};
  global.fetch = async () => {
    calls += 1;
    throw new Error('Fetch should not run without an access token.');
  };

  try {
    const res = responseRecorder();
    await handler(refreshRequest({ offerId: 'offer-1' }, ''), res);
    assert.equal(res.result.statusCode, 401);
    assert.equal(res.result.body.error, 'Please sign in before refreshing SignWell status.');
    assert.equal(calls, 0);
  } finally {
    global.fetch = originalFetch;
    console.error = originalConsoleError;
  }
});

test('limits a non-admin refresh lookup to that user and saves the normalized status', async () => {
  const originalFetch = global.fetch;
  const urls = [];
  const offer = {
    id: 'offer-1',
    user_id: 'user-1',
    offer_data: JSON.stringify({ propertyAddress: '123 Test Street' }),
    signwell_document_id: 'doc-1',
    status: 'Generated'
  };

  global.fetch = async (url, options = {}) => {
    const target = String(url);
    urls.push(target);

    if (target.endsWith('/auth/v1/user')) {
      return jsonResponse(200, { id: 'user-1', email: 'agent@example.com' });
    }
    if (target.includes('/rest/v1/hof_offers?') && options.method === 'GET') {
      assert.match(target, /id=eq\.offer-1/);
      assert.match(target, /user_id=eq\.user-1/);
      return jsonResponse(200, [offer]);
    }
    if (target.endsWith('/api/v1/documents/doc-1')) {
      assert.equal(options.headers['X-Api-Key'], 'signwell-test-key');
      return jsonResponse(200, {
        status: 'completed',
        recipients: [{ name: 'Test Buyer', email: 'buyer@example.com', status: 'completed' }]
      });
    }
    if (target.includes('/rest/v1/hof_offers?id=eq.offer-1') && options.method === 'PATCH') {
      const patch = JSON.parse(options.body);
      assert.equal(patch.status, 'Signed');
      assert.equal(patch.signwell_status, 'Buyer Signatures Complete');
      return jsonResponse(200, [{ id: 'offer-1', status: 'Signed' }]);
    }
    if (target.endsWith('/rest/v1/hof_offer_events')) {
      const event = JSON.parse(options.body);
      assert.equal(event.user_id, 'user-1');
      assert.equal(event.status, 'Buyer Signatures Complete');
      return jsonResponse(201, {});
    }
    throw new Error(`Unexpected request: ${target}`);
  };

  try {
    const res = responseRecorder();
    await handler(refreshRequest({ offerId: 'offer-1' }), res);
    assert.equal(res.result.statusCode, 200);
    assert.equal(res.result.body.status, 'Buyer Signatures Complete');
    assert.equal(res.result.body.updatedOffer.status, 'Signed');
    assert.equal(urls.filter((url) => url.includes('api/v1/documents/doc-1')).length, 1);
  } finally {
    global.fetch = originalFetch;
  }
});

test('returns a safe error when SignWell is unavailable without exposing provider details', async () => {
  const originalFetch = global.fetch;
  const originalConsoleError = console.error;
  console.error = () => {};
  global.fetch = async (url) => {
    const target = String(url);
    if (target.endsWith('/auth/v1/user')) {
      return jsonResponse(200, { id: 'user-1', email: 'agent@example.com' });
    }
    if (target.includes('/rest/v1/hof_offers?')) {
      return jsonResponse(200, [{ id: 'offer-1', user_id: 'user-1', offer_data: {}, signwell_document_id: 'doc-1' }]);
    }
    if (target.endsWith('/api/v1/documents/doc-1')) {
      return jsonResponse(500, { error: 'provider diagnostic: do not reveal this' });
    }
    throw new Error(`Unexpected request: ${target}`);
  };

  try {
    const res = responseRecorder();
    await handler(refreshRequest({ offerId: 'offer-1' }), res);
    assert.equal(res.result.statusCode, 502);
    assert.equal(res.result.body.error, 'Could not retrieve the latest SignWell status. Please try again.');
    assert.doesNotMatch(res.result.body.error, /provider diagnostic/i);
  } finally {
    global.fetch = originalFetch;
    console.error = originalConsoleError;
  }
});
