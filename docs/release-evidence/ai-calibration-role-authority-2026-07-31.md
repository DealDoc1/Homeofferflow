# AI calibration role authority — 2026-07-31

## Scope

The AI calibration feedback endpoint now derives the reviewer role from the
authenticated Supabase profile instead of trusting a browser-supplied role.

## Safety behavior

- A reviewer cannot claim `broker` or `brokerage_admin` in browser JSON.
- AI calibration evidence is accepted only for an authenticated `agent` or
  `brokerage_admin` profile.
- A missing or unknown profile fails closed for calibration evidence.
- Non-calibration feedback remains available and is stored with the safest
  server-derived role available.
- The five-scenario human calibration threshold and scoring/writing safeguards
  are unchanged.

## Verification

- Focused feedback/calibration tests: 10 passed.
- Full regression suite: 314 passed before this change; rerun required before
  deployment.
- No PDF source, field map, signer plan, or offer-generation route changed.
