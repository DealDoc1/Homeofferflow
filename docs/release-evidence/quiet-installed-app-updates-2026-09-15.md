# Installed-app update UX — September 15, 2026

## Outcome

Ordinary browser tabs no longer show an app-update prompt. Installed standalone
apps retain the explicit update choice. No forced refresh occurs during an
interview; repeated Update clicks send one activation request and reload once
after activation. If the waiting worker disappears before the click, the
workspace no longer arms a later unrelated refresh.

The public shell cache advances from v72 to v73 so the shared registration
script is refreshed. Network-first public navigation, offline support, private
data exclusions, and install offers are unchanged. No dependency, backend
request, paid service, or new analytics event is introduced.

## Integration

This ports the PWA-specific intent from pending PR #1216 onto the current
release stack, without copying that older branch's unrelated OnDemand edits
or overwriting the newer saved-work wording. It follows PR #1228, which follows
the simultaneous-signing correction in PR #1227. PR #1216 must not subsequently
be merged wholesale into this stack.

## Verification

- Full local suite: **1,767 tests passed**.
- Seven new runtime tests execute the shipped workspace registration block and
  public update handlers using Node with a DOM/service-worker event model.
- Coverage: regular browser suppression, standalone and iOS standalone
  detection, updatefound, first install, missing waiting worker, double clicks,
  explicit activation, repeated controller changes, and workspace Later.
- Existing PWA cache, installation, sharing, routing, and private-data
  exclusion regressions remain green. Patch whitespace check passed.
- Display-mode behavior was checked against
  [MDN display-mode](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/display-mode)
  and explicit activation against
  [MDN skipWaiting](https://developer.mozilla.org/en-US/docs/Web/API/ServiceWorkerGlobalScope/skipWaiting).

These are local event-model and regression results, not newly completed
physical iOS/Android installation tests or rendered mobile screenshots.
Production verification remains pending the bundled release.

## Cost and reporting

No Vercel build or deployment was initiated. Automatic Git deployments remain
disabled and this change does not modify release workflows. Preserve the
user's no-overage constraint; report this as built/tested, not deployed.
