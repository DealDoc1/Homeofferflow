# HomeOfferFlow - Texas Agent Form Catalog and Release Order

## Purpose

This is the implementation catalog for the OnDemand agent launch. It separates
what HomeOfferFlow can generate today from the next forms that agents commonly
need. A form is not presented as supported until its approved source, field
mapping, signer plan, rendered-PDF QA, and production regression are complete.

## Source forms reviewed

The following Texas REALTORS® member forms were supplied and reviewed on July
29, 2026. Their own licensing notice controls use of the source material.

| Form | Version shown | Pages | Product role |
| --- | --- | ---: | --- |
| TXR-1501 Residential Buyer/Tenant Representation Agreement - Long Form | 06-15-26 | 6 | Full buyer or tenant representation agreement |
| TXR-1506 General Information and Notice to Consumers | 06-15-26 | 6 | Consumer education and acknowledgement workflow |
| TXR-1507 Residential Buyer/Tenant Representation Agreement - Short Form | 06-15-26 | 2 | Short-form buyer or tenant representation agreement |
| TXR-1508 Unrepresented Customer Showing Form | 02-25-26 | 1 | Limited, no-representation showing access workflow |

The July 28, 2026 Texas REALTORS® blank-form list was also reviewed. It
confirms the adjacent residential listing, seller disclosure, leasing, and
transaction follow-up form families below.

## Additional form families confirmed by the supplied inventory

The supplied inventory is a catalog of available member forms, not a license
to reproduce every form in the product. These are the next Texas residential
workflows that matter for an agent launch:

| Priority family | Confirmed forms | Product implication |
| --- | --- | --- |
| Listing-side representation | TXR-1101 Residential Listing Agreement - Exclusive Right to Sell; TXR-1102 Residential Listing Agreement - Exclusive Right to Lease | Separate sale-listing and lease-listing workflows; neither is an offer addendum. Exact source PDFs and signer plans remain required before activation. |
| Seller disclosures | TXR-1406 Seller's Disclosure Notice; TXR-1418 Update to Seller's Disclosure Notice; TREC-55-1; TREC-61-0 | Keep seller disclosure preparation separate from the buyer offer question. Universal review-only TREC-55-1/TREC-61-0 drafts are live for every authenticated agent; TXR-1406/TXR-1418 remain separately source-gated. |
| Buyer relationship | TXR-1501, TXR-1507, TXR-1508, TXR-1506 | These supplied exact PDFs are already source-vaulted and have private preview foundations; signing remains gated by authenticated and completed-PDF QA. |
| Leasing | TXR-2001 Residential Lease; TXR-2003 Residential Lease Application; TXR-2011 Multi-Family Lease; TXR-1910 Seller's Temporary Residential Lease; TXR-1911 Buyer's Temporary Residential Lease | The temporary-lease execution path is live for the supported purchase scenario. Full landlord/tenant leasing needs its own workflow and signer plan. |
| Agent disclosures and notices | TXR-2501 IABS 1-2; TXR-1409 Intermediary Relationship Notice; TXR-1417 Representation Disclosure; TXR-1504 Notice from Buyer's Agent to Seller | IABS remains an agent-owned profile document with optional packet inclusion. The other notices require separate source, role, and delivery rules. |
| Transaction follow-up | TXR-1503 Termination; TXR-1505 Amendment; TXR-1903 Amendment of Contract; TXR-1902 Notice of Buyer's Termination; TXR-1958 Critical Date List; TREC-62-0 Seller Notice of Backup Contract Termination | Build after the relationship and listing foundations; each form needs its own data model and regression scenario. TREC-62-0 is locally inventoried but remains source-gated. |

The inventory also confirms specialized addenda such as seller financing,
loan assumption, residential/fixture leases, hydrostatic testing, minerals,
environmental assessment, HOA/PID notices, and property-condition notices.
Those remain intentionally sequenced after the core relationship, listing,
disclosure, and lease workflows. No form is enabled merely because it appears
in the inventory.

## Inventory reconciliation - 2026-08-08

The supplied 13-page Texas REALTORS(R) blank-form inventory was reconciled
against this catalog. The following high-value residential forms were present
in the inventory but were not previously called out as explicit roadmap items:

| Form | Why it matters | Decision |
| --- | --- | --- |
| TXR-1503 Termination of Buyer/Tenant Representation Agreement | Relationship lifecycle close-out | Add immediately after TXR-1501/1507; requires the originating agreement and signer context. |
| TXR-1505 Amendment to Buyer/Tenant Representation Agreement | Relationship lifecycle changes | Add with TXR-1503; never silently alter the original agreement. |
| TXR-1925 Buyer's Walk-Through, Confirmation, and Acceptance Form | Common pre-closing buyer workflow | Add to the transaction follow-up release after amendments/termination. |
| TXR-1958 Residential Contract Critical Date List | Deadline tracking and client-facing clarity | Add as a generated checklist only after the underlying contract dates are confirmed. |
| TXR-2517 Wire Fraud Warning | High-value transaction safety notice | Add to the buyer/listing intake checklist as an explicit acknowledgement workflow. |
| TXR-1904 Release of Earnest Money | Common post-termination follow-up | Add after termination workflows and define all payee/signature roles. |
| TXR-1902 / TXR-1945 / TXR-1950 | Buyer termination, offer withdrawal, and seller termination paths | Add as separate role-specific workflows; never collapse them into one generic termination button. |
| TXR-1912 | Sale-of-other-property contingency notices | Add with the existing sale-contingency packet, with buyer/seller notice recipients explicit. |
| TXR-1407 / TXR-1421 / TXR-1420 | Sewer, property-condition, and special-taxing-district disclosures | Add to listing/seller disclosure intake, not the buyer offer wizard. |
| TXR-1502 | Commercial buyer/tenant representation | Capture as a later commercial product track, separate from residential TXR-1501/1507. |

The inventory also includes extensive commercial leasing, property-management,
farm-and-ranch, and historical notice forms. They are cataloged as future
coverage rather than launch scope. Their presence does not authorize
reproduction or production distribution. Each still requires an exact source,
authorized-use record, signer plan, rendered QA, completed signed-PDF QA, and
release approval.

## What HomeOfferFlow supports today

| Workflow | Current scope |
| --- | --- |
| Buyer-side purchase packet | TREC 20-19 buyer offer workflow and its verified purchase addenda |
| Buyer temporary possession | TREC 16-7 Buyer Temporary Residential Lease |
| Seller temporary possession | Production: TREC 15-7 Seller Temporary Residential Lease, with buyer/landlord and seller/tenant execution routing and completed-signature visual QA |
| IABS | Agent-owned, private profile PDF; optional per-packet attachment, never automatic |
| Seller/listing documents | Universal TREC-55-1/TREC-61-0 review-only drafts are available; listing agreements and seller signature requests remain outside the live scope |

## Recommended release order

### Release A - Buyer relationship and showing workflows

1. **TXR-1507 Short Form** - provide the fastest guided buyer/tenant
   representation workflow, with the agent explicitly selecting it.
2. **TXR-1501 Long Form** - provide the complete representation option for
   agents who select it; it must remain a separate mapping and QA release.
3. **TXR-1508 Unrepresented Customer Showing Form** - provide a clearly
   limited no-representation showing path, never disguised as buyer agency.
4. **TXR-1506 General Information and Notice to Consumers** - provide it as a
   standalone acknowledgement workflow, not as an automatic purchase-packet
   addendum.
5. **TXR-1503 Termination** and **TXR-1505 Amendment** - add follow-up actions
   only after the corresponding representation agreements are live.

### Release B - Listing-side core

1. **TXR-1101 Residential Real Estate Listing Agreement, Exclusive Right to
   Sell**.
2. **TXR-1406 Seller's Disclosure Notice**, then **TXR-1418 Update to Seller's
   Disclosure Notice**.
3. **TXR-1102 Residential Real Estate Listing Agreement, Exclusive Right to
   Lease** for the landlord/listing path.
4. **TXR-1402 Named Exclusions**, **TXR-1403 Exclusive Agency**, and
   **TXR-1404 Amendment to Listing** as targeted listing follow-ups.

### Release C - Residential leasing foundation

1. **TXR-2003 Residential Lease Application**.
2. **TXR-2001 Residential Lease** and **TXR-2011 Multi-Family Residential
   Lease**.
3. Supporting forms only after the core lease workflow: TXR-2004 Animal
   Agreement, TXR-2006 Inventory and Condition, TXR-2007 Guaranty,
   TXR-2014 Lease Amendment, TXR-2015 Rental Flood Disclosure, and
   TXR-2016 Tenant and Occupant Information.

## Guardrails for every release

- Keep the form's source, revision date, and authorized-use condition on file.
- Do not preselect a legal agreement type, compensation structure, exclusive
  term, or other material business term for an agent.
- Give the agent a clear document-specific review step before sending.
- Define every signer and signing order before placing SignWell fields.
- Visually inspect every relevant blank, checkbox, initial, signature, and date
  on a rendered signed test packet.
- Keep buyer, seller, tenant, landlord, and brokerage data isolated by role.
- Do not market a workflow as available until it passes production QA.

## Immediate build target

TXR-1507, TXR-1501, TXR-1508, and TXR-1506 now have separate private,
source-gated draft foundations. Each preserves its own scope: representation,
unrepresented showing, or general consumer notice. None is an
executable/signable workflow until its own source approval, field mapping,
signer plan, and rendered QA are complete.

The source vault now also accepts source-owner-authorized private sources for
the first listing-side catalog forms (TXR-1101, TXR-1102, TXR-1406, and
TXR-1418). This works for any brokerage or verified organization; it is not an
OnDemand-specific product permission. Seller/listing generation and signing
remain unavailable until their separate release gates pass.

## TXR execution readiness

The next executable document is **TXR-1507 Short Form**, because it is the
smallest complete buyer/tenant-representation workflow and establishes the
reusable standalone-agreement pattern. Its private draft intake, data
validation, source-vault checks, and agent UI are already in place. Before it
can create or send a document, HomeOfferFlow must record authority to use the
exact source, map the private source revision, define its signer/initial plan,
and complete rendered, signed QA.

The other supplied TXR forms remain sequenced as follows:

1. TXR-1507 Short Form — executable buyer/tenant relationship workflow.
2. TXR-1501 Long Form — separate six-page relationship workflow; never a
   fallback or automatic substitution for the Short Form.
3. TXR-1508 — strictly limited unrepresented-customer showing workflow.
4. TXR-1506 — standalone consumer notice/acknowledgement, never automatic in
   an offer packet.
