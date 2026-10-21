# Customer listing reconciliation - October 21, 2026

## Bounded outcome

Reconcile draft PR 1353's customer sale/lease package with actual production
`24d619ebfc8e864440a324368b919cfe273b4ca6` (PR 1355), preserving the working
purchase/disclosure flows and the newly deployed operator QA path. This is a
local checkpoint, not a customer release or additional invitation.

Production QA workflow 39594340665 passed, including 2,914 tests (24 opt-in
source skips), canonical checks and deployment dpl_4Dw1cxCYGGWNSoN9gTtnJSrBFg7Z.
Exact-head CI 39593624648 is green. The workflow performed the only spend check:
$0.05 used, $19.95 unconsumed, $3 reserve. No repeated usage polling or preview.

## Reconciliation

- Preserve the source-only applied migration 20261021113432 byte-for-byte.
  The four customer listing migrations remain unapplied; no migration history
  is rewritten. The pending earlier source constraint and deployed constraint
  allow the same complete 22 codes, in either application order.
- Keep both the customer lease-listing readiness probe and the deployed
  rental-source readiness probe. Tests verify all eight exact probes, their
  ordering, invalid-contract failure and no application-row reads.
- Reserve shell v114 for the next customer release and synchronize all PWA
  and companion expectations. Production remains v113.
- Preserve the exact deployed provider maps, fixed operator actions, approved
  recipients and no-seat customer listing behavior. Rental component sources
  do not become standalone signing workflows; primary listing activation is
  tested separately with signing enabled.

## Focused evidence

Existing pinned runtime: `../txr1101-runtime/bin/python`.

- 109 focused source/readiness/PWA/operator/schema tests pass, four optional
  source skips. An initial system-Python run lacked httpx/pypdf; that runtime
  setup failure is not reported as a pass.
- With exact TXR-1102 and rental source opt-ins, 27 focused QA/disclosure/
  operator tests pass without skips.
- After strengthening component-vs-primary activation coverage, all 33
  source/readiness tests pass.
- `scripts/qa/check_lease_listing_schema.cjs --source-first`: 71 real isolated
  PostgreSQL assertions pass; chronological invocation: 70 assertions pass.
  Both retain grants/RLS and both readiness contracts. The sandbox initially
  denied local shared memory; the same approved fixture then passed with the
  required host permission. No TCP, cloud access or provider sends.
- Migration preflight: 126 migrations, no errors. Whitespace check passes.

The earlier full candidate run at 993963cc passed 3,027 tests with two skips;
it predates this merge and is not claimed as an exact-current full pass.
Run the full suite once at the next real customer-release freeze, not for each
documentation checkpoint. No new hosted customer migration, CI push or deploy
was performed by this reconciliation.

## Live provider state, not completion proof

Private sources TXR-2008 c2a8e41f-a4c5-41ca-b030-15add700bebc and TXR-2015
65426cad-0e63-4fb4-aa23-5afacc085f67 are registered, approved and hash-verified.
They join the existing exact TXR-1102 source. QA run
d8223a26-2084-4755-a20a-e3723683eb56 owns the sole provider document
940f1c1a-d5be-4fff-bad3-a66d55765841 (14 pages, 44 fields).
Initial readback retained its private draft. Later read-only readback passed
all ten checks on that same document; the precise initial failure cause is
not recorded. The owner UI sent that retained document once; both approved
inboxes received the 7:01 AM invitation. No duplicate packet or real client.

Landlord A chose floodplain not aware, flooding aware, known lead hazards and
no reports, with a short fictional explanation. The reports explanation stayed
optional. All required fields for both QA roles are prepared at final Agree &
Finish. Packet-specific electronic-signature disclosure consent was requested
once and remains unanswered. No final acceptance, completed PDF hash or visual
pass is claimed. Private signing links and screenshots are not committed.

Remaining release evidence: final QA completion and actual completed-PDF
placement review, separate ordinary sale-listing completion, coordinated
customer schema/application release, then canonical customer-flow verification.
These are implementation/verification tasks, not source authorization gates.

## Reconciled full-candidate result

At `8efaf9360a6b`, the exact reconciled code passed **3,029 tests, two optional
source skips, exit 0**, in 115.405 seconds. Source opt-ins used the same exact
private TXR-1101, TXR-1102 and rental originals as the preceding full run. The
retained log is outside Git at
`../lease-listing-2026-10-20/ordinary-provider-qa/reconciled-regression-2026-10-21.log`.
The intentional Invalid fixture PDF message is a passing negative-path test.
No application or mapping changes followed this result. Only this evidence
and the roadmap are updated before fast-forwarding the existing draft PR.
Git automatic deployments remain disabled; a PR push is not a deployment.
