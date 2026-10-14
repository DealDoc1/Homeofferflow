# Account-aware homepage and truthful saved-offer actions

## Batch contract

- Outcome: an authenticated agent or investor sees the appropriate homepage promise once account restoration finishes; a visible buyer-offer Resume action actually resumes that saved offer.
- Scope: homepage presentation after existing account restoration, existing primary homepage CTA routing, actual-source runtime regressions, PWA shell v99 and matching cache assertions. No form, billing, permission, recipient, document or database behavior changes.
- Current production baseline: 4fe45d0850e7c072a16f0d9fdab0dd829e165fe4, READY dpl_j3Yp7492NRqXJt1EM4BEHtGU57qe. Vercel project read confirmed the current deployment and canonical root/www aliases.
- Cost constraint: automatic Git deployments remain disabled; one intentional existing prebuilt production release only. Read-only capacity run 38572885640 succeeded at 2026-10-14 13:35:02 UTC: five deployments in the last 24 hours, $0.04 infrastructure credit used, $19.96 unconsumed, $3 reserved for the September 22–October 21 cycle. This snapshot does not guarantee future usage.
- Completion evidence: focused actual-source tests, isolated desktop/390px phone browser review, frozen full regressions, exact-head CI, normal merge, intentional release, canonical source/worker comparison and safe production account/navigation checks.

## Reproduction and changes

- The canonical authenticated Agent Account entry already shows the agent page when reached through `?agent=1`. Its Start a Transaction button correctly opens the four-choice `/agents` page.
- Returning from that public chooser through its Home link initially renders the default buyer homepage. After the real Agent Account label resolves, buyer copy and $99 pricing can remain beneath it. Existing primary CTA logic routes an untouched authenticated agent to `/agents`, so presentation and action can disagree. A subsequently restored local buyer interview was also observed; that saved work must not be rewritten to fix presentation.
- The new presentation helper waits for actual auth/draft restoration and a ready authoritative profile. It only personalizes an untouched Homebuyer-default landing page, without modifying `state`, interview inputs or local storage. Agent/broker roles show the agent presentation; investor accounts show the investor presentation. Cached/user-editable role values are not used by this helper as proof of the account role.
- Explicit audience choices, existing restored drafts, resumable local drafts, an open wizard/seller intake and named transaction/customer/partner routes remain unchanged. The auth-ready event and subsequent UI refresh share the same guarded helper.
- Existing primary CTA handling now checks the owner-validated resumable buyer draft before the default agent redirect. A button relabeled Resume therefore reopens its promised offer instead of routing to the agent chooser. Explicit agent choices still enter the chooser and non-homepage actions do not silently resume a buyer draft.
- The existing owner/privacy checks in `resumableLocalOfferDraft` are unchanged. No new auth/database request, schema, policy, role, entitlement or paid service is introduced. Google address completion and simultaneous signing invitations are untouched.

## Local evidence

- 75 focused Python checks passed across audience isolation, customer audience restoration, homepage entry, draft resume, route recovery, account entry and affected PWA/companion tests.
- The actual-source Node audience-isolation suite passes 141 cases, including 35 new cases for verified role presentation, auth-ready/UI-refresh timing, later explicit Homebuyer selection, protected draft/route/modal states, all three homepage Resume surfaces and existing audience preservation. Existing four-path tests remain intact.
- An isolated local HTTP fixture assembled the current homepage markup/styles and actual presentation/helper functions, with a fictional ready agent profile and no live service calls. This is presentation QA, not a claim that a real Supabase account was created or modified. Desktop review confirmed checked Agent / Broker, agent headline, Start a Transaction and non-buyer pricing. The fixture's fictional saved offer state stayed byte-for-byte unchanged.
- At 390x844, the same fixture has page width exactly 390px and displays the intended agent hero/action/pricing. Selecting Homebuyer, then invoking another simulated auth-ready event, preserves the explicit Homebuyer selection and buyer CTA. The temporary viewport was reset and the temporary preview tab closed.
- No terms, e-sign disclosure, signing request, customer packet, email send, payment or external account setting was changed during QA. The real local saved draft was not deleted or replaced. Pending SignWell QA remains a separate workstream.

## Release status

- The initial full-run interpreter was not a real dependency-complete virtual environment; imports of pinned PDF/email libraries failed. That attempt is not counted as passing. A new isolated temporary Python 3.12 environment installed the checked-in test requirements without modifying the managed interpreter.
- The frozen runtime candidate passed all 2,622 Python tests in 86.147 seconds with one environment skip. Standalone signer geometry matches the approved baseline and the Supabase branch preflight reports no errors. No runtime change followed that full pass.
- Reviewed candidate/CI, merge, intentional release and canonical post-release evidence are pending. This document does not claim deployment before it happens.
