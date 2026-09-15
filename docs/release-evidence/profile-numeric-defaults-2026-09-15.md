# Preserve zero and blank profile defaults

Status: locally implemented and tested; not deployed or browser-verified.

## Customer outcome

- Agent and investor profiles retain explicit zero option fees, option days,
  and earnest money. Saving zero no longer substitutes $250, seven days, or
  an unanswered amount.
- Blank defaults save as null and remain blank when the profile is rendered.
  Example amounts are placeholders, not silently selected answers.
- Negative, fractional, non-finite, invalid, and unsafe-integer inputs receive
  a focused, plain-language error before session refresh or database writes.
  The existing whole-number input scope is retained; cents support is not
  added. Option days respect the existing Postgres integer storage range.
- Saved numeric preferences are treated as intentional answers, so later
  price calculations do not replace them. Unanswered terms can still receive
  the existing calculator suggestions.
- Profile completion indicators recognize zero terms as present.

## Verification

Baseline: `6f6193ab`.

- Profile-default runtime suite: 72 passing cases, including 52 new cases
  executing the actual save, render, default-application, calculator, and
  completion functions with mocked DOM/provider boundaries.
- Against the baseline: 48 failures reproduced; 24 positive controls passed.
- Full suite: 1,997 passed in 16.106 seconds. The fixture diagnostic printed
  after `OK` is expected negative-case output, not a failing test.
- All 45 inline scripts parse; `git diff --check` passes.
- Supabase guidance and the local baseline schema informed validation:
  agent/investor amount fields are nullable numeric; option days is nullable
  integer. No migration or change to ownership filters, alias resolution,
  authentication, or RLS is required.

## Release limits

No live database, authenticated browser, or production verification was run.
No customer messages, documents, signatures, payments, or external settings
were changed. No GitHub push, Vercel build, preview, or deployment was started.
No new dependency or recurring service cost. Record as locally tested in the
daily report, not deployed.
