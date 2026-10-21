# Listing candidate / live partner integration — October 21, 2026

## Outcome and scope

Reconcile the customer sale/lease listing candidate with confirmed production
`0b50b3b5810997e4e83bc87704ea00cbd75e5057`, without undoing the live partner
features, changing reviewed PDF maps, or releasing incomplete customer work.
GitHub production run 39674071508 is terminal success at that exact revision.
Draft PR 1353 was open at 6fbd9704 with green CI 39599483528 before this merge.

## Changes

- Merge current main, preserving optional public-only partner headshots,
  setup-status visibility, versioned assets and graceful legacy-helper support.
- Resolve only shell-version merge conflicts: reserve v116 consistently in
  the worker and seven PWA/companion expectations; live production stays v115.
- Preserve eight readiness probes, including customer lease, rental sources
  and the new zero-row public-headshot-column check. Add an explicit assertion
  for that column in the merged readiness test.
- Compare reviewed TXR-1101/1102 renderers, lease disclosures, listing packet
  composition and both ordinary provider-QA recipes with 6fbd9704: unchanged.
- Compare applied migrations 20261021113432 and 20261021202420 with actual main:
  byte-identical. No hosted SQL or migration history change. The four customer
  migrations remain unapplied; automatic Git deployments remain disabled.

## Verification

Pinned runtime: `../txr1101-runtime/bin/python`.

- `-m unittest discover -s tests -p 'test_pwa*.py'`: 69 passed.
- Affected companion/readiness/partner directory and placement/listing/API/
  provider-QA modules: 148 tests passed, seven private-source opt-in skips.
- With exact HOF_TXR1101_SOURCE, HOF_TXR1102_SOURCE and rental source directory,
  the four listing/lease provider-QA and lease-disclosure modules: 37 passed,
  no skips. This overlaps the preceding tests; counts are not additive.
- Whitespace and conflict-marker checks clean. No PDF field geometry changed,
  so no replacement invitation was created and prior source visual evidence
  is not redundantly repeated.
- Existing SignWell tabs for both lease QA roles were read directly: each
  remains at Final Step / Agree & Finish. Neither final action was clicked.
  The outstanding packet-specific electronic-disclosure consent is unchanged.

This is a locally tested integration checkpoint, not a full current regression,
completed-signature visual pass, or customer release. The older 3,029-test
result applies to 8efaf936 only. Run the full suite at the actual release freeze.

## Remaining critical path

Finalize the already-sent fictional QA packets with the required specific
consent, download and inspect their actual completed PDFs, then coordinate the
four customer migrations with the verified application release and canonical
customer-flow checks. Do not resend existing packets or equate green local
tests with provider completion. No preview, deployment, usage poll, third-party
message, real transaction or billing change was performed in this batch.
