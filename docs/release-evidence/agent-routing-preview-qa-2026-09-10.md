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

PR #1191 merged as `6ce62b6f8d7cad85fec0ff239c9424801beedcec`. The intentional
prebuilt release succeeded in GitHub Actions run `34497368235`; the Linux build
took seven seconds and the deployment became Ready at
`https://homeofferflow-aah5yce65-dealdoc1s-projects.vercel.app`. Canonical-domain,
PWA, API, and packet-runtime checks passed. A read-only early error scan for
that deployment returned no error logs. Canonical HTML and CSP contain every
repair marker, and the Showing Form interview opened from the guided choice
in authenticated live browser QA.

The signed-in account's purchase interview advanced through parties,
financing, addenda, disclosures, and closing to review. Its $350,000 QA price
minus $70,000 down payment produced the expected $280,000 loan. No offer packet
was generated or sent. Google autofilled the selected property, city, state,
ZIP, and county in Chrome; the in-app browser's earlier Google detail request
had returned a network error. This is not a completed signed-out consumer
journey or payment/signature QA claim.

The new controlled TXR-1508 QA draft has been prepared but is not yet sent.
The send review exposed an omitted account-linked signer in the UI. Delivery
was stopped before submission while that recipient-preview issue is repaired.
Current
completed-signature PDF visual QA remains a separate task and is not implied
by the synthetic preview test or unit-test results.
