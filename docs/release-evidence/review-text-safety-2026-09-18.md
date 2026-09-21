# Offer review text safety — September 18, 2026

## Implemented locally

The purchase-interview review summary interpolated several user-controlled
values into HTML without escaping. Names, contact details, property text,
time periods, brokerage details, and uploaded PDF filenames now render as text
through the existing global `escapeAttr` helper. Escaping is display-only:
the offer data, legal text, PDF inputs, and signing recipients are unchanged.
Description shortening happens before escaping so it cannot split an entity.
Existing empty-value markup, currency formatting, and addendum badges remain.

The attachment list and missing-file notice called `escapeHtml`, but that
helper exists only inside the profile-completion script's private closure.
Those callers now use the available global helper. This fixes the corresponding
ReferenceError as well as preserving safe quoted accessibility labels.

## Evidence

- 30 actual-function Node checks pass: 25 review fields, attachment rendering,
  missing-file notices, Unicode/punctuation/literal entities, description
  truncation, and existing presentation formatting.
- Baseline `403b3924` fails the buyer-name escaping check and raises the expected
  missing-helper ReferenceError for uploaded/missing attachment rendering.
- Updated two existing runtime harnesses to load the real helper instead of
  relying on missing or identity-only formatting stubs.
- Full local suite: **2,032 tests pass in 18.218 seconds**.
- All 45 inline JavaScript blocks parse; `git diff --check` passes.

These are isolated runtime/template checks, not an authenticated browser
end-to-end or production security audit. No claim is made that unrelated page
renderers have all been reviewed.

## Release and cost

Local only; no push, preview, deployment, customer email, or production data
change. No Vercel deployment usage incurred. Intended benefit is a trustworthy,
readable offer review and a working attachment list. No production UX or
revenue impact measured before release. Include this work in the next daily
report, not the September 18 08:00 cutoff window.
