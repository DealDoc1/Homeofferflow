# Homepage audience selection preserves saved work

## Issue and implementation

The four homepage audience pills called the same function used to select an
actual transaction role. Browsing could therefore change the unfinished
offer's role, clear its property-visit answer, reset an open interview, and
schedule an offer save. Campaign initialization had the same side effects.

Public audience selection now requests presentation-only behavior. Both the
base selector and its landing-page enhancement wrapper preserve this option.
The pills, audience cards, campaign audience parameters, shared seller URL,
and installed-app seller-plan shortcut use it. The selected pill continues to
control the next public workflow; resume labels follow that visible choice
rather than an unrelated in-memory offer role. Seller-modal dismissal and
audience-specific copy, trust, and context updates remain intact.

Explicit transaction starts and restores keep the existing one-argument
behavior. This change does not globally remove role assignment or draft saves.
Other dedicated authenticated agent/investor route handlers still require a
separate isolation review; this evidence does not certify those routes.

## Verification

- 34 Node runtime cases execute actual selector implementations, wrapper,
  inline pill/card handlers, campaign initialization, keyboard handling,
  seller URL handoff, and seller installed-app shortcut.
- Checks cover offer-object identity, all serialized in-memory offer data,
  step, representative input and helper state, absence of save/reset calls,
  chosen workflow, resume labeling, and retained explicit transaction changes.
- Against pre-fix commit `2f35d8d5`, 28 cases reproduce the defect and six
  positive controls pass. With the fix, all 34 pass.
- All 45 executable inline scripts parse. `git diff --check` passes.
- Full Python suite: 1,999 tests pass in 18.572 seconds.

These are local source-backed runtime tests with mocked DOM, storage/save
boundaries, and route destinations, not browser visual QA or live account QA.
No production offer, identity, contract, signature, or email was modified.

## Release and cost status

Local only. No GitHub push, Vercel build, preview, or production deployment.
No paid service or new recurring background request introduced. Include this
fix in the next authorized cost-controlled release and subsequent daily report;
do not report it as live until production is verified.
