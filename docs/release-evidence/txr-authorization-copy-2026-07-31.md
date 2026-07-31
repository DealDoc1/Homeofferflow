# Texas REALTORS® / NAR authorization-copy evidence — 2026-07-31

## Change

Commit `6825d9d` adds explicit agent-facing launch copy explaining the two
authorization layers for restricted Texas REALTORS® / NAR member forms:

1. The brokerage administrator attests that participating agents are
   authorized.
2. Each agent confirms current authorization at the point of use.

The copy also states that HomeOfferFlow never infers membership from a license
number alone.

## Verification

- `tests/test_agent_launch_scope.py` verifies the two-level gate language.
- Focused brokerage/launch tests: 38 passed.
- Full repository suite: 302 passed.
- No TXR source PDF, field map, signer plan, or production form workflow was
  changed by this commit.
- Live OnDemand source-vault state remains fail-closed: zero source rows and
  zero approved source rows.

## Release status

This is bundled for the next intentional Vercel release under the Hobby
deployment policy. It does not authorize or activate TXR-1507, TXR-1501,
TXR-1508, or TXR-1506.
