# Public entry-path live QA — September 10, 2026

## Scope

Read-only production-browser verification at `https://www.homeofferflow.com`.
No sign-in, form submission, payment, signature request, consent acceptance,
or customer record creation occurred.

## Verified in production

| Audience | Entry route | Result |
| --- | --- | --- |
| Homebuyer | `/?buyer=1` | The public route opened the offer experience and showed the opening acknowledgement. The Continue button remained disabled until the acknowledgement is accepted. The acknowledgement was not accepted during QA. |
| FSBO seller | `/sellers` | The page loaded its four sale-stage choices. “Still getting ready” opened the free seller-plan intake. The intake requested only property address and email, and its submit action remained disabled with both fields empty. |
| Agent / broker | `/agents` | The page loaded all four transaction choices: property listing, purchase, lease listing, and lease representation. No transaction was selected and no sign-in was attempted. |
| Investor | `/investors` | The investor workspace entry, concise workspace explanation, repeat-offer value framing, and return-workspace action all loaded. No sign-in was attempted. |

## Evidence boundary

- This confirms public entry rendering and safe first actions only. It does
  not claim completed buyer interviews, authenticated agent/investor work,
  saved seller requests, payments, generated packets, or completed-signature
  PDF visual QA.
- The buyer journey was intentionally stopped at the legal/e-sign
  acknowledgement. QA must not accept legal terms or electronic-record
  consent on a user's behalf.
- The agent production page was serving the previously released revision
  during this check. Main contains later low-cost improvements, including the
  returning-agent workspace sign-in path, but they have not been promoted to
  production in this cost-controlled release batch.

## Release posture

No Vercel deployment was started for this QA. Git-triggered Vercel deployments
remain disabled; normal main merges do not publish production. A future
intentional production release should recheck all four public entries after
the chosen bundle is deployed.
