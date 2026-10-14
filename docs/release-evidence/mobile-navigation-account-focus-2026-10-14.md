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

## Release checkpoint — 5:29 PM America/Chicago

- PR #1338 exact head a71abb467d18d3f00c8fc98a43746253b229f411 passed CI
  38646553036: 2,629 tests in 178.279s, two skipped; golden rendering, TXR
  geometry, schema preflight and whitespace passed. Normal merge:
  0b9bd2fb98171282fcb8ab10f5b9baf3269060f0.
- One intentional production run 38647063313 succeeded: merged-code suite
  2,629 tests in 173.215s, two skipped; project/schema/spend/build/readiness,
  canonical response, PWA and API/packet-runtime checks passed. Deployment-time
  credit remained $0.04 used/$19.96 unconsumed/$3 reserved.
- Vercel independently reports READY production deployment
  dpl_6nWbwsMspQsaH58hNnxZnaCm85py for the exact merge SHA, with both canonical
  domains assigned. Canonical/local byte identity:
  homepage 09bc57cab558b633227b8cd717753c4f217789082ed123baddb8cd8103c1ff7f;
  worker 7e440cd079abaca8852a3b5851f9ded1d0d7aae8d9ada9c44160f39a74da813c.
- Live 390px DOM initially confirmed Account, compact Start, page width 390,
  no horizontal overflow and no trial invitation. The existing saved offer
  then restored its Step 1 acknowledgement dialog as designed. No acknowledgement,
  New Offer action or signing acceptance was performed. The temporary tab's
  exit click and subsequent observations timed out; fresh live Agent/Explore
  interaction and a final live screenshot remain unverified, not passed.
- Local four-path visual/DOM checks above are valid but are not substituted for
  that incomplete live interaction. No error/fatal runtime entries appeared in
  the bounded 22:25:18–22:28:53 UTC query; this is not universal health proof.
- Temporary local preview and server were closed; live temporary-tab cleanup
  and viewport reset were attempted but unconfirmed because browser control
  was unresponsive. Original offer tab and two pending signing tabs were marked
  for preservation before the interruption.

## Follow-up canonical visual verification — 5:33 PM America/Chicago

Browser control recovered. The old temporary tab was independently confirmed
absent from the live tab inventory, so one fresh canonical `/?agent=1` tab was
used without restarting or replacing the original offer/signing tabs.

- The real owner account resolved to Agent / Broker with active/free-admin
  workspace access. Closed its account panel to inspect the landing page.
- At 390px, page and scroll widths are 390; Explore/Account/primary action are
  all 44px high. The primary action ends at x381.20 and has the full accessible
  label Start a Transaction. The public trial acquisition link is absent.
- At 320px, page and scroll widths are 320; the same controls are 44px high and
  the primary action ends at x311.20. Opened Explore: menu spans x89.61–309.61.
  Closed it successfully.
- Clicked the actual compact primary action: canonical `/agents` rendered
  Question 1 with Property listing, Purchase, Lease listing and Tenant
  representation links pointing to their existing allowlisted agent workflows.
  No transaction link, New Offer, legal acknowledgement, checkout or send was
  submitted. This proves the homepage handoff, not complete transaction signing.
- Saved and visually reviewed the live 390px screenshot at
  `/private/tmp/hof-mobile-navigation-live-2026-10-14.png`.
- Closed the fresh temporary tab, reset the viewport, and refreshed preservation
  marks for the original offer and both pending signing tabs. The earlier live
  screenshot/menu/handoff verification gap is now resolved.
- Read-only Vercel confirmation still identifies the same READY production
  deployment dpl_6nWbwsMspQsaH58hNnxZnaCm85py. No new release or paid service.
