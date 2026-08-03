# Brokerage admin live QA evidence — 2026-08-03

## Scope

This record covers production checks that can be completed without a signed-in
brokerage administrator. It does not claim authenticated UI completion.

Production URL: `https://www.homeofferflow.com/`

Latest verified production commit: `d9eb70b`

Latest Vercel deployment: `dpl_9ouocpBidjaTrC7feae4UHHFEJzs` (READY)

## Verified

| Check | Expected | Result |
|---|---|---|
| Public OnDemand launch page | Loads and describes the 60-day trial, renewal price, and current launch scope | Pass |
| `GET /api/admin-dashboard?scope=brokerage` without a session | `401` with a signed-in-session requirement | Pass |
| `GET /api/admin-dashboard?scope=roadmap` without a session | `401` with a signed-in-session requirement | Pass |
| `GET /api/feedback-alert` health route | `200` and `{\"ok\":true,\"route\":\"feedback-alert\"}` | Pass |
| Production runtime errors | No grouped errors in the selected 24-hour window | Pass |
| Profile-load failure handling | Privacy-safe retry state replaces indefinite brokerage loading | Pass — verified in `index.html` and focused regression test |
| Local regression suite | All tests green | Pass — 371 tests (including brokerage invite acceptance, expiry coverage, live-QA runbook, and profile-load failure coverage) |

The live brokerage membership check was completed without querying or
publishing buyer-sensitive offer data. Organizational roster details remain
internal to the authenticated QA record.

## Current preconditions

- The live OnDemand brokerage is active.
- A brokerage-scoped administrator profile exists for the brokerage.
- The private form-source vault currently has no source records.
- The connected browser session did not expose an authenticated administrator
  profile, so no authenticated UI QA or source upload is claimed here.

## Not yet verified

The following require an authenticated active `brokerage_admin` session and
must be completed before the brokerage workspace tracker is marked passed:

- Brokerage name, role, and branding display.
- Privacy-limited roster and operational totals.
- Invitation creation, expiration, email binding, and acceptance.
- Shared defaults and explicit agent-copy behavior.
- Brokerage context propagation into an offer packet and signing message.
- Negative authorization path for restricted Texas REALTORS® workflows.

No source form was uploaded, no Texas REALTORS® authorization was inferred,
and no restricted workflow was activated during this check.
