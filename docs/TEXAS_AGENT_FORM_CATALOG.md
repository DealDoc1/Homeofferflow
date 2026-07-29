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

## What HomeOfferFlow supports today

| Workflow | Current scope |
| --- | --- |
| Buyer-side purchase packet | TREC 20-19 buyer offer workflow and its verified purchase addenda |
| Buyer temporary possession | TREC 16-7 Buyer Temporary Residential Lease |
| Seller temporary possession | Staging-verified only; not unlocked in production yet |
| IABS | Agent-owned, private profile PDF; optional per-packet attachment, never automatic |
| Seller/listing documents | Existing PDF uploads may be appended when appropriate; HomeOfferFlow does not generate or send standalone seller-side forms yet |

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
