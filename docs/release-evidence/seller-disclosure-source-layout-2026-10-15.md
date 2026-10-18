# Seller disclosure source-layout checkpoint

## Outcome and scope

Prepared October 15, checkpointed October 16. Existing TREC-55-1/TREC-61-0
interview, answer renderer and signing geometry only. No new agent-access
requirement, pricing, source artwork, invitation or production mutation.
Production independently remains e15c5db / READY
dpl_47tztcZ7rgRmvVYvdCdLUubDpBSz on October 16; canonical source serves v102.
Candidate v103 is local and must ship with its review-version migration/API.

## Corrected locally

- Centered item and defect answers on measured source lines; corrected wrapped
  fireplace, roof/structural, flood-area and additional-disclosure row spacing.
- Six-point checkbox marks stay inside printed source boxes. Canonical No and
  actual false values override old affirmative aliases. Ambiguous legacy
  multiple-choice selections are not silently converted into one answer.
- Added saved occupancy duration, roof type/age, structural details, well counts
  including zero, flood-area extent and well ownership. Existing JSON fields
  carry these answers; no extra columns are required for this layout slice.
- Repeated property address on every source page, retaining long/Unicode text
  on bounded continuation pages. Written facts are never cropped or interpreted.
- Corrected main Buyer and water Seller/Buyer signature rows and water-date
  width against independently measured source rules. Added page-one water
  initials for all actual parties; merged packet offsets remain correct.
- Updated render revision to seller-disclosure-source-layout-2026-10-15-v2 so
  previous-layout reviews and provider fingerprints do not approve this layout.

## Evidence

- Final focused regression: 76 tests, 1.187s, OK. Log:
  /private/tmp/hof-disclosure-layout-focused-final.log.
- Final frozen full regression: 2,677 tests, 88.764s, OK, one environment skip.
  Log: /private/tmp/hof-disclosure-layout-full-20261015.log. No full rerun was
  needed to record this unchanged checkpoint. Whitespace passed October 16.
- Three fictional source-backed specimens: one Seller; two Sellers/two Buyers
  plus water; long/Unicode overflow. Final changed pages visually checked:
  ordinary 3/4/6, single-Seller 1/3/4/5, Unicode 2/3/5/7. Other ordinary pages
  were unchanged from the earlier inspected render. No real customer packet.
- Actual interview source checked at 390 and 1280px using a local-only fixture;
  saved No, roof/occupancy values, zero well count, ownership and flood extent
  survived reopening. No horizontal overflow. Screenshots and specimen manifest
  remain under /private/tmp/hof-disclosure-layout-20261015 and the matching
  hof-disclosure-layout-phone/desktop-20261015.png files.
- Previous committed head 7598e4e independently passed GitHub Actions
  38773482696. That is previous-head CI, not independent proof of this layout.

## Remaining

Not deployed, not a completed-provider pass. Small water initials, corrected
signature/date widgets and continuations still need actual SignWell completed
PDF review. Existing Unknown selections for printed Yes/No-only questions need
lossless handling before this disclosure release; do not infer No or silently
drop those saved answers. Conditional-question cleanup remains in progress.
Source PDFs and all previous customer/signing artifacts are unchanged.
