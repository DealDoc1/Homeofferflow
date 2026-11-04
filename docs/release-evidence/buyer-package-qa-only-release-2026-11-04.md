# Isolated owner-only buyer-package QA capability — November 4, 2026

## Release contract

Baseline: verified production e99a462adbcd0d102b842f9ced976b3c463cd3ec,
READY deployment dpl_AoGVYqG5qZMSY82vJwqAojhFpz6c. Candidate branch:
codex/buyer-package-qa-release-2026-11-04. The preserved roadmap remains on
codex/stripe-webhook-hotfix; no reset, stash or unfinished feature release.

Outcome: permit one fixed, fictional buyer representation/consumer notice/IABS
test through the existing protected production signing connection. This releases
a QA capability; it does not enable the customer combined/custom-package flow.
No customer renderer, field map, source revision, invitation ordering, form
eligibility, plan, billing behavior or interview changes. No database migration.

The new pure representation_package helper is unconnected to customer routes in
this candidate. A dedicated AST test proves that its only product-code consumer
is buyer_representation_signing_qa. The latter is callable only through the
owner-email allowlist plus platform-admin check and fixed action-only body.
This follows the existing protected QA-only release pattern rather than claiming
completed customer signing evidence before the test can run.

## Source, authorization and signing plan

Approved source hashes for TXR-1507 and TXR-1506 are fixed, as are the exact
reviewed saved-profile IABS and rendered PDF digests. Source catalog rows must
be approved and authorization-attested with valid IDs, brokerage-relative private
paths and exact revision/hash. The server downloads and verifies private bytes.
The signed-in owner's IABS profile ID/version is checked before and after its
private download; it must match the reviewed IABS. No cross-account sharing or
permissions change. Existing source originals and real agreements are untouched.

The signing plan is one fictional buyer and associate using only the established
two owner-controlled QA inboxes, test mode true, private draft first, simultaneous
invitations, reminders off and no added signature page. The nine-page specimen
has 15 fields/four signatures, with the IABS last and informational only.
Its PDF is byte-identical to the previously visually reviewed ordinary specimen;
only fixed QA recipient IDs are remapped. Packet SHA-256:
92a27bf2e5f7b3c4448a7e92e8b42faf48430a5787951b9a25c9dddca8c00faa.
Layout SHA-256:
82092c5ca574ff4a10d7fdd42e6d815a5ace9b16ac2c57f3505d84059c6cfdfd.

The existing durable scenario/revision reservation precedes provider creation.
Draft identity is persisted before readback, and send_started precedes its sole
send. Existing identity/metadata/geometry/recipient/control checks remain; an
additional QA-only verifier requires exact Boolean required/optional flags.
It is called only by the fixed operator draft runner. The customer shared
signwell_request module remains byte-identical to production. Missing/changed
flags leave the QA draft unsent, including signatures made optional. Ambiguous
outcomes are inspected instead of creating a replacement. Credentials stay in
the existing server runtime; no credential is exported or newly configured.

## Regression and user experience

60 unique focused tests pass across buyer_qa_release_boundary,
buyer_representation_signing_qa, buyer_package_qa, operator_purchase_signing_qa,
listing_package_signing_qa, operator_listing_lead_signing_qa,
representation_package, signwell_qa_readback and operator_signing_controls_runtime.
The final two IABS helper tests passed separately after the 58-case main run.
Actual private buyer/listing sources were supplied; no focused cases skipped.
The Node harness covers the new scope's fixed check/send actions as well as
existing scopes. Extra negative shared-runner cases prove changed/missing/non-
Boolean required flags do not send. Ownership, stale profile, tampered source,
reserved attempt, payload pins and no-customer activation are covered.

The actual owner-control markup/function with repository head styles was
reviewed in a network-blocked fictional fixture at 390x844 and 1280x800. Send
starts disabled; a mocked not_started check enables only the selected control
and shows its status. Text wraps and touch targets are readable. No real send
was clicked. The temporary viewport/tab/server were reset/closed/stopped.
The shell advances from v132 to v133 for this operator-control addition.

Rendered signed-PDF QA is still pending and is the purpose of this capability.
It is not a passed customer-form gate. The prior ordinary/two-client/broker/
Unicode offline review is recorded in the preserved roadmap; no PDF page or
licensed source changed in this candidate. No PDF is committed or re-authored.
Full frozen candidate regression passed: 2,996 tests, 20 skipped, 105.390
seconds. Private buyer/listing source cases were supplied locally. Expected
mocked provider/fixture-error logs belong to negative tests. Supabase branch
preflight passed with 123 migration files and zero errors. Patch whitespace
passes. Exact-head CI and the existing live release checks remain required.

## Release authority and cost boundary

Release authority is the owner's standing instruction for verified, cost-checked
roadmap releases and controlled fictional QA. No customer/partner message or real
agreement is authorized by this QA action. The operator capability itself sends
nothing until its send control is deliberately used after a status check.

Vercel production/team/project were independently verified. Read-only current
deployment history reports three deployments in the last 24 hours. The refreshed
November 4 usage dashboard reports $0.02/$20 credit usage in the current cycle,
leaving $19.98 before the required $3 reserve; dashboard usage can lag one hour.
The billing connector returned Plan not found, so its result is not cost proof.
The existing production workflow must repeat its live frequency/spend/schema/
project gates before its single Linux prebuilt deployment. Automatic Git
deployments remain disabled. No preview, new service, subscription or credential.

This checkpoint makes no deployment, completed-provider or production-runtime
claim. Those results must be recorded only after observed. Broader package
schema, point-of-use and completed signing release requirements remain intact.
