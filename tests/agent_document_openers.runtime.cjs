const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const script = html.match(/<script id="hof-purchase-addendum-interview-openers-v1">([\s\S]*?)<\/script>/)[1];

function runtime(cardId, readyAfter = 0) {
  const calls = [];
  const timers = [];
  let elapsed = 0;
  const window = {
    setTimeout(callback, delay) { timers.push({ callback, delay }); },
  };
  const document = {
    querySelector(selector) {
      if (selector !== `#${cardId} button` || elapsed < readyAfter) return null;
      return { click() { calls.push(cardId); } };
    },
  };
  vm.runInNewContext(script, { window, document });
  return {
    window,
    calls,
    flush() {
      let steps = 0;
      while (timers.length) {
        assert.ok(++steps < 150, 'Document loading must stop retrying.');
        const timer = timers.shift();
        elapsed += timer.delay;
        timer.callback();
      }
    },
  };
}

for (const [form, card] of [
  ['1506', 'txr1506AgreementCard'],
  ['1508', 'txr1508AgreementCard'],
]) {
  test(`Guided TXR-${form} choice opens its existing form exactly once`, async () => {
    const page = runtime(card);
    assert.equal(typeof page.window[`hofOpenTxr${form}Draft`], 'function');
    await page.window[`hofOpenTxr${form}Draft`]();
    assert.deepEqual(page.calls, [card]);
  });
}

test('Guided form waits for a source card that loads after two seconds', async () => {
  const page = runtime('txr1508AgreementCard', 2000);
  const result = page.window.hofOpenTxr1508Draft();
  page.flush();
  await result;
  assert.deepEqual(page.calls, ['txr1508AgreementCard']);
});

test('A missing form stops waiting and reports failure without opening a different form', async () => {
  const page = runtime('txr1506AgreementCard', Infinity);
  const result = page.window.hofOpenTxr1508Draft();
  const rejection = assert.rejects(result, /TXR-1508/);
  page.flush();
  await rejection;
  assert.deepEqual(page.calls, []);
});
