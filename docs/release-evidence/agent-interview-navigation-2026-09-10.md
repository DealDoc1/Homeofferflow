# Agent interview navigation and concise choices — September 10, 2026

## User story

An agent chooses a property listing, purchase, lease listing or lease
representation transaction, answers the next question, and can move forward
or back without keyboard focus disappearing behind the question. The same
interaction should remain usable on a phone and in the installable web app.

## Reproduced problems

- Using the actual interview function and production styles in an isolated
  local browser fixture, Tab from the last button moved focus to the page body
  instead of staying inside the active question.
- Escape from a nested representation choice closed it but left focus on the
  page body. The nested dialog captured the already-removed parent answer as
  its return target.
- Mobile verification caught focus wrapping to an offscreen Back button when
  scrolling was suppressed: its bottom was at 901px in a 667px-high viewport.
- Five purchase-addendum choices repeated the same review/send instructions
  already displayed above the choices, adding avoidable scrolling.

## Corrections

- Both levels of questions share the original transaction launch control.
  Back preserves it; Escape closes only the active question, not an enclosing
  account view. A replaced launch control falls back to the same transaction
  choice after account rerendering.
- Tab and Shift+Tab wrap among the visible, enabled choices in the active
  question. Dynamic choices are re-evaluated for each keystroke; a temporarily
  empty dialog retains a focus target.
- Focused choices scroll into view on small screens.
- Shared instructions appear once. The purchase-specific guidance for the
  residential-lease and fixture-lease addenda is retained, as are all seven
  document choices and their original destinations.
- The mobile-app brief now preserves independent-agent access to released
  shared forms, without a brokerage seat or per-agent attestation. Existing
  subscription rules and private-record ownership remain unchanged. This
  updates the future app plan; it does not claim a native app was built.

The keyboard behavior follows the
[W3C modal-dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).

## Verification

- Full local regression suite: **1,630 tests passed**.
- Twelve executed runtime scenarios cover forward/reverse wrapping, visible
  focus, normal interior tabbing, Escape, unrelated keys, hidden/disabled
  controls, an empty dialog, dynamic controls, lost focus, replaced launchers,
  and returning from nested questions.
- Browser-verified all four transaction-question routes: Tab wraps forward,
  Shift+Tab wraps backward, and Escape restores the original launcher.
- Browser-verified all five nested choice routes (three purchase routes and
  two lease-representation routes): forward/backward focus stays inside,
  Back restores the parent question, and subsequent exit restores the launcher.
  Direct Escape from the nested representation choice also restores the
  launcher.
- At 375 by 667 pixels, the longest document-choice dialog measured 343px wide,
  with 16px side margins and matching 341px client/scroll widths. Its content
  height fell from 1,273px to 904px (about 29%). The concise choices retain
  52px-high touch targets.
- Shift+Tab revealed the focused Back button fully within the viewport
  (bottom 630px); the next Tab revealed the first choice again. Both states
  were checked in the browser, with the focused Back state visually inspected.
- No browser warnings/errors were recorded in the local QA tab. All 43 inline
  scripts parse; patch whitespace is clean.

The fixture executes the actual question code and styles, but workspace
handoffs are simulated and outbound connections are disabled. This is UI
navigation verification, **not** an authenticated transaction, PDF-rendering,
or signing-completion test. No accounts, signatures, emails or payments were
submitted. The temporary tab and local test server were closed afterward.

## Release status

This batch shares the pending v67 shell release with the customer-path
restoration fix. The user explicitly approved publication to the public
`DealDoc1/Homeofferflow` repository and one production release. No Vercel build
or deployment was used for local development. Canonical production verification
remains required after release. No new customer-facing approval or access
requirements were added.
