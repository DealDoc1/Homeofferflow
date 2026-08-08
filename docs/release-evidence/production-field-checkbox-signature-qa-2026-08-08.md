# Production 20-19 Field, Checkbox, and Signature QA

Date: 2026-08-08

## Scope

This QA records the final production-readiness check for the already deployed 20-19 offer-generation runtime. It covers the supported purchase-offer packet paths and the seller temporary lease path. Restricted Texas Realtor TXR sources remain preview-only and are not activated by this release.

## Verification performed

- Full Python suite: 519 tests passed.
- Targeted signer and packet tests: 21 tests passed.
- Golden rendering check: all approved scenarios matched the committed visual baseline:
  - cash single buyer
  - cash two buyers
  - conventional financing (single and two buyers)
  - HOA
  - appraisal
  - sale of other property
  - backup contract
  - seller temporary lease
  - all supported addenda
  - sparse optional fields
- Representative packets were rendered with Poppler and visually inspected page-by-page:
  - cash packet: 12 pages
  - all-supported-addenda packet: 20 pages
  - seller temporary lease packet: 14 pages
- Signer geometry tests confirmed signature/date field page assignments and bounds.
- Existing completed seller-temporary-lease signed-PDF evidence was rechecked: buyer and seller signatures, dates, initials, contract fields, lease terms, notices, and contact fields were readable and seated in their intended areas.
- Production deployment was checked live: the canonical site, launch path, legal-policy pages, and packet runtime returned HTTP 200; `/api/fill-pdf.py` reported `20-19 production`, release `18B-controlled-launch`, all supported packet PDFs present, `uploaded_docs_append_enabled: true`, `unsupported_paths_rejected: true`, and live SignWell configuration. The PWA smoke check passed.

## Result

The supported 20-19 purchase-offer and seller-temporary-lease runtime is production-ready based on the checks above. No coordinate changes were made in this QA pass.

The following remain intentionally gated and are not represented as production-ready:

- TXR-1501, TXR-1506, TXR-1507, and TXR-1508 restricted Realtor-form workflows.
- Any restricted form send/sign flow without authenticated point-of-use preview QA and a controlled completed signed-PDF visual QA artifact.

## Deployment note

The current production deployment is the verified runtime deployment from commit `0c66ef3` (`[deploy-production] Publish PWA service-worker CSP fix`). Later main-branch commits in this window are documentation, tests, and tracker metadata only; they do not change the production packet runtime and do not justify spending another Vercel Hobby deployment.
