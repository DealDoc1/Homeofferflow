# Seller/listing workspace foundation

This foundation separates agent-owned seller/listing intake from buyer offers
and from legal-form drafts. It supports a sale or lease workspace, property
address, one-to-four seller names, requested workflow labels, and confidential
agent notes. Agents can produce a private Seller Listing Launch Checklist and
Seller Consultation Brief from the selected workspace. Both are practical
conversation/planning aids; neither creates representation, determines price,
or causes a document or signing event.

The private offer-comparison workspace also has an optional Estimated Seller
Proceeds Worksheet. It uses only the agent's own payoff and cost estimates plus
saved offer price/concession values. It intentionally labels the result as an
estimate before unentered items: it is never a closing statement, valuation,
offer ranking, or recommendation, and it is not persisted separately.

## Privacy model

- Agents can read and update only their own workspaces.
- An active brokerage administrator gets aggregate sale/lease/status counts
  only, through a dedicated function.
- The broker summary does not return seller names, property addresses, notes,
  pricing, or form/document contents.

## Release gate

Creating a workspace does not create representation, a listing agreement, a
seller disclosure, a PDF, or a signature request. Listing-side form execution
remains blocked until an authorized source, field map, signer plan, rendered
completed-PDF QA, and HomeOfferFlow release-authority approval are complete.
A customer organization attestation is required only when it owns the private
source.
