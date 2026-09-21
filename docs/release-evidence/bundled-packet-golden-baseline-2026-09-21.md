# Bundled packet golden-baseline approval - September 21, 2026

## Scope

GitHub Actions run `35624088266` passed the complete 2,333-test unit suite,
then stopped at the separate golden-packet guard because the approved manifest
still described execution fields removed or corrected by the reviewed addendum
layout work in this release candidate.

The structural differences were limited to these intentional changes:

- remove date widgets where the official addenda do not print a date line;
- place Buyer signatures across the actual printed Buyer signature rules; and
- enlarge and align the financing and backup-contract initials widgets to the
  printed footer blanks.

The affected forms are the third-party-financing, appraisal, HOA,
sale-of-other-property, and backup-contract addenda. Packet page counts are
unchanged.

## Visual review

A fresh 20-page `all_supported_addenda` packet was rendered from the exact
release-candidate code with two buyers. The corrected signing rectangles were
overlaid on pages 13, 14, 15, 17, 18, 19, and 20 and visually inspected at
source-page resolution.

- Both buyers' financing initials stay inside the printed Buyer footer blanks.
- Both financing signatures stay on the two printed Buyer rules.
- Both appraisal, HOA, and sale-contingency signatures stay on their printed
  Buyer rules without covering labels, seller lines, or form text.
- Both backup-contract initials stay inside the printed Buyer footer blanks,
  and both signatures stay on the two printed Buyer rules.
- No replacement date fields were added because these execution rows do not
  contain printed date lines.

The one-buyer conventional-financing scenario was also rendered independently
and inspected on both addendum pages. Its initials and signature use the same
approved source locations.

## Verification

After visual approval, `tests/fixtures/golden_packet_rendering.json` was
regenerated from all 12 controlled packet scenarios. The exact CI command now
passes locally:

`scripts/check_golden_packet_rendering.py --cross-platform`

The refreshed manifest stores only page fingerprints and privacy-safe signing
geometry. No customer PDF, name, email, address, credential, or private source
document is committed.

No SignWell request, customer email, database change, Vercel build, or
production deployment occurred during this correction.
