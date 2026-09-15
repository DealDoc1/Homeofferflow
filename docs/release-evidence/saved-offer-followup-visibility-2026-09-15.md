# Saved-offer follow-up visibility

Status: locally implemented and tested; not deployed or browser-verified.

## Customer outcome

The shared conditional-section restore function now restores visibility for
personal-property details, lead-disclosure follow-ups, dollar/percentage
broker-fee fields, and the existing buyer-agent note. Previously these relied
on clicking a selection card again; loading saved answers alone could leave
the required follow-up fields hidden or retain another offer's visible panel.

Visibility follows the current radio selections. Blank and negative choices
hide the corresponding panels; affirmative choices reveal their existing
fields without rewriting their answers or choosing new transaction terms.
Lead year-built `unknown` follows the same existing presentation as the
interactive selection handler. No legal content or document rules changed.

## Verification

Baseline: `e161e46d`.

- Saved-offer runtime suite: 24 passing cases, including 19 new cases.
- Against the baseline: 18 failures reproduced, six positive controls passed.
- Cases execute the actual hydration, resume, and conditional restore
  functions with mocked DOM/provider boundaries. Agent, investor, and
  homebuyer offer resumes are covered, including switching between different
  saved answers. Existing financing, HOA, sale contingency, backup offer,
  repairs, disclosure delivery, concessions, warranty, and second-buyer
  sections retain their visibility behavior in a positive control.
- Full suite: 1,997 passed in 15.993 seconds. The invalid fixture PDF diagnostic
  after `OK` is expected negative-case output, not a failing test.
- All 45 inline scripts parse; `git diff --check` passes.
- Existing daily report automation was read and remains ACTIVE at 08:00.
  No duplicate automation created and no scheduling settings changed.

## Release limits

These are local runtime checks, not a visual browser or production pass.
No customer data, messages, signatures, documents, payments, authentication,
database policies, or external settings changed. No GitHub push or Vercel
build/preview/deployment was started; no dependency or recurring cost added.
Include in the daily report as locally tested and awaiting release, not live.
