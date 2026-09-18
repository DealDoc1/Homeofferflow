# Complete non-realty inventories - September 18, 2026

## Local correction

The generated TREC 57-0 addendum previously limited the item description to
three lines. The review screen's separate full-text fix did not correct this
PDF truncation. The renderer now uses all eleven measured description blanks
at a readable nine-point font. When the complete inventory cannot fit, it puts
a clear continuation reference on the form and copies the entire inventory to
labeled continuation pages. It does not summarize or draft the entered terms.

The source rules span PDF x=64.5 through 567.0. Their top-origin y positions are
248.72, 267.56, 286.41, 305.25, 324.09, 342.94, 361.78, 380.63, 399.47,
418.31, and 436.69. The source PDF is unchanged and is not part of this commit.

Explicit numeric zero consideration is preserved, separately from a blank
amount. Selected non-realty addenda with a missing source now fail clearly for
both short and overflowing inventories instead of silently omitting the form.

Continuation pages follow existing generated addenda and any repair
continuation. Existing signature fields retain their pages and coordinates.
New inventory pages receive buyer initials; seller initials are added only
for already included seller recipients. This does not invite new recipients.

## Verification

- Eleven new regression tests exercise eleven-line fit, overflow, 120 items,
  long serial-number-like tokens, literal markup, deselection, legacy aliases,
  repair/inventory/upload page offsets, existing seller recipients, missing
  source files, and zero versus blank consideration.
- The inventory, repair, and renderer-sync suites pass all 22 checks.
- Full local discovery ran 2,060 tests in 20.168 seconds: 2,058 pass and two
  fail. The failures are the unchanged TXR-1507 approved-map reference checks
  (`test_every_current_map_matches_the_source_calibrated_baseline` and
  `test_current_released_maps_match_the_approved_baseline`). This is not an
  all-green release result. The reference maps were not rewritten to hide it.
- The PDF skill's visual review covered seven rendered pages from three local
  synthetic unsigned examples: all eleven blanks; a 70-item, two-page
  continuation; and a packet combining separate repair and item continuations.
  Text, repeated property identification, references, and footer rules are
  legible and clear of printed labels. These are not completed SignWell PDFs.
- Shared continuation layout preserves the existing Helvetica font behavior;
  this is not a claim of comprehensive Unicode script support.
- No real client file was modified or used as a generated specimen.

## Release status

Local implementation only. No Git push, deployment, Vercel build/preview,
provider send, customer email, or production database action occurred.
Fresh completed-provider visual QA for the new continuation initials remains
unverified. The separate TXR-1507 placement correction remains pending its own
completed-provider verification; its approved reference maps are unchanged.

Include in the next daily report as local work, not deployed functionality or
measured revenue/conversion improvement.
