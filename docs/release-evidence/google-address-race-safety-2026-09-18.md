# Google address search reliability - September 18

## Status

Implemented and runtime-tested locally. Not pushed, deployed, or verified in a
real browser against live Google Places. No Vercel build or preview was started.
Runtime tests stub the provider and deliberately resolve requests out of order;
they do not send addresses to Google or incur Places requests.

## Customer problem reproduced

The shared address picker accepted every completed prediction request without
checking whether the input had changed, lost focus, or been removed. An older
response could replace newer suggestions, reopen a dismissed list, or close a
newer list on failure. A delayed Place Details response could overwrite a
customer's subsequent manual correction, including on its error path.

The picker also sent input events for its own selections through its search
listener, starting redundant autocomplete requests. A global session token was
shared by independent address fields. Finally, each wired field installed a
document click listener retaining that field; another field's listener could
dismiss the active input's suggestions.

## Changes

- Capture text and input revision immediately on each edit, before debouncing.
- Accept suggestions only for the same connected, focused field, unchanged
  text/revision, and uninterrupted dropdown interaction.
- Dismiss pending results on Escape, blur, clearing, and outside clicks; ignore
  stale errors without closing another field's current results.
- Check selection revision and current value before applying delayed details.
  A newer edit, selection, removed field, or blur prevents stale side effects.
- Preserve normal input/change events for draft and dependent-field listeners,
  but suppress new searches for programmatic selection updates and callbacks.
- Use a per-input session token, reused across that input's typing burst and
  renewed for the next search after a selection. Prediction objects retain the
  token for their associated details request, following Google's documentation:
  https://developers.google.com/maps/documentation/javascript/place-autocomplete-data
- Use one shared outside-click listener instead of retaining every old dialog
  input through a separate document listener.
- Preserve existing field discovery, lazy loading, US address restrictions,
  three-character minimum, 280 ms debounce, manual entry, accessible controls,
  and address-free analytics. No new service, pricing, or settings are added.

## Evidence and limits

- The first thirteen failure-case tests failed against the prior source.
- Final runtime matrix: **23 pass** against the new source. The identical
  matrix against `fd285ce7` reports **3 pass and 20 fail**, establishing that
  these checks distinguish the existing defects from the correction.
- Runtime cases include out-of-order responses, edits during debounce,
  clearing, cross-field results, old errors, blur/Escape/removal, details
  success/failure after manual correction, successful dependent-field filling,
  fallback behavior, no duplicate selection search, per-field token isolation
  and renewal, typing bursts, duplicate pointer selection, and click-handler
  lifetime/isolation.
- Focused Python wrapper/coverage/lazy-loader suite: **17 tests pass**.
- Final full discovery: **2,108 tests in 34.934 seconds; 2,106 pass and two
  fail**. The failures are the existing TXR-1507 approved-map reference checks
  awaiting completed-provider placement verification. No additional regression
  failure was reported; this is not an all-green release claim.
- Browser visual verification and actual provider behavior remain unverified.
  No measured conversion, revenue, or billing improvement is claimed. The
  expected benefit is more reliable address entry and fewer redundant calls.

The separate TXR-1507 provider test was refreshed at the start of this pass and
still showed **Sent**, not completed. No additional packet or reminder was sent.
Customer signature verification and production release remain separate work.
