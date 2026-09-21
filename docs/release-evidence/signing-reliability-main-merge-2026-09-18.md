# Signing-reliability mainline merge — September 18, 2026

## Outcome

The seven-commit signing-reliability stack was consolidated in pull request
[#1233](https://github.com/DealDoc1/Homeofferflow/pull/1233) and merged into
`main` as `b4d517be791e242e415b0348b0e1dcc920d148a9`.

The merged behavior:

- restores simultaneous signer invitations and accurate delivery summaries;
- preserves draft, partially signed, completed, declined, and canceled states;
- prevents late or replayed events from replacing newer signing progress;
- recovers standalone and purchase-offer signature requests from the same
  saved provider document rather than issuing duplicate invitations; and
- verifies the saved document identity, fields, and recipients before retry.

Pull requests #1228 through #1232 were closed as superseded after their exact
commits were included in #1233. Pull request #1227 closed automatically when
its commit reached `main`.

## Verification

GitHub Actions run
[`35404761878`](https://github.com/DealDoc1/Homeofferflow/actions/runs/35404761878)
passed on the merge commit. Its Python job completed all required steps:

- pinned dependency installation;
- full unit-test discovery;
- approved golden packet rendering;
- standalone TXR signer-geometry guard;
- Supabase branch preflight; and
- patch-whitespace validation.

## Deployment and cost boundary

The intentional production-release workflow for the merge commit was skipped.
Git-triggered Vercel deployments remain disabled, so this merge created no
Vercel preview or production deployment and consumed no intentional deployment
from the current release budget.

The code is merged and CI-verified, but it is not yet production-deployed or
canonical-domain verified. Those remain part of the next coordinated release.
