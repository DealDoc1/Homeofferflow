# TXR-1101 private packet preview on the production baseline

Continues the listing release candidate based on production revision
`d39d4d19dfeae92830b9ae59ac85e28bb66584f2`. The existing authenticated
draft-preview endpoint now renders an owner-scoped TXR-1101 packet from the
approved exact source. It uses the agent's professional profile and saved
notice details, and can include the owner's saved IABS and the listing-side
lead disclosure. Responses are private and non-cacheable. Invalid and
unavailable draft previews receive a client error. The preview performs no
data writes or provider calls, and listing signing remains disabled.

72 focused tests passed across the listing API, exact-source renderer,
packet composer, lead disclosure and adjacent standalone recipient review.
The HTTP fixture exercised ownership, private storage, the non-cacheable PDF
response, and real composition with a fictional IABS and pre-1978 case.
Visually reviewed selected pages from nine exact-source HTTP previews,
including ordinary, single seller, broker vs. associate, delayed/off-MLS,
extra fees, Unicode, overflow, and lead disclosure and explanation pages.

Dashboard integration, current recipient review and signing, completed
SignWell PDF verification, and release checks remain. No production migration,
deployment, or invitation was made.
