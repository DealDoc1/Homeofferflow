# Correct rolling deployment counts without an app build

## Batch contract

- Outcome: the existing release-cost safeguard accurately counts recent deployments and fails closed on untrustworthy responses. Preserve its 100-deployment threshold, $20 infrastructure credit assumption and $3 reserve.
- Scope: capacity script, focused/captured-response tests and a reviewed-main read-only check workflow. No application, PDF, signing, billing setting, source, role or credential changes. No Vercel build/deployment/preview required.
- Baseline app production `a63489823e2d823aa2835ecb3d7e3a1db97b5b52`, READY `dpl_FiQvp354oPnUfwoCtMw6DuCAkp8x`. Active roadmap continues separately from this bounded cost-safety correction.

## Verified cause

- Last intentional app release `38464036125` reported zero deployments in its rolling window despite known same-day release identities. Its independent spend check and app deployment were successful, but zero was not reliable capacity evidence.
- At fixed UTC snapshot October 13 20:44:26, the exact old from-cutoff query returned 100 older rows, latest creation `1791826886039` before cutoff `1791837866000`. Local time filtering therefore misleadingly produced zero.
- Current since/until query for the same project/team/window returned nine recent deployments, including the latest app release, with pagination count nine and no next cursor. Only IDs, states and creation timestamps are retained in `tests/fixtures/vercel_deployment_window_2026_10_13.json`, not creator/contact/credential data.
- Official current endpoint/filter guidance: https://vercel.com/docs/rest-api/deployments/list-deployments. from/to are deprecated, since/until are the current time filters. The observed legacy-query behavior, not a guessed timestamp conversion, is the causal evidence.

## Correction and local verification

- Use v7 since/until with a fixed upper boundary across pages, preserve both local time boundaries, and validate every timestamp instead of silently skipping malformed entries. Support the documented createdAt fallback only when created is absent. Reject boolean, nonfinite and absent timestamps.
- Follow advancing, bounded pagination when the configured threshold needs more data. Validate page counts and IDs, reject duplicated entries, ignored date filters and invalid cursors. Once the observed count reaches the threshold, stop further reads and reject release rather than spending requests to compute an unnecessary exact excess count.
- Twenty-one focused tests pass: current query/scoping, both time boundaries, out-of-window exclusion, malformed responses, multiple pages, saturation at threshold, nonadvancing/duplicate pagination, captured live count nine, fail-closed main before billing, and unchanged spending-reserve behavior.
- The new read-only workflow is restricted to protected main and existing production environment. Official checkout/Python/Node actions are pinned to resolved commit SHAs, checkout does not retain credentials, CLI is the same reviewed version 57.0.0, and the existing Vercel credential is exposed only to the capacity read. No credential is retrieved locally, no app environment is pulled, and no build/deploy command exists.
- Full regression, independent final-head CI, merge and actual read-only production check will be recorded at their completed checkpoint. No fresh app deployment is claimed for this pipeline-only correction.
- Frozen local candidate: 2,586 tests in 85.354 seconds, OK (one environment-dependent skip). The printed Invalid fixture PDF message belongs to an expected negative test; process exit zero and final OK are the result. Working-tree whitespace passes; committed-range whitespace is checked before push.
