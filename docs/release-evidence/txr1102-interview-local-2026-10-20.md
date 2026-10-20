# Lease-listing interview — local checkpoint, October 20, 2026

Status: implemented, locally tested and visually reviewed; **not deployed**.
Follows API/schema checkpoint `d91d47f3`. The release baseline remains the
documented production `bfd03d99` / shell v112; this slice did not poll Vercel.

## User outcome and scope

An agent can choose Lease listing, prepare an agreement through seven focused
steps, save it, open Prepared documents and reopen the same answers for editing.
The interview reuses the sale-listing dialog's navigation, session/account
guards, confirmed-save handling and ambiguous-save recovery, not a parallel
draft store. Lease-specific facts remain in a separate question model:

1. Landlord and property, with optional contact/legal-description details.
2. Monthly rent, lease-term range and listing dates.
3. Explicit negotiated listing, cooperating-broker, renewal and tenant-purchase
   compensation; no rates or fees are preselected.
4. Marketing, keybox, intermediary and make-ready instructions.
5. Property facts and the source-specific related-document checklist.
6. Optional landlord rental preferences; unconfirmed values stay unspecified.
7. Review and brokerage signer role. Preparing does not send invitations.

Saved workspace identity/property data and brokerage notice snapshots are
reused. Native Google-address hints and the existing form IDs/address observer
and companion mappings are retained. The offline shell includes the new model
asset. No brokerage seat, source-owner step or new commercial term was added.

Read-only review of the actual private source's paragraph 19 confirmed that
the lease checklist differs from the sale checklist. Labels now have one
server/client contract, including rental flood disclosure, lease lead paint,
IRS forms, unescorted access and assistance-animal information. Requested items
are never called attached documents. Actual related-PDF composition remains
the next workstream; a checklist is not a substitute for it.

## Verification

- Focused Python run: **162 tests, two unrelated source opt-in skips, exit 0**.
  Includes actual lease-source renderer/API tests, client/server field and
  preference limits, contract compatibility, sale interview regression,
  prepared-document isolation, navigation and offline/PWA checks. The logged
  saved-IABS failure is an intentional negative test.
- Node runtime suites executed within those tests: 12 lease model/opening
  cases, 28 shared sale model/save cases and eight document-viewer account
  isolation cases. Three ordinary/branch/preference client mappings pass the
  actual lease API parser losslessly.
- All 47 inline executable JavaScript blocks in `index.html` compile, and
  `git diff --check` passes.
- Actual Chromium/installed-Chrome local browser fixture: **67 lease checks**
  across 1280×1000 and 390×844, 16 screenshots. Exercises all seven steps,
  explicit zero, delayed MLS, make-ready authority, optional preferences,
  save → queue → edit → save on the same ID, plus mobile ambiguous network
  and conflict responses. No browser JavaScript errors or horizontal overflow.
- Two browser-generated real request payloads also pass the strict Python
  lease-answer validator. The browser fixture itself echoes synthetic API
  responses; it is not a hosted database or real-provider signing test.
- Shared sale-dialog browser regression: **seven checks**, four screenshots,
  both viewports; sale titles, six-step navigation and its own update action
  remain unchanged. These are separate from the lease suite above.

Commands:

```sh
HOF_TXR1102_SOURCE='../listing-source-2026-10-17/sources/TXR-1102-2026-01-05.pdf' \
  ../txr1101-runtime/bin/python -m unittest \
  tests.test_txr1102_interview_runtime tests.test_txr1101_interview_runtime \
  tests.test_agent_interview_navigation tests.test_txr1102_api tests.test_txr1101_api \
  tests.test_txr_1102 tests.test_standalone_recipient_preview \
  tests.test_standalone_form_schema_contract tests.test_pwa_baseline \
  tests.test_pwa_update_runtime tests.test_offline_draft_guidance \
  tests.test_public_pwa_registration -q

node scripts/qa/txr1101_interview_fixture.cjs /private/tmp/hof-lease-interview-20261020 --lease
node scripts/qa/check_lease_listing_interview_browser.cjs \
  /private/tmp/hof-lease-interview-20261020 ../lease-listing-2026-10-20/interview-browser

node scripts/qa/txr1101_interview_fixture.cjs /private/tmp/hof-sale-shared-dialog-20261020
node scripts/qa/check_lease_listing_interview_browser.cjs \
  /private/tmp/hof-sale-shared-dialog-20261020 ../lease-listing-2026-10-20/sale-regression-browser --sale-smoke
```

Browser tooling uses an isolated headless Chrome process, not the owner's
profile or tabs. Fixture traffic is localhost-only; all external traffic is
blocked. The bundled Playwright browser executable was absent, so the existing
installed Chrome was used without installing or upgrading dependencies.

## Visual findings and artifacts

Local captures live outside Git under:
`../lease-listing-2026-10-20/interview-browser/` and
`../lease-listing-2026-10-20/sale-regression-browser/`.

The first phone pass exposed an oversized/stacked optional-preference checkbox,
long allocation option text and content showing below the sticky footer. Fixed
the toggle, concise option labels, footer stacking/bottom padding and readable
prepared-document titles. Review dates now use readable month/day/year labels.
The post-fix browser run passed. All seven mobile step captures and the queue
were reviewed in contact sheets; updated mobile steps 3/6 and the queue were
rechecked individually, alongside desktop steps 1/7 and the mobile sale review.
The final legal-name maxlength adjustment is attribute-only and covered by a
runtime markup assertion; it does not change screenshot geometry.

## Remaining work and boundaries

- Compose real applicable lease-related PDFs, including the correct rental
  lead disclosure and rental flood disclosure, with truthful included/pending
  summaries and packet-bound review before send.
- Register/verify the exact lease source through the existing central private
  library as part of the coordinated release; no new owner authorization is
  needed for the already supplied source.
- Connect the additive lease readiness probe, complete packet/provider-rendering
  QA, then exact-head CI/full regression and one intentional code+schema release.
- Live Google prediction requests were not exercised by the network-isolated
  fixture. Existing address wiring was preserved, not replaced.

No hosted SQL, live SignWell calls, invitations, customer messages, Tyler email,
charges, new user permissions, Vercel checks or deployments occurred. No new
PDF output was authored. Full regression is reserved for the release candidate.
The roadmap remains active, and this is not a launch-completion claim.
