# Backup-contract layout - September 18, 2026

**Local candidate; not deployed or completed-provider verified.**

## Findings and correction

The current two-page source is TREC 11-9 dated 05-04-2026, SHA-256
`1bc6edd2f69f43ad3d8a1cfd82603a395d7e68b0164170fa5800fbf80d33f832`.
It has no canonical AcroForm fields or page widgets. The original source and
all customer-executed documents remain unchanged.

The previous layout placed Buyer initials above the source's identification
line, let signature/date fields cross the execution rules, and started some
answers well inside their blanks. Explicit numeric zero fees disappeared due
to truthiness checks. Page-two property text also lacked a width bound.

The correction:

- Places one/two Buyer initials within the printed Buyer identification span
  and signatures above their own execution rules. No new Seller recipients
  are added. Existing signature/initial IDs remain stable; unprinted date
  fields are removed.
- Aligns both property headers, fee amounts, delivery days and date components
  to measured source blanks. Keeps readable embedded Unicode text and literal
  markup. Long answers continue intact on an initialed attachment immediately
  after the two source pages; subsequent repair/other continuation offsets
  account for the extra pages.
- Preserves entered zero fees separately from unanswered values, and retains
  all existing answer-key aliases. Valid ISO dates are split into month/day
  and two digits after the source's printed `20`. Invalid dates and years
  outside 2000-2099 fail explicitly instead of producing misleading text.
- Rejects a missing selected source or required signing page, preserves source
  hashing, records a render revision, and synchronizes both renderer copies.

Blank draft dates remain allowed. This is an answer/geometry correction, not
new legal drafting, a date-order/closing-consistency audit, or new approval or
brokerage-seat requirements. The existing interview was not changed this turn.

## Verification and limits

The PDF skill's source inspection and rendered-review workflow was followed.
All seven final Poppler-rendered QA pages were visually reviewed: ordinary
two-Buyer answers, zero-dollar fees with one Buyer, and a long Unicode/literal
markup address across both source pages plus its complete attachment. Blue
rectangles represent signing bounds, not actual signatures. Source rules,
labels, answer text and footer areas remain separate.

Four offline production request cases cover short/long answers and one/two
Buyers. Actual rendering and field-map code run; only delivery is intercepted.
They retain one request, one combined PDF and simultaneous invitations.
Additional checks cover all legacy aliases, explicit zero/blank distinctions,
source geometry, lossless continuations, later repair-page offsets, unsigned
uploaded attachments, source hashes, revision metadata, missing pages and
deselected stale answers. No approved geometry reference was overwritten.

Bundled pypdf 6.10.0: all 49 focused tests pass, including packet bounds,
source audit and renderer synchronization. The first production-pinned run
exposed two test-extraction assumptions: spatial extraction interleaves the
source's printed underscores with overlay text, and a nine-point font can be
reported with floating-point rounding. The assertions now use content-order
text plus a font-size tolerance, while keeping rendered and coordinate checks.
The final production-pinned pypdf 4.3.1 full suite ran 2,295 tests in 60.359
seconds: 2,293 pass, with only the same two pre-existing approved-geometry
reference failures. Log: `/private/tmp/hof-backup-contract-final-suite.log`.

No customer send, signature, cancellation/replacement, database mutation,
public push or Vercel build/deployment occurred. Private QA artifacts remain
ignored under `tmp/pdfs/backup-contract-review/`. Existing production cost and
coordinated-release constraints remain unchanged. This is not full interview
browser QA, whole-packet visual approval or completed-provider verification.
