# TXR/NAR agent-attestation release handoff

This handoff is for the HomeOfferFlow brokerage authorization hardening batch.
It does not activate a Texas REALTORS® form or alter the purchase-offer PDF
flow.

## Release

- Release name: Individual Texas REALTORS® / NAR agent attestation gate
- Local branch: `release/intentional-prod-2026-07-31-ai-scenario-gate`
- Local commits: `4d787ba`, `000d716`, `20b653a`, `c027f8d`
- Production scope: brokerage authorization controls and restricted-form audit metadata only
- Packet/form target marker: none; no packet source, coordinate map, or production offer route changed

## Behavior

- Brokerage setup asks the authorized brokerage administrator whether participating agents are authorized Texas REALTORS® / NAR users.
- Each restricted-form draft requires the individual agent’s point-of-use attestation.
- The server records the authenticated agent and timestamp on the active brokerage membership.
- Suspending brokerage access clears the prior individual attestation; restoration requires a new attestation.
- The broker dashboard exposes only attestation status, not buyer names, property details, offer terms, or document contents.
- Membership is never inferred from a license number.

## Supabase verification

Applied migration: `homeofferflow_brokerage_txr_agent_attestation`.

Verified live on project `acqylchftrjjoablvqyq`:

- `hof_brokerage_members.txr_agent_authorized`
- `hof_brokerage_members.txr_agent_attested_by`
- `hof_brokerage_members.txr_agent_attested_at`
- `hof_brokerage_members_txr_agent_attestation_check`

The OnDemand organization gate remains intentionally unattested until its
authorized brokerage administrator completes the attestation.

## Verification

- Full automated suite: 331 tests passed.
- Release preflight: passed with no packet/form source or mapping change detected.
- Working tree: clean.
- Production route `api/fill-pdf.py`: untouched.
- Production PDF: untouched.

## Deployment gate

Do not deploy until the local branch is published through GitHub and the
intentional Vercel release process is run under the approved deployment author.
GitHub write authentication was unavailable when this handoff was prepared.
