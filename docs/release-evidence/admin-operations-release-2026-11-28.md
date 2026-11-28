# Coordinated operator reporting and QA diagnostics release

## Scope and release boundary

Base: verified canonical production
aeda19c33dffea3add04b50994ca826f4e1e7963,
READY deployment dpl_H4S48GWWLUyzjG9Yec4oWa9mSJM5.
The candidate batches the accurate acquisition activity cards (d663d3f7)
with already-reviewed omitted-control readback and sanitized failed-send
diagnostics (bc4af812e, integrated as 350dfacdc). Support-send evidence is
synchronized through 920ca25a4. Shell v241 retires the stale public index.

No new signing recipe or send path, reservation reset, provider retry, customer
package activation, PDF, database migration, API field removal, billing
configuration, dependency or release workflow change is included. The retained
buyer QA draft still has an unexplained HTTP 422 send failure. This release
does not complete buyer/custom packages, activate uploaded AI review, or launch
native apps. Those remain the separate priority checklist items 2, 3 and 4.

## Verification before release

112 combined focused Python cases passed using the actual pinned private blank
sources, including all five acquisition-card Node runtime checks. The existing
three channel-summary Node cases also passed. Local Chrome reviewed the
changed actual card templates/CSS with fictional metrics at measured 390px
and 1280px content widths; text, contrast and wrapping passed without horizontal
overflow. Browser overrides were reset, the temporary tab closed and the
localhost review server stopped. No new PDF page review is needed because no
PDF bytes, field map or renderer changed.

Release preflight passed against the production base with expected deploy
author andrewchri@gmail.com; no packet/form source or mapping change detected.
Git automatic deployments remain disabled. Independent Vercel history readback
found 3 of 12 rolling deployment slots used. The billing connector returned
Plan not found; the existing authenticated CLI usage route succeeded instead.
Current-cycle infrastructure usage was $0.009244, leaving $19.990756 of the
$20 credit with the $3 reserve intact. The intentional production workflow must
recheck schema, project, capacity and spend immediately before its build.

Full local candidate regression passed: 3,255 tests in 105.275 seconds with
30 opt-in skips. Protected exact-head CI is still required before merge/release.
One intentional prebuilt production deployment is authorized
only after those checks pass. No routine preview or documentation-only release.

## Post-release checks required

Confirm canonical deployment commit, public shell v241 and runtime/PWA smoke;
verify changed assets match the tested tree. In the authenticated Admin UI,
confirm accurate acquisition event units and read-only Check corrected test
returns the retained draft's diagnostic instead of throwing for an omitted
checkbox_groups key. Do not click Send, create another draft, reset a receipt,
use a real customer packet, or claim completed-provider QA. Inspect the
deployment's recent error/fatal logs with bounded retention.
