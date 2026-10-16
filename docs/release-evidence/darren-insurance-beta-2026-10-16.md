# Darren Foster insurance beta launch — October 16, 2026

## Batch contract

- Outcome: publish the owner-authorized complimentary insurance partner and prepare an unsent completion reply to Darren, copying Vanna.
- Scope: existing central beta application, public directory, optional payment-planning card and existing offer-follow-up component. No customer packets, form mappings, signatures, billing, account permissions or disclosure PR #1341 changes.
- Production baseline: main e15c5db0138751a0232054045eda7e0b8442e465, READY dpl_47tztcZ7rgRmvVYvdCdLUubDpBSz. Separate checkout/branch keeps the disclosure candidate out.
- Cost: Git autodeploy remains disabled. One intentional prebuilt release. Read-only capacity run 38943829211 passed at 17:59 UTC: zero deployments in the rolling day, $0.04 infrastructure used, $19.96 unconsumed, $3 reserved. Release job repeats this check before building.
- Required evidence: focused renderer/API tests, frozen regression check, independent CI, exact release identity, database readback, canonical served-code comparison and desktop/mobile placements. Follow-up display checks must not be misrepresented as a new fulfilled customer transaction.

## Approved setup and publication

- Vanna's 1a14522aa396c83c confirms North Texas, with service statewide except coastal areas; current official agent-page information/branding may be used. Darren's later correction 1a145318105d0a76 explicitly supersedes Vanna's personal phone and permits both business emails.
- Existing public-profile fields contain only approved information. Mobile +19034362470, office 903-712-4393, and both business emails appear in the expanded directory description. Website CTA opens Darren's official agent/contact page; the independent call action uses his corrected mobile. No automatic customer-information forwarding.
- Application 7250bf33-bb42-473e-b84d-1766a240c4db; active placement 3b28df5e-d0ea-40ca-a0d7-1872f3326176. Independent SQL readback confirms beta, onboarding complete, fee zero, brokerage null, no subscription, payment not_started, agreement not_started and agreement timestamps null. No agreement execution is asserted.
- Scoped publication workflow 38943852557 remained queued with no runner/steps. It was cancelled and independently confirmed completed/cancelled before the equivalent scoped transaction created the placement. Only timestamp-update trigger exists on the touched tables; no billing/email trigger. No duplicate writer or new credentials.
- Approved image is the existing official Texas Farm Bureau Insurance logo served on Darren's current agent page. No invented brand artwork or unsupported insurance services.

## Implementation and verification

- New optional insurance card loads only when finance step 4 is active and the payment-planning details are open. Existing central public lookup/cache is reused. Failure hides the card without blocking the interview; provider choice and no automatic sharing are explicit.
- Insurance placement events retain aggregate placement metadata only. Server allowlist includes insurance_planning; active-placement validation remains unchanged. No schema change.
- Existing roofing banner and offer-follow-up remain intact. Service-worker shell v103 includes the new small asset, without reloading an active interview.
- Focused partner Python tests: 165 passed. Insurance renderer/source checks: 2 Python tests covering 6 Node runtime cases passed. PWA focused tests: 69 passed. Existing roofing runtime passed. Full local regression found one obsolete v102 assertion in the companion test; that test-only expectation was corrected to v103. Independent CI is required before release.
- Desktop card and mobile 390px card/follow-up have been visually reviewed using actual components and the live published profile. No horizontal overflow. Public directory is independently visible on the canonical live domain with the correct CTA and mobile.
- Read-only display script scripts/qa/insurance_partner_display.cjs is reproducible, uses public profiles only, and never sends customer packets or external communications. Its screenshots are labeled display checks, not completed-customer-flow evidence.

## Remaining completion evidence

- Exact-head CI, merge and one intentional production release.
- Canonical asset byte comparison, final desktop/mobile captures and completion email draft readback.
