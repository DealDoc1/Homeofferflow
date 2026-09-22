# Not-found recovery funnel

Date: 2026-09-22

## Change

- Records a privacy-safe not-found recovery view and the selected transaction path.
- Preserves the allowlisted `site_recovery` channel through secure agent sign-in.
- Adds the recovery channel to the existing aggregate admin conversion report.

## Privacy and cost

- No URL, referrer, email, property address, or visitor identity is stored by this funnel.
- Events use the existing lightweight event endpoint and database table; no new provider or recurring service is required.
- Navigation is not delayed: Beacon is preferred, with a keepalive request fallback.

## Verification

- Public discovery tests cover all four recovery paths, the view event, the selection event, and preserved channel.
- Agent funnel tests cover the API allowlist, secure sign-in handoff, and admin reporting allowlist.
