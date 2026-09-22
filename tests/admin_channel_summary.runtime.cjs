const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const page = fs.readFileSync(path.resolve(__dirname, '..', 'index.html'), 'utf8');
const start = page.indexOf('  function adminSafe(');
const end = page.indexOf('  // Event metadata is inserted', start);
assert.notEqual(start, -1);
assert.notEqual(end, -1);
const helpers = page.slice(start, end);

function summarize(views, actions, fallback) {
  const context = {
    escapeAttr(value) {
      return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    },
  };
  vm.runInNewContext(helpers, context);
  return context.adminChannelStageSummary(views, actions, fallback);
}

test('shows every observed acquisition channel and its stage counts', () => {
  assert.equal(
    summarize(
      { direct: 7, homepage: 3, organic: 2, email: 0 },
      { direct: 2, homepage: 1, organic: 1, email: 0 },
    ),
    'direct 7 / 2 · homepage 3 / 1 · organic 2 / 1',
  );
});

test('uses a quiet fallback until attributed traffic arrives', () => {
  assert.equal(summarize({}, {}, 'waiting for visits'), 'waiting for visits');
});

test('escapes unexpected channel labels before rendering', () => {
  assert.equal(summarize({ '<script>': 1 }, {}), '&lt;script&gt; 1 / 0');
});
