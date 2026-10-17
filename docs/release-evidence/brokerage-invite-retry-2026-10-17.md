# Brokerage invite retry recovery — October 17, 2026

## Bounded outcome and baseline

Allow the same verified agent to retry an already completed invitation after
the final response is lost, without writing membership again or requiring a
replacement invitation. Scope: existing admin API acceptance helper and tests.
Production/main baseline revalidated as
9b9ccadf4b4c824aeb0d00d83b6698a1830b6b43, READY deployment
dpl_5UZYVezc3CGFDxs7GBPbFCL7fTQJ, canonical HomeOfferFlow domains.

Keep automatic Git deployment disabled. Use only the existing normal PR/CI
and one intentional spend-protected prebuilt production release. No preview,
schema migration, browser role change or real invitation is required.

## Reproduction and behavior

The original helper looked up only pending invitations. A controlled test
accepted an invitation and lost its final HTTP response; retry returned
"no longer available" despite the correct active profile and membership.
The real POST handler also returned 400 on its second identical acceptance.
Empty HTTP-200 write results could count as success, and an existing member
could bypass the inactive-brokerage lookup.

- Permit lookup of pending/accepted invitations only. Accepted retry requires
  both the invited verified email and the original accepted_by actor.
- Confirm the same agent profile, same active agent membership and active
  brokerage. An accepted retry then returns the unchanged success contract
  with no profile, membership or invitation writes. It does not reactivate
  removed/suspended access, switch brokerages or grant broker/owner status.
- An already completed connection is not a new expired invitation; its retry
  can confirm that existing active connection even after the original expiry.
  Pending invitation expiry rules remain unchanged.
- Check active brokerage for existing memberships as well as new memberships.
- Require exact profile, membership and invitation readback from each existing
  write; an empty or mismatched result cannot consume the next stage or claim
  confirmed acceptance. Existing membership uniqueness and seat-cap enforcement
  remain in place. No form-access or brokerage-seat requirement was added.

## Verification and limits

- Nine new stateful tests exercise the actual helper and real POST handler
  with httpx MockTransport, fictional records and no external network.
  Cases include lost final response, partial membership failure/retry,
  suspended/removed/pending membership, wrong actor/email, cross-brokerage or
  privileged roles, inactive brokerage, previously accepted expiry and empty
  write responses. The repeated HTTP-handler request returns the same 200
  contract and performs no extra writes.
- Existing test transport now returns realistic requested row representations
  instead of id-only placeholders. Seventy-nine focused checks pass across
  retry, OnDemand launch, recovery, scope and administrative-attestation tests.
- Frozen full suite: 2,661 tests in 84.803 seconds, OK, one environment skip.
  Log /private/tmp/hof-invite-retry-full-20261016.log. Its later Invalid fixture
  PDF message is an expected negative-test diagnostic, not suite failure.
  The process handle expired before continuation; the preserved terminal log
  was inspected, not rerun or treated as an unexplained running process.
- Read-only production schema inspection confirmed existing invite columns,
  including accepted_by, and the unique brokerage_id/user_id membership index.
  No credential or private invitation token was retrieved or exported.
- API-only change: the public shell/assets remain unchanged, so no offline
  cache bump is needed. Signing/PDF candidate PR 1341 is excluded.

The existing staged profile -> membership -> invitation writes remain separate
HTTP operations. This is retry recovery and truthful confirmation, not a new
atomic transaction or proof of every concurrent-revocation ordering. It is
also not a live broker-admin rollout/agent-activation pass. No real customer,
brokerage membership, billing record or invite was changed for these tests.

## Production verification plan

After exact-head CI and the single release: verify provider source SHA and
canonical aliases, production PWA/API/runtime smoke and unauthenticated admin
rejection. Do not consume or create a real invitation just to claim a live
acceptance pass. Record runtime-error observations with their scope/limits.

## Deployed checkpoint

- Candidate 3de4466f93d7f3fdaeea41ad142533d50af3ccf9 passed independent CI
  39028282304, including full regression, golden rendering, signer geometry,
  database preflight and whitespace. PR 1345 merged as
  7b408eb09b46720261e8fed4712fe42e81547f33.
- One intentional release, 39028545771, completed at 2026-10-17 11:28:33 UTC.
  Exact-merge regression, release preflight, coordinated-schema readiness,
  spend/capacity, PWA and production API/packet-runtime smoke all passed.
- READY production deployment dpl_4ngxPqMxccmvJjNCB4pB9yWgeinL:
  https://homeofferflow-4jsuwv36f-dealdoc1s-projects.vercel.app. Provider metadata
  confirms the exact merge SHA, intended project/team and root/www aliases.
  Existing static HTML/JavaScript + Python API architecture is unchanged.
  The prebuilt build step took eight seconds.
- Fresh pre-build credit snapshot: $0.04 infrastructure usage, $19.96
  unconsumed, $3 reserved for the September 22–October 21 cycle. This snapshot
  is not a guarantee against later traffic usage; automatic Git deploys stay off.
- Canonical index and worker bytes match the tested tree and remain identical
  to the previous public shell. SHA-256 values respectively:
  41f1890fe921e582823265e81db28f1c203baae354362b8f615e43e148c4db6d and
  005fb23d381af20a8c0715b7e9d41a1f911fe472e0ddc968d9fe4cb61d9c443b.
- Canonical unauthenticated admin GET and invite-acceptance POST both returned
  401. The POST used only a fictional all-zero token and no authorization;
  no real invite, profile, membership, subscription or delivery was touched.
- Initial runtime error/fatal scan, scoped to this deployment with a one-hour
  lookback, returned no groups. That does not prove future traffic or a live
  authenticated enrollment. External drain configuration remains unverified;
  no monitoring product or paid service was changed.

This backend correction is deployed and smoke-verified, while authenticated
broker-admin rollout/activation and other form-signing QA remain separate.
No live invite acceptance was exercised merely to obtain a production check.
The post-release documentation checkpoint does not request another deployment.
