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
assert.deepEqual(
  JSON.parse(JSON.stringify(companion.normalizeMilestones([
    { label: '  Survey delivery  ', date: '2026-10-01' },
    { label: '', date: '' },
  ]))),
  [{ label: 'Survey delivery', date: '2026-10-01' }]
);
assert.throws(() => companion.normalizeMilestones([{ label: 'Survey', date: '' }]), /enter a short name and the date/);
assert.throws(() => companion.normalizeMilestones([
  { label: 'Survey delivery', date: '2026-10-01' },
  { label: '  SURVEY   DELIVERY ', date: '2026-10-01' }
], { rejectDuplicates: true }), /Enter each confirmed date once/);
assert.equal(companion.normalizeMilestones([
  { label: 'Survey delivery', date: '2026-10-01' },
  { label: 'Survey delivery - amended', date: '2026-10-03' }
], { rejectDuplicates: true }).length, 2);
assert.equal(companion.normalizeMilestones([
  { label: 'Survey delivery', date: '2026-10-01' },
  { label: 'Survey delivery', date: '2026-10-01' }
]).length, 2, 'saved legacy milestones remain readable until corrected');
assert.throws(() => companion.normalizeMilestones(Array.from({ length: 13 }, (_, index) => ({ label: `Date ${index}`, date: '2026-10-01' }))), /no more than 12/);

const calendar = companion.buildCalendar({
  property: '1438 Whitaker Road, Van Alstyne, TX',
  effectiveDate: '2026-09-22',
  optionDeadline: '2026-09-29',
  closingDate: '2026-10-22',
  milestones: [{ label: 'Survey delivery', date: '2026-10-01' }]
});
const unfoldedBasicCalendar = calendar.replace(/\r\n /g, '');
assert.match(calendar, /PRODID:-\/\/HomeOfferFlow\/\/Under Contract Timeline\/\/EN/);
assert.match(calendar, /DTSTART;VALUE=DATE:20260922/);
assert.match(calendar, /DTSTART;VALUE=DATE:20260929/);
assert.match(calendar, /DTSTART;VALUE=DATE:20261022/);
assert.ok(calendar.includes('SUMMARY:Survey delivery — 1438 Whitaker Road\\, Van Alstyne\\, TX'));
assert.match(unfoldedBasicCalendar, /Date entered by the agent from the fully signed contract or a written amendment/);
assert.match(unfoldedBasicCalendar, /5:00 p\.m\. local time where the property is located/);
assert.ok(calendar.includes('1438 Whitaker Road\\, Van Alstyne\\, TX'));
assert.equal(companion.buildCalendar({ property: 'No dates' }), '');

const longUnicodeCalendar = companion.buildCalendar({
  property: `${'North Texas 🏡 '.repeat(12)}\rClient\nProperty`,
  effectiveDate: '2026-10-01',
  milestones: [{ label: `${'Inspection and repair milestone 🛠️ '.repeat(2)}`, date: '2026-10-04' }]
});
for (const physicalLine of longUnicodeCalendar.split('\r\n')) {
  assert.ok(Buffer.byteLength(physicalLine, 'utf8') <= 75, `calendar line exceeds 75 octets: ${physicalLine}`);
}
const unfoldedCalendar = longUnicodeCalendar.replace(/\r\n /g, '');
assert.ok(unfoldedCalendar.includes('SUMMARY:Contract effective date — North Texas 🏡'));
assert.ok(unfoldedCalendar.includes('Client\\nProperty'));
assert.ok(unfoldedCalendar.includes('Inspection and repair milestone 🛠️'));
assert.equal((longUnicodeCalendar.match(/BEGIN:VEVENT/g) || []).length, 2, 'user-entered newlines cannot inject calendar events');

const eventIds = value => value.replace(/\r\n /g, '').match(/^UID:.+$/gm);
const sameDay = {effectiveDate:'2026-10-01',closingDate:'2026-10-01',
  milestones:[{label:'Survey delivery',date:'2026-10-01'}]};
const offerA = eventIds(companion.buildCalendar({...sameDay,offerId:'fictional-a'}));
const offerB = eventIds(companion.buildCalendar({...sameDay,offerId:'fictional-b'}));
assert.deepEqual(offerA, [
  'UID:homeofferflow-20261001-1@homeofferflow.com',
  'UID:homeofferflow-20261001-2@homeofferflow.com',
  'UID:homeofferflow-fictional-a-milestone-1@homeofferflow.com'
]);
assert.deepEqual(offerA.slice(0,2), offerB.slice(0,2));
assert.notEqual(offerA[2], offerB[2]);

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
