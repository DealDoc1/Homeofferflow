# Lease listing agreement — source-backed local preparation

## Outcome and scope

Implemented the TXR-1102 answer contract, exact-source renderer and explicit
signing map on `codex/lease-listing-package`, starting from the reconciled
listing checkpoint `699cec16`. This is a component checkpoint, NOT a deployed
lease-listing interview or an end-to-end completed transaction.

Production remains PR #1354 / `bfd03d99` / shell v112. The separate sale-listing
branch remains at `699cec16`; its existing ordinary provider test is unchanged.
No existing signing question was re-asked, invitation created, email sent,
source uploaded, migration applied, permission changed or deployment made.
Automatic Git deployments remain disabled; no Vercel usage check or preview.

## Exact source and rendering

Uses the already downloaded private English 01-05-26 TXR-1102 source, all eleven
Letter pages, SHA256
`30ae702ee94d71fc2aec5717f0d1b6d78b4fea53b5b418f7d74b39f658e44657`.
The file stays outside Git. Wrong-source bytes are rejected before parsing.
The source has no native AcroForm fields/widgets; overlays are source-specific.
All legal/copyright wording is retained. Only the two exact supplier-imprint
text operands are removed through the existing validated footer helper; the
original downloaded source is never edited.

Validation covers the two mutually exclusive compensation sections, other-
broker share, renewal/sale fees, listing dates, monthly rent and lease-term
bounds, MLS instructions, make-ready authority, property exceptions and
optional rental marketing preferences. No fees or factual answers are inferred.
Rates on one month's rent are not arbitrarily capped at one month. Monetary
precision, booleans, exponents, stale hidden branch values and unknown input
keys are checked. Explicit zero stays distinct from blank.

Unknown construction year is retained as unknown; it cannot silently suppress
the requested lead document. Selection is a request, not proof an addendum was
attached. The future package adapter must report included and pending files
truthfully and must not substitute the purchase lead form for a rental form.

Long/Unicode answers are preserved in a referenced continuation with readable,
paragraph-specific labels. Other-document answers and long property context
are not duplicated unnecessarily. Broker license 9010832 fills an otherwise
blank OnDemand Realty license. Contact snapshots remain explicit. Broker-only
execution does not fill an unused associate identity or second landlord row.

## Actual checks completed

- 16 lease-specific methods passed using the actual private source opt-in.
- Latest affected suite: 51 methods, two unrelated source opt-in skips,
  1.391 seconds, exit zero. Includes unchanged sale-listing and packet helpers.
- Ordinary local proof: 11 pages, two landlords/associate, 39 planned fields.
- Single-landlord/broker proof: 11 pages, 26 fields, no rental preferences or
  unused landlord/associate fields.
- Long/Unicode proof: 16 pages, 54 fields, full source plus five continuation
  pages. No truncation or replacement of Unknown with No.
- Reviewed all eleven ordinary source/output pages; the broker-only
  compensation, no-intermediary, no-make-ready and execution differences;
  and long/Unicode property, fee, MLS, make-ready, preference, execution and
  all five continuation pages.
- Visual review caught signature/date boxes touching printed-name labels and
  a replacement percentage crowding its percent sign. Corrected both. An
  actual-source test now checks all execution rectangles against every printed
  source character; a targeted test locks the narrow percentage placement.
- Dates use MM/DD/YYYY with lock_sign_date; one/two landlords and explicit
  broker/associate roles are tested. All initials include their correct source
  or continuation page; all field IDs and page/box bounds are checked.
- Local proofs contain obvious fictional labels, watermark and placement
  guides. These are NOT actual completed SignWell PDFs or client examples.

Read-only source and placement PNGs plus the three technical proof PDFs are in
the chat output folder `lease-listing-2026-10-20/`. Do not email the stress proof
to the owner or a client or present it as the normal user experience.

Poppler initially hit the bundled machine's missing/default fontconfig cache
paths. That run was interrupted and terminated; a private output-folder
fontconfig resolved it without changing system settings. Final renders use that
configuration. Apparent repeated-header omissions in image presentation were
checked against raster data: all five continuation header regions are pixel-
identical to the fully reviewed first continuation, with 1,709 dark pixels.
Footer placement outlines are present on every source-page raster.

The PDF authoring marker was run successfully once for the three local proofs.
No full regression/CI/release loop was repeated for this unconnected component;
the complete reconciled parent passed 2,932 tests in the preceding checkpoint.

## Next implementation, not an owner blocker

Wire the lease-specific model into the existing owner-authenticated draft,
preview, recipient confirmation and same-request retry APIs. Add one simple,
conditional lease-listing interview to the existing transaction choice, with
Google completion on addresses and metadata-only saved drafts. Reuse the
existing related-document package pattern while distinguishing actual rental
sources from purchase sources; do not claim requested files are included.
Then complete the schema/API/browser and customer-shaped provider checks and
one coordinated release. No source-owner, brokerage-seat or additional blanket
approval requirement is introduced. Do not mix unfinished lease activation into
the separate sale-listing release.

Reproduce focused checks with `HOF_TXR1102_SOURCE` pointing to the private
source and `../txr1101-runtime/bin/python -m unittest tests.test_txr_1102
tests.test_txr_1101 tests.test_listing_packet -q`. Local layout proof generator:
`scripts/qa/prepare_txr1102_layout.py --source <private PDF> --output <QA folder>`.
No provider or cloud credentials are accepted by that generator.
