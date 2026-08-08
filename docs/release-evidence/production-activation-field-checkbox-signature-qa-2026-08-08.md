# Production activation - field, checkbox, and signature QA - 2026-08-08

## Release decision

The supported HomeOfferFlow production workflows are activated and verified on
the current production runtime:

- TREC 20-19 purchase offer packets;
- supported financing, HOA, appraisal, sale-of-other-property, backup, and
  non-realty addenda;
- buyer and seller temporary residential lease packets;
- current SignWell recipient/signature routing for those supported packets.

The canonical production runtime reports release `18B-controlled-launch`,
TREC main form `20-19 production`, SignWell production mode, and all supported
packet assets present.

## Automated verification

- Full Python suite: **555 tests passed** (including seller-intake integrity and
  roadmap reconciliation coverage).
- Golden packet rendering: **approved baseline matched** for cash single/two
  buyer, conventional single/two buyer, HOA, appraisal, sale of other
  property, backup, seller temporary lease, all supported addenda, and sparse
  scenarios.
- Release preflight: **passed**; no pending packet/form source or field-map
  change is being deployed.
- Live production PWA smoke check: **passed**.
- Canonical production pages and API health endpoint: **HTTP 200**.
- Fresh live release check: `release=18B-controlled-launch`,
  `trec_main_form=20-19 production`, `signwell_test_mode=false`, and all
  public policy/launch pages returned HTTP 200.

## Rendered placement review

Fresh local renders were inspected visually, not inferred from text extraction:

- contract page 1: parties, property, price split, financing checkbox, lease
  checkboxes, and required blanks;
- contract execution page: buyer/seller signature and date lines;
- backup addendum signature page: buyer/seller signature lines;
- seller temporary lease page 2: notice fields, landlord/tenant fields, and
  signature/date lines.
- Current local render recheck also covered the all-supported-addenda packet's
  backup addendum page 1 and signature page, including the visible A(2) values,
  Paragraph G/H dates, and buyer/seller signature lines.

Existing completed signed-PDF evidence remains on file for the supported
purchase packet and seller temporary lease. Those completed packets confirmed
that signatures and dates land on their intended lines without footer/body
spillover.

## Restricted-form boundary

TXR-1501, TXR-1506, TXR-1507, TXR-1508, executable listing agreements, seller
disclosures, and lease-listing workflows remain fail-closed. They are not
represented as active production signing workflows because the required
authenticated brokerage-member preview, signer plan, and completed signed-PDF
visual QA are not complete for those restricted sources.

This boundary is intentional and protects users from receiving a form that has
not completed the source, authorization, field-placement, recipient, and
completed-signature gates.

## Deployment note

The verified main branch was intentionally promoted through the guarded
production workflow after the full regression and rendered-placement checks:

- verified runtime commit: `26f4e2a Harden seller lead intake privacy and validation`;
- Vercel deployment: `https://homeofferflow-cxfcayjys-dealdoc1s-projects.vercel.app`;
- Vercel deployment ID: `dpl_8qguYXEPjeUh6CWYw71GTGpCNqvJ`;
- GitHub Actions test run: `31258649426` (all jobs passed). The deployment was
  intentionally performed once from the verified main branch after the local
  placement/signature gates passed.

Git deployments remain disabled to stay within the Vercel Hobby deployment
limit; this was the single intentional production deployment.
