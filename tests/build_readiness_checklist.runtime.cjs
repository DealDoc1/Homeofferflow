const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('assets/build-readiness-checklist.js', 'utf8');
const keys = ['discovery', 'readiness', 'financing', 'land', 'builder', 'transition', 'movein'];

function environment(initial = '{}', storageThrows = false) {
  const values = new Map([['hof:build-readiness-checklist:v1', initial]]);
  const boxes = keys.map(key => ({
    dataset: { buildReadinessTask: key }, checked: false, disabled: false, handlers: {},
    addEventListener(name, fn) { this.handlers[name] = fn; },
  }));
  const progress = { textContent: '' };
  const message = { textContent: '' };
  const buttons = { buildReadinessClear: { handlers: {}, addEventListener(name, fn) { this.handlers[name] = fn; } },
    buildReadinessPrint: { handlers: {}, addEventListener(name, fn) { this.handlers[name] = fn; } } };
  let printCount = 0;
  const localStorage = {
    getItem(key) { if (storageThrows) throw Error('blocked'); return values.get(key) || null; },
    setItem(key, value) { if (storageThrows) throw Error('blocked'); values.set(key, value); },
    removeItem(key) { if (storageThrows) throw Error('blocked'); values.delete(key); },
  };
  const root = {
    document: {
      querySelectorAll() { return boxes; },
      getElementById(id) { return id === 'buildReadinessProgress' ? progress : id === 'buildReadinessChecklistStatus' ? message : buttons[id]; },
    },
    localStorage,
    print() { printCount += 1; },
  };
  vm.runInNewContext(source, { window: root });
  return { boxes, progress, message, buttons, values, get printCount() { return printCount; } };
}

const stored = environment(JSON.stringify({ discovery: true, builder: true, forged: true, land: 1 }));
assert.equal(stored.boxes.filter(box => box.checked).length, 2, 'restores only known true checkmarks');
assert.equal(stored.progress.textContent, '2 of 7 steps marked');
stored.boxes[2].checked = true;
stored.boxes[2].handlers.change();
assert.deepEqual(JSON.parse(stored.values.get('hof:build-readiness-checklist:v1')), { discovery: true, builder: true, financing: true });
stored.buttons.buildReadinessPrint.handlers.click();
assert.equal(stored.printCount, 1);
stored.buttons.buildReadinessClear.handlers.click();
assert.equal(stored.progress.textContent, '0 of 7 steps marked');
assert.equal(stored.values.has('hof:build-readiness-checklist:v1'), false);

const blocked = environment('{}', true);
blocked.boxes[0].checked = true;
blocked.boxes[0].handlers.change();
assert.equal(blocked.progress.textContent, '1 of 7 steps marked');
assert.match(blocked.message.textContent, /could not be saved/);
blocked.buttons.buildReadinessClear.handlers.click();
assert.equal(blocked.progress.textContent, '0 of 7 steps marked');
assert.match(blocked.message.textContent, /could not be removed/);

console.log('Build Readiness checklist runtime: 10 assertions passed');
