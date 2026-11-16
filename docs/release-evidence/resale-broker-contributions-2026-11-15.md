# TREC 20-19 resale brokerage contributions

Corrected the agent prompt for §12B(1) to identify the seller's contribution
toward the buyer's broker. Removed the obsolete Page 10 wording and turned
off automatic use of the old profile fee default for new offers. Existing
transaction selections stay in the same serialized fields and contract rows.

Closing now collects §12B(2) separately as a dollar amount or percentage of
sales price when the buyer contributes toward the seller's broker. The review
names the payer and recipient on each row. The browser, checkout and packet
generator validate the selected buyer amount. An explicit buyer contribution
also works for an unrepresented buyer. Existing API keys and aliases remain
available. Reopening an older draft restores the contribution and saves only
the selected unit. No change to the buyer representation agreement.

Page 7 of source TREC 20-19, revision 05-04-2026, was reviewed for both payment
directions, both units, an unrepresented buyer and a cleared choice. The
source and signing fields were unchanged. Offline Chrome at 390 and 1280
pixels confirmed conditional fields, separate review values, percentage
validation and saved-draft alias restoration. Forty-four focused tests passed.
The roadmap shell is v413. No deployment, live checkout, or signature send ran.

Inspection of the separate §7I work found that the shared PDF checkout
preflight runs only for assumption financing. The water disclosure browser
and packet checks apply broadly, but standard cash and financed checkouts
still need the server-side water guard in `api/create-checkout.js`. Carry
that fix into the isolated water-disclosure release before publication.

## November 16 isolated production candidate

The §7I guard is already live. The compensation patch is isolated on the
verified production base `756cf5b130a93f7cc0cfa770f0006643540d1282`
(deployment `dpl_E4XyCmCeTxRYDAvBDHRH1A9XHGaD`). The candidate changes
the interview, checkout validation, page 7 answer rendering, and shell
v194. It adds no database migration and keeps Git deployments disabled.

### Approved source and authorization

The existing public TREC 20-19 source, printed revision 05-04-2026, is
unchanged from production. The SHA-256 of `20-19_0.pdf` is
`be3fa154f00476a674c73ba20f6c589111a905bc1e0894e0d5786b714f16f8d4`.
This patch only fills the existing §12B lines on the production source.
Adoption of the newer download has independent signing QA.

### Signing plan and rendered signed-PDF QA

Recipient routing, simultaneous signing, document order, and execution
fields remain unchanged. The existing completed-provider evidence for the
execution layout is `purchase-provider-completion-2026-10-12.md`. Its
three-case, 26-field layout fingerprint reproduced exactly
(`f9f006620d97dccce36b273f52544788d7c664e453b199d98e74e694d9cbaf34`).
Page 7 answer rendering was visually checked for both payment directions,
both units, a single unrepresented buyer, and an explicitly cleared
contribution. No fresh provider send was performed.

### Regression

On the isolated candidate, 202 focused checkout, packet, saved offer,
profile and cache checks passed. Offline Chrome at 390 and 1280 pixels
verified both the compensation steps and the water workflow, review,
validation and saved-draft restoration. A previous full run on identical
runtime and test files ran 3,037 tests, with no failures and 27 skips.
Exact-head GitHub CI and the production workflow repeat release checks.

### Release authority

The owner requested release of the generated-document fixes based on
OnDemand's compliance feedback. This candidate is limited to §12B on the
currently deployed source. Use the existing guarded prebuilt release and
canonical verification. Rollback target is the prior production deployment
listed above. No deployment was initiated during candidate preparation.
