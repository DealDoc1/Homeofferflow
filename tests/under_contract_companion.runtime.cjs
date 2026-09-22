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
assert.match(calendar, /5:00 p\.m\. local time where the property is located/);
assert.ok(calendar.includes('1438 Whitaker Road\\, Van Alstyne\\, TX'));
assert.equal(companion.buildCalendar({ property: 'No dates' }), '');
