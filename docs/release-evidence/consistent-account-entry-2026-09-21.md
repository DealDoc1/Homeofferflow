# Consistent account entry — 2026-09-21

## User problem

The global signed-out account action said `Agent / Broker Login` even though the
same account dialog also supports investors. Other account messages alternated
between `login`, `log in`, and `sign in`. The mismatch made one shared account
entry look role-limited and less polished than the guided paths behind it.

## Candidate change

- Use the concise, role-neutral `Sign In` label for the global signed-out
  account action in its initial, restored, and responsive states.
- Use `HomeOfferFlow Account` as the pre-interaction dialog title while keeping
  the visible Agent, Broker / Team Lead, and Investor choices intact.
- Standardize customer-facing subscription and packet prompts on the verb
  `sign in`.
- Preserve account-role routing, passwordless authentication, saved profiles,
  transaction context, and analytics behavior.

## Verification

- 95 focused account, agent, investor, subscription, PWA, and modal tests
  passed.
- Full repository suite: 2,392 tests passed in 68.140 seconds.
- A 1280 by 900 headless Chrome check verified `Sign In` before interaction,
  all three account choices after opening, focus in the email field, no old
  `Login` label, and no customer-visible provider terminology.
- The local static server intentionally lacks the Vercel Analytics endpoint;
  that expected local-only 404 was not an application error overlay.

## Release status

Implemented, locally tested, and browser-verified. This change is not
production-live until the coordinated post-reset deployment completes and the
canonical navigation and account dialog are checked again.
