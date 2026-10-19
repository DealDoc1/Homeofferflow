# Normal seller questionnaire and PDF access

## Batch contract

Outcome: verify one ordinary seller can edit saved answers, obtain a complete
disclosure and reach confirmation without the prior multi-case QA bundle.
Scope: existing seller review page and questionnaire script; localhost fixture
uses the actual API renderer with isolated source reads. Production baseline
remains `61e516d0` / shell v106; this candidate reserves v107. No Vercel build,
deployment, subscription, live database mutation, email or invitation.

The previous goal turn made progress: both v4 provider signers were confirmed
complete and all 13 comparison pages were reviewed. That clears the exact
placement test, not ordinary customer-shaped acceptance or the full release.

## Broken boundary and correction

The original ordinary-browser fixture deliberately returned PDF unavailable;
it had not exercised successful saved-answer rendering in the page. Connected
it to the real `_render_seller_disclosure_draft_preview`, while retaining a
separate default unavailable-PDF mode. No external network or credential is
accepted by the renderer bridge; the only source transport is an in-memory,
fictional-host GET. Signing in this fixture now explicitly returns an error,
not a simulated invitation-success claim.

The first successful PDF revealed a usability issue: the embedded viewer was
blank in this browser and there was no independent PDF access. Corrected the
actual customer page, not just the fixture:

- Open disclosure PDF and Download PDF use the same verified current preview.
- Embedded viewing is optional and collapsed, avoiding a large blank panel.
- Questionnaire and legacy review-only paths share this access behavior.
- Edits remove all stale preview sources, revoke the old blob and hide the
  former confirmation. New links are created only after a successful preview.
- Separate-tab viewing uses `noopener noreferrer`; no session storage or new
  provider dependency. The confirmation message is concise and laid out as a
  separate block rather than alongside the button.

## Verification report

Story: local seller interview -> answer save -> actual API/source renderer ->
complete PDF -> browser download and confirmation. This does not simulate or
claim a production database, emailed code or SignWell delivery pass.

| Boundary | Result | Evidence |
| --- | --- | --- |
| UI and input | Local pass | Actual seller HTML/scripts; changed roof age from 8 to 9 years |
| UI to save | Fixture pass | Saved answer is retained for the next render; no external database |
| Saved data to renderer | Actual-renderer pass | Four-page supplied source through real API, isolated source transport |
| Response to browser | Pass after fix | Four-page PDF downloaded via actual visible Download PDF link |
| Confirmation | Fixture pass | Current preview permits confirmation and shows Send for signature; no send attempted |
| Phone layout | Local pass | 390px viewport and document width; no horizontal overflow, blank embed collapsed |
| Database/delivery | Not executed here | Existing isolated PostgreSQL and completed v4 results remain separate evidence |

Focused run: **31 tests passed** in 0.744 seconds with both actual source paths
set, including four-/six-page source output, answer/security boundaries,
legacy review behavior, signing boundaries, interview and handoff wrappers.
The new Node runtime check verifies both preview source forms and invalidation
of all stale links. No full regression was repeated for this unfinished batch.

Viewed all four pages of the actual ordinary PDF: no duplicated execution
pages, stress text, fake signatures or test watermark. It is a fictional,
unsigned example, not a real completed seller disclosure. Only explicit
fixture answers are printed; the real application does not default answers to
No. Edited roof age is present in the downloaded PDF.

Artifacts in the chat output root:
- `normal-seller-flow-2026-10-19/output/pdf/normal-seller-disclosure-unsigned.pdf`
- `normal-seller-flow-2026-10-19/mobile.png` and `desktop.png`

Temporary browser tab closed, viewport reset, exact loopback server PID stopped
and its live session confirmed exit 143. No unrelated user tabs were closed.

## Remaining release scope

This customer PDF-access correction is implemented and locally verified, not
deployed. Normal production email-code/save/version/review/signing acceptance,
v2 listing-lead provider QA, purchase-offer packet inclusion and coordinated
schema/source/code release remain. Do not request v4 signatures or forward its
invitation again. No new owner action is needed for this local correction.
