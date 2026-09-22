const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const match = html.match(/<script id="hof-customer-action-error-v1">([\s\S]*?)<\/script>/);
if (!match) throw new Error('Customer action error filter was not found');

const window = {};
vm.runInNewContext(match[1], { window });

function status(message, interactive = false) {
  return {
    textContent: message,
    querySelector: () => interactive ? {} : null,
  };
}

test('keeps short customer instructions but rejects technical details', () => {
  const fallback = 'Please try again.';
  assert.equal(window.hofCustomerActionError(new Error('Please enter the property address.'), fallback), 'Please enter the property address.');
  assert.equal(window.hofCustomerActionError(new Error('Please retry: database column is missing.'), fallback), fallback);
  assert.equal(window.hofCustomerActionError(new Error('Postgres constraint violation'), fallback), fallback);
});

test('sanitizes visible error regions without removing interactive recovery controls', () => {
  const technical = status('Supabase database constraint violation');
  const actionable = status('Please choose at least one recipient.');
  const interactive = status('Database error', true);
  const root = { querySelectorAll: () => [technical, actionable, interactive] };

  window.hofSanitizeVisibleErrors(root);

  assert.equal(technical.textContent, 'We couldn’t complete that action. Please try again.');
  assert.equal(actionable.textContent, 'Please choose at least one recipient.');
  assert.equal(interactive.textContent, 'Database error');
});
