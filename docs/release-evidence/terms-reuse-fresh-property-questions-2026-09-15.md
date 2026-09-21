# Reuse preferences without copying property facts

Status: locally implemented and tested; not deployed or browser-verified.

## Customer outcome

`Reuse terms` retains financing type, loan duration/rate/cost preferences,
buyer approval period, title payer/amendment, survey election, and warranty
preference. It no longer preanswers HOA, seller disclosure receipt, year-built
lead questions, lead disclosure receipt, sale contingency, backup offer,
appraisal election, or as-is/repair election for a different buyer/property.
These questions remain in the existing interview to be answered again.

The prior source offer is unchanged. Client/property identifiers, amounts,
dates, attachments, signing artifacts, and IABS attachment election remain
excluded from the new terms-only draft. Resume and Duplicate & edit code are
unchanged. Dashboard explanations and the new-draft status describe the more
precise behavior without internal terms such as "terms-only start".

## Verification

Baseline: `cab7a346`.

- Saved-offer runtime suite: 30 passing cases, including six new cases across
  agent, investor, and homebuyer roles. These execute actual reuse, resume,
  hydration, and visibility functions with mocked DOM/provider boundaries.
- New cases verify retained preferences, unanswered property questions,
  cleared prior field contents, hidden obsolete follow-ups, cleared attachment
  context, source immutability, and unchanged resume behavior.
- Against the baseline: three reuse failures reproduced; 27 controls passed.
- Updated allow-list and customer-copy assertions match the intended behavior.
- Full suite: 1,997 passed in 16.204 seconds. Expected invalid-fixture PDF
  diagnostic after `OK` is not a test failure.
- All 45 inline scripts parse; `git diff --check` passes.

Supabase guidance informed preservation of the existing ownership-scoped read
and account-change checks. No query shape, authorization policy, SDK, or schema
was modified. Documentation reviewed:
https://supabase.com/changelog
https://supabase.com/docs/reference/javascript/using-modifiers-maybesingle
The markdown changelog endpoint was unavailable; its HTML version was used.

## Release limits

No live database or authenticated browser pass was performed. These tests do
not establish end-to-end production behavior. No customer messages, signatures,
documents, payments, or external settings changed. No GitHub publication or
Vercel build/preview/deployment started; no dependency or recurring cost added.
Include in the daily report as locally tested and awaiting release, not live.
