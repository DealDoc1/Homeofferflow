# Repair instruction overflow — September 18, 2026

## Defect

Paragraph 7D(2) previously shrank long repair instructions into two blanks and
then discarded the remaining words, replacing them with `...`. The interview
review could therefore show obligations absent from the generated packet.

## Local implementation

- Preserve the existing two-line layout for descriptions that fit completely.
- Otherwise put a readable reference in 7D(2) and append the user's full repair
  description as one or more clearly identified continuation pages.
- Copy the user's terms without drafting, summarizing, or adding obligations.
  Treat markup as literal text and wrap long unbroken words.
- Repeat the paragraph heading and property address on every continuation page.
- Keep existing core and addendum signature page numbers unchanged. Append
  continuation pages before the adapter's Paragraph 4 forms and user uploads;
  their existing relative-position calculations keep their fields on their own
  pages.
- Add required Buyer initials on every continuation page. Existing Seller
  recipients also receive initials there, but Buyer-only packets gain no new
  recipients or Seller invitations.
- Explicit As Is choices ignore stale repair descriptions. Text-only legacy
  drafts retain the repair election and continuation when needed.
- Keep production and staging renderer copies identical through a shared helper.

## Evidence

- Nine new real-adapter tests pass: short text, long text including the final
  requirement, 150-item multi-page descriptions, As Is aliases, legacy drafts,
  unchanged addendum fields, existing Seller fields, literal markup/900-character
  tokens, and uploaded-document page ownership.
- Full local suite: **2,049 tests; 2,047 pass, 2 fail in 20.750 seconds**.
  The only failures remain the two existing TXR-1507 approved-map comparisons:
  `test_every_current_map_matches_the_source_calibrated_baseline` and
  `test_current_released_maps_match_the_approved_baseline`. Their approved
  references were deliberately not rewritten for the unverified TXR-1507
  candidate. This is not an all-green release.
- Synthetic unsigned packets generated with
  `scripts/qa/repair_continuation_preview.py`. Paragraph 7D(2)'s reference and
  selected repair checkbox visually inspected at page 5; final one-page and
  two-page continuation examples rendered with Poppler and visually inspected.
  All example terms, including the last requirement, are visible without
  overlapping the header or initials lines. The PDF skill required this separate
  visual check rather than treating extracted text as sufficient.
- Independent local field bounds assert the entire initials rectangles remain
  above their printed rules. These are not completed SignWell signature checks.
- `git diff --check` passes. Existing source forms and existing signature maps
  were not edited by this change.

## Release and remaining QA

Local candidate only: no push, deployment, provider request, email, or customer
packet replacement. No Vercel build/preview usage. Browser integration,
completed-provider initials placement, and production behavior are unverified.
The new continuation layout uses the renderer's existing Helvetica font support;
the tests above do not establish support for every Unicode writing system.

TXR-1507 remains the immediate customer incident. The last observed SignWell
login attempt reached Google's passkey verification prompt. The supplied signed
client agreement is unchanged; no client resend is authorized by this QA work.

Include this work in the next daily report as locally implemented and tested,
not deployed and not revenue-validated. Broader repair/special-provision overflow
outside Paragraph 7D(2) remains separate work.
