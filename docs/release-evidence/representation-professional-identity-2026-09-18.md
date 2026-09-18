# Representation professional identity - September 18, 2026

**Local candidate; not deployed, database-verified or live-provider verified.**

## Finding and correction

Shared-library drafts retain the PDF source host in the existing non-null
`brokerage_id` column. Rendering and broker-recipient resolution incorrectly
treated that host as the drafting agent's brokerage. Merely choosing an available
source could therefore populate another office's name/license or select its
contact as the broker signer.

The source-host column now remains audit-only in these paths. A common resolver
reads the signed-in agent's own profile and optional active organization. Agents
without a seat use their saved brokerage name/license. An active, owner-linked
membership can supply that organization's identity and broker contact. Missing
or inactive membership does not block the associate signing path. No broker
email is inferred from the agent's email or from source ownership.

The send handler resolves this context once and shares it with rendering, so a
profile edit during source download cannot produce different professional names
in the PDF and recipient list. The actual resolved values remain part of the
tracked-request fingerprint. Buyer/seller-only addenda skip these identity reads.
Existing draft ownership, source revision and delivery checkpoints remain intact.
Simultaneous signing remains `apply_signing_order=False`.

## Verification

- Seven new resolver tests cover no-seat use, active own organization, inactive
  or missing organizations, missing profile, database failure, foreign-host
  rejection and the shared professional context.
- Real-render/offline-delivery fixtures now deliberately use different source
  and agent brokerage IDs, and assert owner-scoped queries. They exercise
  TXR-1501/TXR-1507, both professional roles and one/two clients. Additional
  integration tests cover no-seat profile rendering and mid-preparation edits.
- 34 focused tests passed before the final full-suite run. Provider HTTP and
  database responses are mocked; no actual invitations are sent.
- Two source-based short-form specimens (independent profile / own linked
  organization) were generated through the real render/send adapter with mocked
  persistence and delivery. All four rendered pages were visually inspected.
  Names/license values occupy the existing measured blanks. Geometry unchanged.
- The PDF skill supplied the render-and-inspect workflow. Private synthetic
  specimens stay under `tmp/pdfs/professional-identity-review/`, untracked.
- Full discovery: 2,220 tests in 50.135 seconds; 2,218 pass and the same two
  approved signing-map reference comparisons fail. No baseline was regenerated.
  Log: `/private/tmp/hof-professional-identity-suite-final.log`. The first run
  also exposed an obsolete source-string assertion, which was updated to check
  the new resolver alongside runtime no-seat and foreign-host tests.

## Security and scope

The Supabase skill informed the owner-scoped profile/membership queries and
failure handling. Current changelog and Data API security documentation were
reviewed; no relevant API breaking change was identified. Queries use the
verified server user ID, never browser-supplied brokerage IDs or editable JWT
metadata. Profile lookup failure raises rather than silently producing an empty
identity. No grants, RLS, schema, dependencies or client keys changed. No live
database query/mutation, public push, deployment, build or paid test occurred.

## Still outstanding

- The supplied source PDF has static OnDemand production/contact details in its
  footer. They remain visible in both specimens. This correction only addresses
  dynamically populated legal-party/execution fields and recipient selection;
  it does not claim a fully neutral shared-library output.
- An independent agent choosing a separate broker signer still needs an explicit
  self-service broker contact workflow if no own linked office contact exists.
  This change deliberately does not substitute the source provider's contact or
  silently treat the agent as the broker. Associate signing needs no seat.
- Production release and actual completed-provider verification remain pending.
  Existing client documents and source files were not modified or replaced.

## Subsequent local continuation

The independent separate-broker contact workflow above was subsequently
implemented and tested locally; see
[independent-broker signing](independent-broker-signing-2026-09-18.md).
It is not deployed/live-provider verified. The static source footer issue remains.
