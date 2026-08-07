# OnDemand authentication and launch preflight — 2026-08-07

## Public launch surface

The live `/ondemand` page was inspected through the connected browser and
confirmed to show:

- `$0 today` for the launch trial;
- a 60-day trial period;
- renewal at `$29/month` with a displayed renewal date;
- cancel-anytime language;
- current scope limited to purchase-offer packets and supported addenda;
- a clear statement that standalone buyer-representation, listing, and seller
  disclosure workflows are not yet live.

## Brokerage membership preflight

The live Supabase membership query confirms that:

- the OnDemand brokerage exists and is active;
- one active `broker_admin` membership is present for the brokerage;
- an active test-agent membership is present;
- Andrew's current brokerage membership is pending and therefore is not yet a
  valid authenticated agent-QA identity.

This verifies the brokerage hierarchy and launch-scope state only. It is not
evidence of authenticated dashboard QA, TXR point-of-use QA, or completed
signature QA.

## Side-effect boundary

No sign-in email was sent, no draft agreement was created, no SignWell document
was sent, no billing event was created, and no Vercel deployment was triggered
by this preflight.

## Remaining gate

Run the authenticated broker-admin and agent QA bundle using an existing valid
session, then retain the metadata-only reports and perform rendered PDF review
before any restricted Texas REALTORS® workflow is enabled.
