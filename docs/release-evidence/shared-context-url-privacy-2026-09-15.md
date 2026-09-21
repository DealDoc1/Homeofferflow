# Installed-app shared context: URL cleanup

## Issue and implementation

The existing installed-app GET share target read `title`, `text`, and `url`
into a review card but left those values in the visible browser URL. A copied
address or later browser-history navigation could therefore include context
the user shared for review only.

After reading the existing bounded values, the share script now replaces the
current history entry with the same path, unrelated parameters, and fragment,
removing only `pwa_share`, `title`, `text`, and `url`. It preserves history
state. Cleanup happens before waiting for DOM-ready or rendering the card.
The context remains in page memory and escaped DOM text; this adds no storage,
offer prefill, API request, or automatic visit to the supplied external link.

Only URLs with `pwa_share=1` are handled. Empty shares are cleaned without
rendering an empty card. History access failures do not block the existing
review or customer actions, but in that case URL cleanup is not guaranteed.

## Verification

- 12 source-backed Node runtime cases pass. Against pre-fix `e95e5bac`, seven
  cleanup cases fail and five existing-behavior controls pass.
- Covers cleanup before rendering, duplicate parameters, preservation of
  unrelated route/auth/campaign parameters and history state, empty shares,
  non-share URLs, denied/unavailable history access, escaped markup, unsafe
  link rejection, and all three buyer/agent/seller handoffs.
- Test spies observe no new persistence/network requests and no shared text
  or shared URL in the recorded action telemetry arguments.
- Asset syntax and `git diff --check` pass. Full local suite: **2,000 tests
  pass in 17.308 seconds**.

The actual asset runs in a mocked DOM/history environment; this is not live
browser QA. The main `trackEvent` implementation already catches provider
exceptions, so this batch does not change that helper based on an assumed bug.

## Privacy limits and release status

This does **not** erase the initial GET request, previously captured URLs,
upstream access logs, or any prior history entries. Changing the share protocol
to POST would require a separate design and verification effort; no such claim
is made here.

Local only; no push, build, preview, or production deployment. No recurring
service or cost added. The pending bundle already advances the installed-app
shell to v73; ship this asset with that intentional update, not as an assertion
that existing installed apps have already refreshed.
