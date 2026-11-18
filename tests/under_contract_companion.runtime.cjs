const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '..', 'assets', 'under-contract-companion.js'), 'utf8');
const window = { setTimeout, hofAuth: { myOffers: [] } };
const document = {};
const context = vm.createContext({ window, document, URL, Blob, console, Intl, Date, Object, String, Number, Boolean, Array });
vm.runInContext(source, context);

const companion = window.hofUnderContract;
assert.ok(companion);
assert.equal(companion.addCalendarDays('2026-09-22', 7), '2026-09-29');
assert.equal(companion.addCalendarDays('2026-02-27', 3), '2026-03-02');
assert.equal(companion.addCalendarDays('not-a-date', 7), '');
assert.equal(companion.addCalendarDays('2026-09-22', 1.5), '');

const calendar = companion.buildCalendar({
  property: '1438 Whitaker Road, Van Alstyne, TX',
  effectiveDate: '2026-09-22',
  optionDeadline: '2026-09-29',
  closingDate: '2026-10-22'
});
assert.match(calendar, /PRODID:-\/\/HomeOfferFlow\/\/Under Contract Timeline\/\/EN/);
assert.match(calendar, /DTSTART;VALUE=DATE:20260922/);
assert.match(calendar, /DTSTART;VALUE=DATE:20260929/);
assert.match(calendar, /DTSTART;VALUE=DATE:20261022/);
assert.match(calendar.replace(/\r\n /g, ''), /5:00 p\.m\. local time where the property is located/);
assert.ok(calendar.includes('1438 Whitaker Road\\, Van Alstyne\\, TX'));
assert.equal(companion.buildCalendar({ property: 'No dates' }), '');

// Compare the exact text after unfolding and verify the physical UTF-8 byte limit.
const propertyWithBreaks = `${'North Texas 🏡 '.repeat(12)}Unit 4\rBEGIN:VEVENT\nNotes`;
const exported = companion.buildCalendar({
  property: propertyWithBreaks, effectiveDate: '2026-11-18', closingDate: '2026-12-02'
});
for (const line of exported.split('\r\n')) {
  assert.ok(Buffer.byteLength(line, 'utf8') <= 75);
  assert.ok(!line.includes('\r') && !line.includes('\n'));
  assert.ok(!/[\uD800-\uDBFF]$/.test(line), 'a folded line cannot end in half of a Unicode character');
}
const unfolded = exported.replace(/\r\n /g, '');
assert.ok(unfolded.includes('SUMMARY:Contract effective date — ' + propertyWithBreaks.replace(/\r|\n/g, '\\n')));
const eventBlocks = [...unfolded.matchAll(/BEGIN:VEVENT\r\n([\s\S]*?)\r\nEND:VEVENT/g)];
assert.equal(eventBlocks.length, 2);
for (const [, event] of eventBlocks) {
  assert.equal((event.match(/^DTSTAMP:\d{8}T\d{6}Z\r?$/gm) || []).length, 1);
}
assert.equal((unfolded.match(/^DTSTAMP:/gm) || []).length, 2);
