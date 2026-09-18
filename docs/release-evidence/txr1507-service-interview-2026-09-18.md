# TXR-1507 service-level interview - September 18, 2026

**Local candidate; not deployed or live-provider verified.**

## Finding

The supplied short form's Showing Services choice expressly states that
paragraphs 6, 7 and 8 do not apply. The interview nevertheless displayed and
required purchase/lease compensation and an intermediary decision, and the
renderer printed those values even when Showing Services was selected. This
could block an otherwise complete showing-only draft and produce confusing
irrelevant values on the agreement.

## Change

- Full Services displays compensation and intermediary questions; Showing
  Services displays only its showing fee among those service-specific terms.
  Common party, market-area, term and signer questions remain unchanged.
- Hidden controls are disabled, so native FormData omits their values. Switching
  back restores answers still in the open dialog; no destructive clearing occurs.
- Server parsing validates only applicable terms. Explicit zero showing fees
  remain valid. Stale hidden values are not persisted, even when an older client
  sends malformed hidden input. Applicable required questions remain required.
- The renderer also ignores stale compensation/intermediary answers in legacy
  showing-only drafts. Source wording is unchanged and no compensation is
  inferred. Existing client documents and database records are not modified.
- A render revision binds this content change to tracked signing attempts:
  `txr-1507-2026-09-18-service-terms-v1`. Base signature geometry is unchanged.

## Verification

- 62 focused Python test methods pass, including the draft-submission runtime
  suite. Six new tests cover service-specific parsing, hidden-value handling,
  explicit zero fee, required applicable terms and legacy PDF behavior.
- Three parser regressions fail against the preceding committed code with
  unnecessary hidden-answer validation errors; they pass after the correction.
- A real headless browser runs the actual extracted dialog and its style block,
  with synthetic authentication/source and a mocked save. All page network
  requests are blocked. It verifies both choice directions, preserved answers,
  disabled/required states, native form validation and exact saved payload.
- Browser verification at 390px includes reaching the submit button without
  horizontal scrolling. Mobile top/bottom and desktop screenshots were viewed.
  This is an isolated dialog check, not authenticated production end-to-end QA.
- Four rendered source-PDF pages were visually reviewed: both pages for Full
  Services and both for Showing Services. The latter shows only its showing fee,
  with no added compensation amounts or intermediary selection. The PDF skill
  provided the render-and-inspect workflow rather than text-only validation.
- Full discovery: 2,211 tests in 50.370 seconds; 2,209 pass and the same two
  signing-map approved-reference comparisons fail. No baseline was regenerated.
  Log: `/private/tmp/hof-txr1507-services-suite.log`.

The agent-browser CLI specified by the browser skill was unavailable. Bundled
Playwright ran an isolated headless Chrome instance instead; it closed in a
finally block. No user Chrome profile or existing tab was accessed.

Private outputs: `tmp/qa/txr1507-services/` and
`tmp/pdfs/txr1507-services-review/`. No customer data or source PDF is committed.
No push, deployment, build, live provider call, customer email, database mutation,
paid test or new resource occurred. Production release and completed-provider QA
remain outstanding; no new customer-facing approval or brokerage seat is added.
