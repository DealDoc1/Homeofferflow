# Isolated transaction-print release candidate — November 2, 2026

## Outcome and exact scope

Give agents **Print unsigned copy** on prepared offer cards and details, and
**Signed PDF** on completed offers. The preview offers Open to print, Download
PDF and Close preview. Unsigned copies explicitly say they are reconstructed
from saved terms and must be reviewed before hand signing; they do not send
invitations or consume another packet.

Production baseline: `17da266084a593c2e4053259cd23b08e14f54780`, READY deployment
`dpl_9AJuyzeHsi7HppTrpPg7tQB7Srxt`. The candidate is based directly on that commit. A single read-only Git fetch
updated the remote-tracking ref; no reset, stash or existing work was changed. The candidate isolates the original
`fbe608fe` print feature from all unreleased roadmap changes. Its only product
changes are additive read-only dispatch/helper code in `api/fill-pdf.py`,
`lib/offer_printing.py`, print controls in `index.html`, and shell v131.
No SQL, source PDF, renderer, signing map, signature creation/retry, recipient
routing, billing, authentication policy, or workflow file changes.

## Approved source and authorization

Existing production approved source checks and pinned renderers are reused.
No source or renderer file changes relative to production. The helper reads
only the authenticated owner's saved offer and discards browser-supplied terms.
It compares recorded source/renderer manifests after rendering and refuses
changed versions. Draft/generating/failed-generation records cannot be printed.
Client checkout-shaped fields do not enter the paid-generation path. Private
PDF responses are no-store and never added to the service-worker cache.
The owner explicitly requested transaction printing and hand-signature access,
and has standing authority for verified cost-checked releases. No agent seat,
new source-owner gate, new paid service, or customer message is introduced.

## Signing plan and rendered signed-PDF QA

Unsigned printing never creates a provider document, sends invitations, updates
transaction state, or reserves usage. Completed signing copies use the existing
owner-scoped provider-confirmed completed-download endpoint. All existing
signers, concurrent invitations and field rules are unchanged.

Rendered signed-PDF QA is reused only for unchanged components: the corrected
purchase contact/execution map has completed-provider review recorded in
`purchase-provider-completion-2026-10-12.md` (document
`6ad57745-57bc-4bd0-8324-e7d68b51c86e`, PDF digest
`cf7e8d01cb6b738f3876359ca83d68a8c011b13855533c70a1fb8e26ddb0ce50`).
Disclosure placement retains the completed v4 component proof recorded in
`seller-disclosure-v4-completed-review-2026-10-19.md`. This candidate changes
neither component nor provider rendering, so the lean protocol does not require
another signing packet. It does not clear pending provider QA for other forms
or the separate new required-field readback guard. No claim is made that those
unreleased signing workstreams are included or complete.

## Regression and UX evidence

- 31 focused Python tests passed: offer-print ownership/dispatch, transaction
  signing recovery, PWA update behavior and update experience.
- Browser runtime passes unsigned/signed routing, invalid response and version
  failure recovery, signed-out access, account changes/sign-out while reading
  either PDF, and stale-account error suppression. Requests capture the session;
  an old account's result cannot open in a new account.
- Fictional localhost-only preview controls visually reviewed at desktop and
  390x844 mobile using this candidate's exact action code. No customer data or
  external calls. The fixture PDF is blank; this verifies controls/layout,
  not fresh form placement. The prior browser policy block on blob-tab
  navigation was respected; native download/print-dialog interaction remains
  unverified by that tool. Agent access to the recovered original PDF remains
  available separately.
- Full regression: 2,957 tests, 23 skipped, passed using the existing pinned
  runtime. The first run found one test hard-coded to shell v130. Its asset
  checks remain intact, and its shell check now enforces version >=130.
  All five disclosure-attachment tests passed, followed by the full rerun.
- All 12 golden rendering scenarios match the approved baseline, including
  signing geometry. Standalone signer geometry also matches. Supabase branch
  preflight passes with 123 migration files; no schema changes are included.
  Whitespace checks pass. Exact-head CI remains required before merge/release.

## Release authority and cost boundary

Use only the existing prebuilt production workflow after affirmative evidence,
exact-head CI, author, existing project/schema and current cost checks. Do not
create previews or deploy this evidence alone. Automatic Git deployments remain
disabled. No customer packet, email, signing invitation, production data repair,
credential change or charge occurred during preparation. The original SignWell
HTTP 422 and historical email receipt remain separate unresolved incidents.

## Automated release gate status

- approved source: verified
- authorization: verified
- signing plan: verified
- rendered signed-pdf qa: verified
- regression: passed
- release authority: approved
- ready for production: yes

These statuses apply only to the unchanged production offer renderer/component
proof and this read-only print-access candidate. They do not approve other
roadmap forms or new signing-map changes. Deployment still requires exact-head
CI, the existing workflow's live schema/project/cost gates, and canonical
verification; none is bypassed by these local candidate statuses.
