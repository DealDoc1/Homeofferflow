# Conditional seller-disclosure questions — October 16, 2026

## Outcome and scope

The existing main/water disclosure interview now shows empty follow-up fields
only when the Seller's answers make them relevant. Roof details and optional
additional notes remain available. No answer is inferred, required, disabled or
silently cleared. If an answer changes after details have been entered, those
details stay visible with a short review hint until explicitly cleared; a
return to the relevant branch removes the hint. Numeric zero is retained.

Scope: index.html visibility helpers/listeners and draft reopening, actual-source
runtime coverage, and a fictional offline browser fixture. No PDF renderer,
signature geometry, source artwork, migration, account permission or pricing
change in this slice. The accumulated disclosure candidate still requires its
existing review-version migration and API to ship together.

## Verification

- Ten actual-source Node runtime cases passed: conditional occupancy, defects,
  smoke detectors, flood/repair and water/shared-well branches; changed answers;
  saved Unicode facts; explicit clearing; zero counts; hint reuse/removal.
- Twenty-two focused Python tests passed in 0.487s, including the runtime
  wrapper, listing-to-disclosure handoff, scalar roundtrip and source checks.
- Final full regression passed: 2,683 tests in 89.399s, one environment skip,
  process exit zero. Log: /private/tmp/hof-disclosure-conditional-full-20261016.log.
  The later Invalid fixture PDF diagnostic is an intentional negative-test
  output, not a failure. Patch whitespace passed.
- Actual-source offline browser fixture checked at 390px and 1280px CSS widths
  (mobile height approximately 844px; desktop 900px). Browser zoom was 80%, so
  the temporary outer override was adjusted to obtain the measured CSS widths;
  the override was reset afterward. Neither viewport had horizontal overflow.
- Occupancy and flood follow-ups appeared on their relevant answers. Filled
  details remained visible after the parent changed and disappeared only on
  explicit clearing. Shared-well answers, a capped-well count of 0, Unicode
  names and a paragraph break survived actual device save/reload/reopen. A
  changed well answer retained existing facts with review hints, then returning
  to Yes retired the hints without changing the stored values.
- Fixture uses the real render/collect/reopen/visibility helpers, isolated
  fictional local storage and connect-src 'none'. This proves the changed UI
  and device persistence, not authenticated API/database/provider integration.
  Browser logging contained an extension receiver-connection error; no page
  application failure was observed during these interactions.
- Screenshots: the persistent thread output folder
  disclosure-conditional-2026-10-16/mobile-shared-well.jpg and
  disclosure-conditional-2026-10-16/desktop-retained-details.jpg. These are local
  fictional QA views, not production or executed documents. QA tab closed and
  server stopped after verification.

## Release boundary

Not deployed and not completed-provider verified. No hosted build, production
SQL, customer-record mutation, provider invitation, email or charge occurred.
Automatic Git deployments remain disabled. The next release-critical work is
the integrated Seller review/signing/completed-PDF pass for the accumulated
candidate, not another source authorization or brokerage-seat requirement.
