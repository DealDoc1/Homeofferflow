# Preserve Unknown answers on Yes/No-only disclosure questions

## Bounded continuation

Outcome: an Unknown answer survives the actual PDF without a false Yes/No
selection or an unsupported U on the printed line. Scope: the existing
disclosure renderer, continuation notes, interview hint and QA helper/tests.
No source artwork, signature geometry, API permission, price or new customer
step. Production remains e15c5db / READY
dpl_47tztcZ7rgRmvVYvdCdLUubDpBSz, canonical v102 independently checked today.
This local candidate follows source-layout checkpoint c9ce79b.

## Source fidelity and behavior

Read all six supplied source pages. TREC-55-1 item rows permit Y/N/U and its
condition-awareness/smoke-detector questions have actual Unknown checkboxes;
TREC-61-0 groundwater-district question also has an Unknown checkbox. Those
answers remain in their existing source positions. Sixty-two other main-form
questions and six water questions offer only Yes/No. Existing Unknown answers
for those questions now append a section/question-labeled entry reading:
"Seller's answer: Unknown. The Yes/No answer on the form is blank."

The renderer copies inputs; saved answers and delivery metadata are not
mutated. It does not infer No from uncertainty or interpret seller facts.
Canonical Unknown also suppresses old affirmative checkbox aliases. Older U,
u and Unknown spellings are retained. Yes, No, true, false and blank cases do
not add Unknown pages. Existing source-provided Unknown marks still work.

The combined packet keeps main pages 1-4 and water pages 5-6, then appends the
details with initials for every actual Seller and Buyer, including one-Seller
listing-stage cases with no Buyers. No extra signer or required source file is
introduced. Current render revision is now
seller-disclosure-unknown-preservation-2026-10-16-v3, so earlier-layout review
evidence does not approve this changed rendering.

## Verification

- 93 affected tests passed in 1.805s: actual renderer across all 68 affected
  keys, Yes/No/blank preservation, valid source Unknown choices, legacy aliases,
  immutable inputs, save/reopen, revision-bound reviews, API/send boundary,
  execution geometry and the actual-source interview runtime.
- Four fictional source-backed specimens generated locally, nothing sent.
  Changed Unknown source pages 2-6 and attached page 7 visually inspected.
  The actual printed Unknown boxes remain checked; unsupported Yes/No answers
  and flood extent are unselected. All eight selected Unknown answers appear
  on the attached page, with legible section labels and all four initials.
- Ordinary, single-Seller and Unicode cases have exactly unchanged extracted
  source/continuation text and signing-field arrays compared with yesterday's
  visually reviewed specimens. Unknown handling adds no ordinary-case pages.
- Artifacts: /private/tmp/hof-disclosure-unknown-20261016/manifest.json and
  fictional specimen PDFs/PNGs. They are QA artifacts, not executed agreements.
- Final frozen full regression: 2,683 tests, 95.239s, OK, one environment skip;
  process exited zero. Log: /private/tmp/hof-disclosure-unknown-full-20261016.log.
  Whitespace passed. No new dependency, build, hosted branch, production SQL,
  provider request, email, charge or customer-record mutation.

## Remaining release evidence

Not deployed or completed-provider verified. Conditional-question clarity and
the integrated seller-review/signature/completed-PDF pass remain unfinished.
Ship the accumulated candidate's review-version migration and API together;
do not release this renderer alone or call a QA-field overlay a real signature.
