# TXR-1508 showing-form answer placement - September 18, 2026

Status: **local candidate, not deployed and not newly provider-completed QA**.

## Findings and correction

Read and measured the supplied 02-25-26 blank TXR-1508. The original file was
not modified. Property and customer-name baselines previously touched their
printed underlines. The unbounded text drawing could cover adjacent license or
customer-initials labels. Selecting the associate as the acknowledging signer
did not check the source's associate choice.

The measured source underline rectangles are:

| Answer | Left/right (PDF points) | Top-origin underline top |
| --- | --- | --- |
| Property | 108.02 / 576.09 | 141.38 |
| Broker name | 187.58 / 403.63 | 480.07 |
| Broker license | 475.66 / 559.90 | 480.07 |
| Associate name | 187.58 / 403.63 | 498.79 |
| Associate license | 475.66 / 559.90 | 498.79 |
| Customer 1 | 137.78 / 295.60 | 560.47 |
| Customer 2 | 137.78 / 295.60 | 604.06 |

`lib/txr1508_answers.py` now bounds every answer to those blanks with readable
8-to-7-point fitting and descender clearance. Values that cannot fit are
preserved in full on an attached answer continuation, with a visible reference
in the source blank. Shared Unicode font support prevents silent missing-glyph
substitution. The attachment says Customer and showing form, not Client or a
representation agreement; no service or compensation terms are inferred.

The associate checkbox follows the selected role, and the two existing
representation-status marks fit within their source glyph bounds including
stroke width. The base provider initials/date coordinates are unchanged.
Each appended page receives required initials for exactly the selected
customer(s) and broker or associate. The actual rendered PDF page count is
used by the authenticated send path. Simultaneous invitations remain enabled.

Boundary testing found a trailing shared-layout spacer producing a blank
continuation page. Spacing now occurs only between answer blocks. This also
applies to TXR-1501 and TXR-1507; their render revisions were advanced so a
previously prepared provider request is not silently treated as the new copy.
TXR-1508 render/map revisions were advanced for its new optional pages.

## Verification

- Six new test methods cover independent measured answer bounds, all role and
  representation-status combinations including stroke extents, full long and
  Unicode values, preserved inputs, customer-specific attachment labels,
  no blank trailing page, unchanged base field geometry, invalid page counts,
  and stale prepared-map rejection.
- Offline actual-render/send integration covers broker/associate, one/two
  customers and normal/long answers (eight combinations). Every attachment
  page has the correct required initials; only one source download and one
  mocked send occur. Database/provider calls are test doubles, not live QA.
- 66 focused tests pass using the production-pinned pypdf 4.3.1 library.
- Full bundled-library discovery: **2,239 tests in 51.349s; 2,237 pass, two
  existing approved-map comparison failures**. Approved references were not
  refreshed. This is not an all-green regression or release-readiness claim.
  Log: `/private/tmp/hof-txr1508-answer-suite.log`.
- `scripts/qa/txr1508_answer_preview.py` checks the exact reviewed source hash,
  generates four fake-data specimens and confirms source bytes unchanged.
  All six resulting pages were rendered through Poppler and visually inspected
  under the PDF skill: standard broker (one customer), standard associate
  (two customers), and a long-answer continuation for each role.
- Blue outlines are requested field geometry, not completed SignWell artwork.
  New continuation initials and checkbox/answer changes still need completed
  provider PDF inspection before production-ready claims.

Private specimens stay untracked under `tmp/pdfs/txr1508-answer-review/`.
No source/customer PDF was committed. No push, Vercel build/deployment, email,
provider invitation, signing action, cancellation, replacement, new paid
resource, or database mutation occurred. The release cost/publication hold
remains unchanged. The active roadmap remains incomplete.
