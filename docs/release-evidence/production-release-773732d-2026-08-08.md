# Verified production release — 773732d — 2026-08-08

## Scope

This intentional release promotes the verified HomeOfferFlow runtime and
brokerage/agent enhancements from `main` to production. It preserves the
protected purchase-offer mappings and existing SignWell packet behavior.

## Deployment evidence

- Repository: `DealDoc1/Homeofferflow`
- Release commit: `773732de53792b031c09621e8ac275f42535bcc0`
- Commit author: `Andrew Christian <andrewchri@gmail.com>`
- Commit message: `[deploy-production] Promote verified HomeOfferFlow release`
- Vercel deployment: `dpl_8mxYMAJBCvNsdTqGibUceT5D6ZNJ`
- Vercel state: `READY`, target `production`
- Canonical aliases: `https://www.homeofferflow.com/`, `https://homeofferflow.com/`

## Verification

- Full local regression suite: **513 tests passed**.
- Release preflight against the previous live commit: **passed**.
- Production PWA smoke check: **passed**.
- Production runtime error check for the selected hour: **no runtime errors**.
- OnDemand launch page: 60-day free trial, `$29/month`, card required,
  cancel-anytime copy present.
- Seller Temporary Residential Lease completed packet: fields, checkboxes,
  initials, signatures, and dates visually inspected and passed.

## Restricted-form boundary

TXR-1501, TXR-1506, TXR-1507, TXR-1508, TREC-55-1, and TREC-61-0 remain
fail-closed for production send/sign. Their supplied source PDFs and unsigned
draft renders passed local visual inspection, but authenticated point-of-use
preview QA and controlled completed-signature visual QA are still required
before any of those workflows can be activated.
