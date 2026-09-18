# Google address picker interaction repair — September 18, 2026

Status: implemented and tested locally; not pushed or deployed. Google Places
remains the preferred address source throughout the existing shared picker;
manual address entry remains available. No external provider requests, paid
resources, customer messages, or Vercel builds were used for this work.

## User story and reproduced defects

An agent or customer selects a suggested address, continues through the
interview by keyboard, and receives the complete location without losing
focus or having later manual changes overwritten. The existing picker:

- only selected on mouse-down or touch-end, omitting click-only activation;
- blurred the address after details returned, disrupting keyboard navigation;
- canceled selected-place details merely because the user tabbed ahead;
- intercepted IME Enter and searched intermediate composition text.

Seven newly added runtime checks failed against the unchanged source. The
repairs add click activation with the existing synchronous duplicate guard,
keep focus under the customer's control, distinguish suggestion dismissal
from completion of a chosen address, and defer searches during composition.
Pending details now also check that companion fields remain connected and
unchanged, so a manually corrected city/state/ZIP/county is not overwritten.
Typing a different street still invalidates the previous selection.

Keyboard focus behavior was checked against the W3C editable combobox pattern:
https://www.w3.org/WAI/ARIA/apg/patterns/combobox/
This is not a full accessibility-conformance certification.

## Automated checks

- `node --test tests/google_address_races.runtime.cjs tests/google_address_components.runtime.cjs`:
  **52 passed** (34 interaction/race checks and 18 component-integrity checks).
- The ten additional interaction checks cover click-only activation,
  mouse/touch/click duplicate prevention, keyboard focus, delayed details after
  Tab, edited/removed companion fields, composition request suppression,
  invalidation of pre-composition searches, and both modern and legacy IME
  Enter signals. The pre-change run passed 27 of 34 race/interaction checks;
  seven behavior assertions failed, not just source-text checks.
- Focused Python address tests: **14 passed**.
- Full discovery: **2,109 tests in 35.012 seconds; 2,107 pass, two fail**.
  The only failures are the unchanged TXR-1507 approved-map comparisons:
  `test_every_current_map_matches_the_source_calibrated_baseline` and
  `test_current_released_maps_match_the_approved_baseline`. Those references
  have not been rewritten to conceal the outstanding completed-PDF QA.
- `git diff --check` passes.

## Browser check and boundaries

`node scripts/qa/address_picker_preview.cjs` serves a loopback-only page using
the actual picker and address-component functions extracted from `index.html`.
The helper supplies synthetic Google-shaped responses, no credentials, and a
Content Security Policy that blocks external connections. It does not expose
the repository, source PDFs, or customer data. The local browser check showed:

1. The page rendered labeled fields and a suggestion list.
2. ArrowDown + Enter selected the first address, populated the unit, city,
   state, ZIP+4 and county, and retained address focus.
3. Tab moved directly to City.
4. With details deliberately held, ArrowUp + Enter selected the last address,
   cleared the former location, and Tab moved to City. Releasing the details
   filled the selected location while focus stayed in City.
5. Pointer selection performed one details request. A manual city correction
   while details were pending survived the response; no stale location was
   applied and focus remained in City.

Browser logs contained one connection error at initial load: "Could not
establish connection. Receiving end does not exist." Its origin was not
established. It did not recur during the successful interaction checks; no
picker exception was observed. This is not a claim of a completely clean
browser console.

Click-only and IME behavior are runtime-event tested, not a screen-reader or
physical mobile-device pass. Live Google credentials/network responses,
production layout, authenticated draft persistence, and resulting customer
PDFs were not tested by this synthetic fixture. No end-to-end production pass
or measured conversion improvement is claimed.
