# Keep the selected customer interview — September 10, 2026

## Production finding

On the canonical `https://www.homeofferflow.com/?buyer=1` path with an existing
agent session, the Homebuyer interview initially displayed Step 1 of 10. After
account restoration it changed to Step 1 of 8 even though the visible landing
page still described the Homebuyer path. Passive account/profile refreshes
were replacing the selected transaction audience with the account role.

## Correction

- Preserve the chosen Homebuyer, Agent/Broker, Investor or FSBO path when
  account controls refresh or an authoritative profile finishes loading.
- Apply saved agent/entity defaults only to their corresponding interview.
  A personal homebuyer offer must not inherit unrelated agent or investor
  terms because the account happens to finish loading later.
- Keep explicit account-role selection and starting an offer from an account
  intentional: those actions still choose the appropriate transaction path.
- Advance the installable site's shell cache to v67.

Account authentication, authoritative profile lookup, authorization, database
schema, subscription entitlements, prices, legal text, document coordinates and
Google Maps autocomplete are unchanged. This is a navigation/defaults fix, not
a change to who can access account data or forms.

## Local verification

- Full regression suite: 1,626 tests pass.
- Twenty-nine executed Node scenarios use the actual shipped functions in an
  isolated environment: all four audiences with agent, broker and investor
  account refreshes; anonymous sessions; asynchronous authoritative profile
  loading; a selection made while that request is pending; saved-role startup;
  investor default scoping; and explicit account starts for all three roles.
- All 43 inline scripts parse; patch whitespace is clean.
- The tests do not create accounts, send email, submit documents, purchase a
  plan, or call a live database. They are regression checks, not a replacement
  for the canonical browser check after release.

## Release boundary

Prepared for one intentional prebuilt production release from the current
production base `d62fcf3001e4303242a19843889851b4e629c0ad`. Build work remains on
the standard GitHub runner, not on Vercel build infrastructure. Canonical
browser verification and release identifiers will be recorded after the
deployment is confirmed.

### Publication authorization

The user explicitly approved publishing the pending HomeOfferFlow UI fixes,
tests and sanitized release notes to the public `DealDoc1/Homeofferflow`
repository, followed by one production release. This resolves the earlier
publication hold; no alternate upload route was used.

The implementation commits are:

- `a736338` — preserve the selected customer path during account restoration;
- `3acb3bd` — consistent keyboard navigation, visible mobile focus, concise
  document choices, and independent-agent access in the future app brief.

The combined local regression suite passed 1,630 tests. Source PDFs, completed
agreements, credentials and private QA contacts are not part of this payload.
Deployment and canonical-browser results remain to be recorded after release.
