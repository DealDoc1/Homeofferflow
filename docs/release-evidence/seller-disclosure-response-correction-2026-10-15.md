# Seller disclosure response-letter correction

## Batch contract

- Outcome: preserve the Seller's Yes/No/Unknown answers on every affected
  TREC-55-1 feature line instead of turning all nonempty values into a check.
- Scope: 17 page-one response lines and their older aliases; source-specific
  glyph placement, regression and two fictional unsigned specimens. No
  execution widgets, parties, source artwork, pricing, permissions or schema.
- Production baseline: e15c5db / READY dpl_47tztcZ7rgRmvVYvdCdLUubDpBSz.
- Cost: local rendering/testing only; no Vercel preview, provider invitation,
  reminder, real client packet or extra paid service.
- Evidence: actual-render failing reproduction, correct Y/N/U/boolean/alias
  behavior, independent source-rule measurements, changed-page visual review
  and frozen-candidate regression. Completed-provider review stays separate.

## Inventory and reproduced defect

- Focused Gmail subject search found no seller-disclosure or 55-1 invitation.
  An earlier broad body search found existing test completions, not evidence
  of a seller-disclosure signing run. Do not inspect real client packets or
  create duplicate invitations based on the broad results.
- Text inventory of the unchanged 32-page test composite found no 55-1/61-0
  component. Its purchase form mentions a Seller's Disclosure Notice, which
  is not an actual disclosure component or signing-QA pass.
- The current UI submits Y, N and U for the 17 feature choices. The renderer
  used `if values.get(key): _check(...)`, so N and U produced the same mark as
  Y. Legacy False was discarded, and alias/canonical values could overprint.
- New real-render tests failed on the previous implementation, including
  canonical precedence, both booleans, six older aliases and all Y/N/U cases.
  Test-only blank paper avoids putting source artwork into the repository.

## Correction and visual evidence

- Use the existing letter renderer for all 17 feature lines. Exact canonical
  values take precedence over aliases. Empty stays empty; actual booleans
  normalize to Y/N without treating a nonempty N/U as affirmative.
- The initial corrected-letter render exposed old source anchors outside
  their response rules. Independently measured every affected horizontal
  rule in the original 05-04-2026 PDF; recentered the glyphs 2–3 points above
  those rules. Alias and canonical maps agree. No signature rectangle moves.
- Original supplied source SHA-256 remains
  65a52e167c290814930624ba230e232c152573359f1388cdb5e1237a62e4239a.
- Two fictional unsigned four-page specimens: all 17 No, and mixed Y/N/U.
  Page one of each was rendered and visually inspected after the final
  calibration. All answer letters fit their individual rules without
  covering adjacent labels. No other response, source page, signer or
  continuation logic changes. No complete disclosure or signed PDF is claimed.
- Specimens and manifest: /private/tmp/hof-disclosure-responses-20261015/.
  The prepare-only helper is scripts/qa/check_seller_disclosure_responses.py.
- Complete execution-widget fingerprint for both forms and all twelve
  Seller/Buyer-count combinations matches the deployed baseline:
  4b9bcc58cfecdfaacbdc8c6ef9a1e69727d6d7daa6f94cc25be84f44a4815610.
- An initial Poppler call omitted the known task-local Fontconfig setting and
  produced excessive cache warnings. It completed; subsequent renders used
  FONTCONFIG_FILE=/private/tmp/hof-fontconfig-qa.conf with redirected logs,
  succeeded and were visually reviewed. No system/font permissions changed.

## Verification and release boundary

The intermediate response-only candidate passed 2,653 tests in 85.972s, one
environment skip. Visual review then required anchor calibration, so that
result is not the final calibrated-candidate proof. Final focused suite:
73 tests in 0.625s, OK. Final full suite: 2,655 tests in 84.801s, OK with one
environment skip. Whitespace passed. The existing negative-fixture diagnostic
after `OK` is intentional, not a failed test.

This correction is local, not deployed and not a completed-provider pass.
The broader seller-disclosure end-to-end review still lacks its completed
provider specimen. Preserve that partial status and the existing release
evidence requirements rather than converting local rendering into an asserted
signing pass. Do not bypass the release preflight or reuse another form's
signed PDF as evidence for this disclosure.

The audit also identified unimplemented narrative/explanation coverage in
the disclosure experience. That needs its own complete interview-to-PDF
implementation; a correct feature-letter page is not the entire seller suite.
