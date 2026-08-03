# Brokerage admin live QA evidence — 2026-08-03

## Scope

This record covers production checks that can be completed without a signed-in
brokerage administrator. It does not claim authenticated UI completion.

Production URL: `https://www.homeofferflow.com/`

## Verified

| Check | Expected | Result |
|---|---|---|
| Public OnDemand launch page | Loads and describes the 60-day trial, renewal price, and current launch scope | Pass |
| `GET /api/admin-dashboard?scope=brokerage` without a session | `401` with a signed-in-session requirement | Pass |
| `GET /api/admin-dashboard?scope=roadmap` without a session | `401` with a signed-in-session requirement | Pass |
| `GET /api/feedback-alert` health route | `200` and `{\"ok\":true,\"route\":\"feedback-alert\"}` | Pass |
| Production runtime errors | No grouped errors in the selected 24-hour window | Pass |
| Local regression suite | All tests green | Pass — 360 tests |

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
