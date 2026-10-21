# Lease signing operator control - October 21, 2026

Status: **implemented locally, focused tested, offline browser checked**.
No new provider document, invitation, source upload, hosted migration, credential,
billing change, deployment or Vercel usage check.

The fixed lease provider-QA endpoint added at `6bc2d794` lacked a matching owner
control. Add it to the existing collapsed Delivery Connections QA panel, inside
the existing approved-email and platform-admin boundary. The test description
identifies one fictional landlord/associate and rental lead/flood components,
not a matrix of customer contracts. Start its send button disabled; the owner
must first read the recorded status. Preserve the existing reservation-based
one-attempt server mechanism and read-only check action.

Replace the nested frontend scope ternary with an explicit fixed action/widget
map for purchase, showing, amendment, listing-lead, listing-package and
lease-listing. Unknown/inherited keys return before any request. Previously an
unknown scope could fall through to the purchase test: it must not be used as
a way to invoke a lease QA endpoint. Each valid scope affects only its own
status and send button; ambiguous responses keep send disabled while retaining
the read-only check control. Server authorization and source/render code are
unchanged, and no arbitrary caller-provided API action is introduced.

## Verification

```sh
HOF_TXR1101_SOURCE='../listing-source-2026-10-17/sources/TXR-1101-2026-06-15.pdf' \
HOF_TXR1102_SOURCE='../listing-source-2026-10-17/sources/TXR-1102-2026-01-05.pdf' \
HOF_LEASE_DISCLOSURE_SOURCES='../lease-listing-2026-10-20/sources' \
  ../txr1101-runtime/bin/python -m unittest \
  tests.test_operator_signing_controls_runtime tests.test_lease_listing_signing_qa \
  tests.test_amendment_signing_qa tests.test_listing_package_signing_qa -q
```

**26 focused tests pass, no skips, exit 0.** Includes all six send/check action
pairs, cross-widget isolation, missing session, unknown/prototype scope names,
ambiguous response handling, fixed recipients and source/layout validation.
The Node controls runtime has 16 cases (already included in the Python wrapper,
not 16 additional Python tests). `git diff --check` passes.

`scripts/qa/operator_signing_fixture.cjs` extracts the actual owner-control HTML
and actual handler into a no-network fixture with a synthetic status response.
In CUA, send began disabled. Clicking Check lease listing test produced exactly
`{"action":"check_lease_listing_signing_test"}` and enabled that control only
for the fictional not-started result. No send button was clicked; the fixture
also refuses sending. No JavaScript errors. The fixture's standalone wrapper
needed explicit inherited admin text color to be readable; that harness-only
correction did not change production styling. The final local screenshot is
`../lease-listing-2026-10-20/ordinary-provider-qa/operator-control-local.jpg`.
Temporary browser/server were closed. This is not a hosted or provider test.

## Candidate / release state

The preceding candidate `993963cc3fab8fe082167d6ec59925705b84b220` completed
GitHub run `39590140951` successfully: full unit suite, golden packet rendering,
standalone signer geometry, Supabase branch preflight and whitespace. Its local
full result was 3,027 tests, two optional-source skips. Those results must not be
silently attributed to this later UI addition. This change has focused coverage;
the next draft-PR CI run will verify the exact updated commit, without another
duplicate local full run. No renderer or source geometry changed.

Remaining: make the fixed QA path available through the intentional coordinated
release process, register rental components privately with the matching source
catalog, complete actual SignWell signing and inspect the completed PDF. The
existing ordinary sale-listing test remains a separate pending completion, not
an invitation to resend it. General owner/source authorization is not missing.
Keep PR 1353 draft and do not claim these customer workflows are deployed yet.
