# Incoming offer and disclosure review

Candidate based on `17fd68d3`. The listing-side offer comparison now lets
agents record findings for the water provider, the payer and receiving broker,
addenda and notices, and the Seller’s Disclosure Notice. The notice check
provides the official TREC link and asks the agent to compare the printed
edition and signing date with brokerage requirements. Findings are preserved
with contingency notes and the copied seller summary. Switching workspaces
prevents stale findings or offer rows from appearing in a different listing.

The purchase workflow also lets agents check the form edition for a PDF
labeled Seller’s Disclosure and repeats the reminder during offer review.
The PDF preview uses the original local bytes. The existing storage and
transaction routes, signing fields, and packet assembly remain in use.
These are guided manual checks. The application does not infer the edition
or signing date from an uploaded document.

54 focused tests passed, covering the existing listing workspace, offer
review, and PWA behavior. Offline Chrome at 390px and 1280px verified the
incoming findings, persistence through the mocked existing query/insert
contract, copy, recovery, stale-workspace isolation, private PDF preview,
official link, focus restoration, and relabeling. No deployment or live
record write took place. Shell v197 is local.
