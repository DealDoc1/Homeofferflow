# Vercel production baseline — 2026-08-07

This is the read-only runtime baseline captured before the next intentional
production deployment. It does not authorize a deployment or change runtime
behavior.

## Project

- Project: `homeofferflow`
- Vercel project ID: `prj_LupoeEEcWigvtw6CII2bL46l0RB3`
- Team ID: `team_BZUBDsoLMwlnaXtIES35YT4S`
- Current latest production deployment queried: `dpl_DA1Y4EWxUFkwgW6x2SHLpGjGwzxf`

## Runtime check

- Time window: previous 24 hours
- Grouped runtime errors: none found
- Runtime status counts: HTTP 200 = 3; HTTP 401 = 1

The 401 response is expected for an unauthenticated protected request. Any new
5xx/function-error cluster after deployment must be investigated before
release sign-off.

## Deployment policy

Git deployments remain disabled to conserve Vercel Hobby capacity. The next
release must be one intentional production deployment after applicable QA
gates pass, followed by a post-deploy runtime comparison against this baseline.
