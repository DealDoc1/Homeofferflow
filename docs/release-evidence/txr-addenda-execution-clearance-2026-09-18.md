# TXR addenda execution-copy corrections - September 18

## Status and scope

Local corrections only. Not deployed, not approved-map changes, and not
completed-provider signature evidence. While inspecting combined-packet gaps,
the first layout defect found was draft names printed inside signature fields.
Corrected that boundary before adding these forms to combined offer packets.
Their standalone-to-combined integration remains unfinished.

## Findings and changes

- TXR-1905, 1914, 1917, 1919, and 1948 ignored the server-owned `_for_signing`
  flag and drew review-only names into execution areas. Across the five forms,
  18 of 20 tested signature rectangles intersected printed name characters.
  Signing copies now omit these draft labels. Unsigned review copies still
  display them; parties, recipient IDs, signer counts, and widget geometry
  are unchanged. The actual send route already passes `_for_signing=True`.
- TXR-1917 X marks were above the source checkbox cells. Moved their baselines
  to 540, 502.3, and 436.7 PDF points. The deadline formerly started at x=121,
  on the printed word "days" instead of the x=90.30..120.66 blank. It now
  starts at x=97, y=377. Property text moved above its rule, to y=604.
- The supplied TXR-1948 source has 11 interactive fields using the same
  canonical/widget objects. The old page-copy plus static-overlay path left
  form values blank and lost the canonical field tree. The corrected path
  clones the document and fills canonical text/checkbox values and appearances;
  inactive election amounts are cleared. Signature fields remain unsigned.
  Static library sources retain the existing overlay fallback. Ambiguous
  editable field structures or nonempty source signatures are rejected.
- Added render revisions to internal signing metadata and request fingerprints
  for these five forms. A prior provider document must not be mistaken for the
  corrected render merely because its signer coordinates match. This does not
  create a user approval requirement or modify an existing provider document.

## Evidence

- The initial two regression methods produced 38 failing subcases: 20
  signing-copy name checks and 18 measured name/field intersections. Both
  methods passed after the correction, across one/two buyers and sellers.
- Every non-name term remains identical between draft and signing overlays;
  signer maps remain identical. All three environmental X rectangles and a
  three-digit deadline fit independently measured source blanks.
- Reopened appraisal outputs for all three elections: all 11 canonical fields
  remain; widget and canonical IDs/values agree; each updated widget has a
  nonempty appearance. Re-election clears prior values. Additional tests cover
  malformed field trees and rejection of an executed source.
- The actual render route is exercised with mocked private storage, verifying
  the server-owned signing flag and render revision for all five forms; the
  revision changes the request fingerprint. No provider POST occurs.
- The first focused run passed 36 tests. Full discovery then ran 2,115 tests
  in 35.791 seconds: 2,113 passed; the same two TXR-1507 approved-map baseline
  mismatches remained. This is not an all-green suite. Two further appraisal
  negative/re-election checks were added afterward; the expanded focused run
  passed all 38 tests in 0.430 seconds.
- Used `scripts/qa/txr_addenda_execution_preview.py` against the exact private
  sources, with synthetic parties and source-specific field outlines. Inspected
  every page of the five corrected specimens (seven pages). Execution areas
  are free of the printed party names. The corrected environmental blanks and
  editable appraisal fields are visually legible and correctly selected.
  Outlines are synthetic QA aids, not SignWell signature artwork.

## Remaining work found during visual review

The same specimens expose additional pre-existing non-signature alignment
issues in TXR-1905, 1914, and 1919: several X marks sit above or beside their
source boxes, and some financial numbers sit on source text or rules. These
are concrete local correction tasks, not a request for owner approval and not
an external blocker. Audit their full election matrices next. Do not describe
these forms as fully placement-verified or release-ready based on this pass.

No signing map baseline was refreshed, real customer document changed, signing
invitation sent, live database record altered, public push performed, or Vercel
build/deployment started. QA PDFs remain private and untracked under `tmp/`.
