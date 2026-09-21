# OnDemand installed-app handoff — 2026-09-21

## Outcome

An OnDemand agent returning from a successful mobile checkout now sees one
contextual install choice inside the enrollment card. The sitewide floating
install card does not compete with that next step on the OnDemand page.

The contextual path now records aggregate CTA, native-prompt, acceptance, and
dismissal outcomes. This makes the existing PWA a measurable low-cost bridge to
a future native app without adding app-store work, a provider, or recurring
infrastructure.

## Evidence basis

- The 30-day aggregate funnel recorded 42 native-install-available events and
  34 shown prompts, but no accepted event.
- Source inspection found two independent install surfaces could retain the
  same browser prompt on `/ondemand`, while the checkout-return path discarded
  its choice without recording the outcome.
- The OnDemand sales and enrollment copy already states the current offer,
  price, card requirement, cancellation terms, and three enrollment steps, so
  this change removes noise instead of adding more copy.

## Privacy and cost

- Events contain only an allowlisted action, broad platform (`ios`, `android`,
  or `web`), and the fixed `/ondemand` surface.
- No email, account, client, property, device identifier, document, or campaign
  value is included.
- Existing endpoints, the existing service worker, and the existing PWA are
  reused. No new function, database table, vendor, or scheduled task is added.

## Verification

- Focused OnDemand enrollment, shared PWA, and install-experience checks pass:
  72 tests.
- The real inline OnDemand enrollment script parses in Node before release.
- The complete local regression suite passes: 2,376 tests.
- Production verification remains part of the single coordinated post-reset
  release; no preview deployment was created.
