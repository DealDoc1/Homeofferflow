# Mobile navigation and account focus — 2026-10-14

## Intended outcome

Make the homepage navigation usable on narrow phones and remove duplicate
public trial acquisition prompts after sign-in. Preserve all four customer
audiences, existing saved-offer Resume routing, enrollment terms, and permissions.

## Reproduction and bounded changes

- Canonical authenticated Agent homepage at 390px: the navigation action ended
  at x403.58, outside the viewport; an active/free-admin owner also saw the public
  OnDemand trial invitation.
- At widths up to 640px, primary navigation now uses a display-only Start/Resume
  caption, retaining the full desktop text, accessible name and existing action.
  Explore, Account/Sign In, and the primary action have at least 44px height.
- The Explore dropdown anchors to the header and stays within the viewport.
- The public Agent trial invitation is guest-only. Signed-in account/billing
  surfaces retain their existing enrollment controls; this does not determine
  eligibility or change subscriptions.
- Shell cache v100 refreshes the edited homepage for installed clients.

## Verification before release

- 42 focused Python tests passed, including actual-source Node runtime cases for
  guest/signed-in transitions, seven account status variants, and five full/compact
  navigation labels including Resume.
- The local full suite ran 2,629 tests in 84.988s: one obsolete source-text
  assertion expected the old guest-unaware condition, and one test was skipped.
  Updated that assertion to the new guest-only condition; all 67 affected trial,
  mobile-navigation, and PWA checks then passed. No customer source changed after
  the full run. Green frozen-candidate CI is required before merge.
- Isolated browser fixture loads the actual homepage markup, styles and relevant
  presentation functions, with fictional account state and no live services.
- All four audiences at 320px and 390px: page width equals viewport, controls fit,
  full accessible labels remain intact, signed-in trial invitation absent.
- At 320px, the Explore menu spans x89.61–309.61. Guest navigation controls are
  44px high; the primary action ends at x311.20. At 390px it ends at x381.20.
- All four audiences at 1280px retain full desktop navigation text with no
  overflow. Guest Agent promo returns on sign-out. Fictional saved data stays
  unchanged during account refresh.
- Full regression and release checks are recorded by the linked CI runs. Final
  canonical browser verification follows release; local fixture is not evidence
  of real-account billing or a complete signing transaction.

## Safety and deployment

No changes to contracts, PDF geometry, signing order, permissions, database,
address autocomplete, checkout terms, or saved transaction data. No emails or
new signing packets. Automatic Git deployments remain disabled; use one
intentional prebuilt production release after the existing fresh credit/headroom
check. Production base: 38503472b27ca98fee794278416a0a0dd9d7b77b.

Fresh read-only capacity workflow 38646291849 passed at 22:15:29 UTC: five
deployments in the preceding 24 hours, $0.04 infrastructure credit used and
$19.96 unconsumed for September 22–October 21, with the existing $3 reserve.
The release workflow repeats the spend check immediately before deployment.

## Rollback

Promote the prior known-good production deployment dpl_DgRB6xjr8xD4FHB4uyr9jRMu643Y
if canonical navigation or account display fails, then correct on a new branch.
