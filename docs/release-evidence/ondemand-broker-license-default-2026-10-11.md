# OnDemand Realty broker license default

## Outcome and scope

Use the owner-confirmed broker firm license `9010832` when OnDemand Realty is identified and its broker-license blank is empty. Scope: interview, agent profile, brokerage profile, TREC 20-19 contacts, TXR-1501, TXR-1507, TXR-1508, and the existing OnDemand brokerage record.

- Prior verified production: `da511a0d242d3026e7b716ad6cfbfeea3c4c49a5`, READY `dpl_96vs29Ewd4sSrezwrTQ7nRuYEHnS`.
- Preserve entered license values, other firms, associate/agent licenses, existing signed documents, and access roles. Case/space/punctuation variants of the exact OnDemand Realty name are accepted; unrelated firms are not.
- Fill existing UI blanks quietly, without another interview question. Clear only this automatic suggestion when its brokerage name changes; preserve user-entered values. Profile defaults cannot assign OnDemand's number to another firm in an open draft.
- The backend text-layout fallback covers restored or directly submitted blank-license purchase packets and representation/showing drafts without requiring a brokerage seat.
- Installed web shell v81 retires stale public assets without reloading an open interview.

## Approved source, authorization, and signing plan

- Approved source: existing TREC 20-19 revision 05-04-2026 and existing owner-supplied private TXR source revisions: TXR-1501/1507 06-15-26, TXR-1508 02-25-26. No printed source, terms, source vault entry, or source revision changes.
- Authorization and release authority: the owner supplied `9010832` and directed that it be used wherever OnDemand Realty has a blank broker-license field; standing authority covers the coordinated fix and release.
- Agent attestation: no new attestation, source-owner approval, or membership gate is introduced.
- Signing plan, roles, field coordinates, required flags, and simultaneous invitations are unchanged. This is a broker-identity text default, not a signing-map replacement.
- Authenticated QA database check: the exact OnDemand brokerage row had a null license. A blank-only update set it to `9010832`; a second live SELECT confirmed persistence. Both existing OnDemand agent profiles already contained the correct number and were not changed. No schema, account permissions, signed agreements, or client offer records were changed.
- Rendered signed-PDF QA / completed signature visual QA: no new provider-completed signing result is claimed. The previously recorded fresh signing-map verification gap remains separate; this text-only change adds no signature fields or geometry. No test/client invitations were sent for this default.

## Verification and cost boundary

- Four changed pages rendered from the actual generators against the approved local sources and visually inspected: purchase page 11, TXR-1501 page 6, TXR-1507 page 2, TXR-1508 page 1. The seven-digit license is legible inside its broker blank, separate from the associate license.
- Fifty-two focused tests pass, including four UI surfaces, nonmatching firms, explicit-value preservation, brokerage switches, profile-draft isolation, representation renderers, and PWA checks.
- All twelve golden purchase packets match the existing approved baseline; standalone TXR signing geometry is unchanged and matches its baseline.
- Full regression and protected CI are recorded at their completed checkpoints; do not treat an in-progress test as passed.
- The first full regression exposed isolated interview fixtures missing the new shared helper and event-listener setup. Corrected those fixtures to load the actual helpers; event registration is now a separately wired function. Seventeen affected runtime tests pass. No test assertions were removed, and that failed first run is not cited as green.
- Final local regression: 2,502 tests in 84.916 seconds, OK with one skipped. All 46 inline browser scripts parse successfully. Migration preflight confirms the unchanged 117-migration set; patch whitespace passes.
- One intentional prebuilt production release only. The existing release workflow checks actual Vercel headroom before building; no previews or automatic Git deployments. QA-only changes merged earlier require no standalone deployment.
- Existing release CLI commands now read the protected Vercel token from their scoped environment rather than process arguments. No new credential or permission was created.

## Initial deployed checkpoint and final profile matching correction

- PR #1310 passed independent CI `38175293147` and merged as `de2b16ff935b2390ee5937c2f06a5fe33323cf3c`.
- Intentional release `38175562394` succeeded: exact-commit regression, database readiness, spending, prebuilt build/deploy, canonical site, PWA, and packet-runtime checks all passed. READY deployment `dpl_Hnfm5BUa65epQKSouSgpRGRVKSyQ`, `homeofferflow-dyuyk05ps-dealdoc1s-projects.vercel.app`.
- The live pre-build spending check showed $0.03 used, $19.97 unconsumed, and a $3 reserve. This is a measured snapshot, not a future-usage guarantee.
- Final review found the brokerage-profile card could borrow a saved personal-profile license despite a different displayed firm name. Match the actual displayed brokerage before borrowing a saved license; otherwise apply only the exact named firm's known default. Preserve explicitly entered organization licenses. No backend/PDF/source/signing changes in this follow-up.
- Twenty-eight affected local tests pass. The actual profile-card template calls the tested matching helper; six differing-name/blank/explicit-license cases are covered. Installed web shell v82 delivers the corrected card without reloading an open interview.
- Protected CI and the corrected canonical release are recorded when actually completed. The already visual-reviewed PDF default and existing completed-provider signing gap are unchanged.
