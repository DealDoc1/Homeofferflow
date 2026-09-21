# Installed-app shell update evidence — 2026-09-21

## Outcome

HomeOfferFlow's installable web app now uses shell cache `homeofferflow-shell-v74`.
This deliberate version change lets an already-installed app detect the bundled
public-workflow improvements and offer the existing in-app update choice instead
of leaving a returning user on the previous cached interview shell.

## Cost and scope

- No native app, app-store account, new provider, background job, or recurring
  infrastructure was added.
- The existing user-controlled update behavior remains unchanged: a waiting
  worker activates only after the user chooses the update.
- API responses, authenticated data, signed documents, and third-party requests
  remain excluded from the service-worker cache.
- The worker continues to cache public HTML only after a successful visit and
  uses network-first navigation.

## Verification

- PWA baseline, installation, update, share-target, and shortcut tests cover the
  new shell version and existing privacy boundaries.
- Runtime update tests execute both the authenticated workspace and public-page
  update handlers, including no forced activation, one controlled reload, and
  quiet browser-tab behavior.
- The complete local test suite is run before release bundling.

## Production state

This change is merged-ready but remains pending the single intentional bundled
production deployment scheduled after Vercel billing capacity resets.
