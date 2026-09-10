# Agent routing and PDF preview QA — September 10, 2026

## Scope

This batch repairs the current guided interview and document-preview UI. It
does not change form source PDFs, field coordinates, signer placement, access
rules, or payment behavior.

- Connect Showing Form and Consumer Notice interview choices to their existing
  TXR-1508 and TXR-1506 draft forms. A selected document now gets a visible
  opening status and a retry action if opening fails.
- Remove purchase-closing lease addenda from the lease-listing branch.
  TXR-1953 and TXR-1954 remain under purchase addenda with context explaining
  existing tenant leases and leased fixtures at closing.
- Permit same-origin and blob PDF preview frames in the existing CSP while
  retaining the Stripe frame allowance. Other frame origins remain excluded.
- Add a same-document PDF download link and an explanatory fallback when the
  browser reports no inline PDF support. Object URLs are revoked on close.
- Increment the offline application shell to v64.
- Pin the prebuilt production workflow to repository-secret project/team IDs,
  checking them before environment pull and before build.

## Evidence

- Live canonical QA reproduced the Showing Form route failing to open its
  interview, while the direct form button successfully prepared a saved draft.
- Live canonical QA reproduced a PDF preview blocked by the frame policy.
- Auth restoration took approximately two seconds before routing to the
  correct question; this delay was not incorrectly counted as a broken route.
- User-supplied TXR-1953 and TXR-1954 source text identifies purchase-contract
  closing obligations, not rental-listing agreements.
- Local Node behavior tests execute the production opener functions: both
  repaired forms, delayed mounting, bounded failure, PDF-capable rendering,
  no-viewer fallback, and private object-URL cleanup.
- A localhost-only synthetic PDF using the actual preview helper and actual
  CSP rendered visually in Chrome. The in-app browser did not render its
  native PDF frame; the download link was visible. No private document was
  exported through an alternate route for that test.
- Full local regression suite: 1,609 tests passed. This includes the Python
  wrappers for the seven Node behavioral subtests. Whitespace check passed.

## Remaining verification

Production verification follows the intentional prebuilt deployment. The new
controlled TXR-1508 QA draft has been prepared but is not yet sent. Current
completed-signature PDF visual QA remains a separate task and is not implied
by the synthetic preview test or unit-test results.
