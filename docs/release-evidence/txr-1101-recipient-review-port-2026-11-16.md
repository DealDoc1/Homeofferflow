# TXR-1101 recipient review and verified send on the production baseline

Continues the isolated listing candidate after `db572dd4b`. The same
owner-scoped endpoint used by the dashboard now returns the sellers,
the selected broker or associate, and the actual packet page count and
included/pending documents. An unanswered foreign-person field returns
the existing edit-required response before rendering. Send revalidates
recipients, the saved signing map and the reviewed packet fingerprint
before creating a private SignWell draft. It checks provider field and
recipient readback and, where applicable, the exact-one and conditional
lead-disclosure controls before inviting any signer. The existing durable
retry path retains one provider document and simultaneous invitations.

114 focused tests passed in the candidate, covering exact-source PDF and
fake-transport API requests through save, preview and send, existing
standalone recipient review, provider readback, changed attachments,
missing or malformed fingerprints, changed recipients and retry. No
real provider request ran. The dashboard still needs to pass the packet
fingerprint, display the packet summary and reopen the listing interview
when the response requires an answer. Completed fictional provider PDF
review and coordinated release verification still apply.
