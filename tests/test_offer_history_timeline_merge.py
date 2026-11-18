from pathlib import Path
import subprocess
import unittest


class OfferHistoryTimelineMergeTests(unittest.TestCase):
    def test_history_retains_only_a_newer_timeline_saved_during_the_request(self):
        html = (Path(__file__).resolve().parents[1] / "index.html").read_text()
        start = html.index("  function keepTimelineSavedDuringHistory(")
        end = html.index("  async function loadMyOffers(", start)
        program = "const assert = require('node:assert/strict');\n" + html[start:end] + """
const timeline = (updatedAt, closingDate) => ({updatedAt, closingDate});
const offer = (tracking, status) => ({id:'fixture', status, offer_data:{
  optionDays:7, transactionTracking:tracking
}});
const previous = timeline('2026-11-18T11:00:00.100000+00:00', '2026-12-01');
const saved = timeline('2026-11-18T11:00:00.100400+00:00', '2026-12-06');
const older = timeline('2026-11-18T05:00:00.100125-06:00', '2026-12-03');
const newer = timeline('2026-11-18T11:00:00.100800Z', '2026-12-07');
const fresh = offer(saved, 'Generated');
for (const incoming of [undefined, older]) {
  assert.deepEqual(keepTimelineSavedDuringHistory(offer(incoming, 'Signed'), fresh, previous.updatedAt),
    offer(saved, 'Signed'));
}
const server = offer(newer, 'Signed');
assert.equal(keepTimelineSavedDuringHistory(server, fresh, previous.updatedAt), server);
const removed = offer(undefined, 'Signed');
assert.equal(keepTimelineSavedDuringHistory(removed, fresh, saved.updatedAt), removed);
const malformed = offer(timeline('unknown', '2026-12-08'), 'Signed');
assert.equal(keepTimelineSavedDuringHistory(server, malformed, previous.updatedAt), server);
"""
        completed = subprocess.run(["node", "-"], input=program, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
