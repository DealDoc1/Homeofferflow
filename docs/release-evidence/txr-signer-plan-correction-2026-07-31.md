# TXR signer-plan correction - 2026-07-31

## Finding

Rendered source review showed that TXR-1501, TXR-1506, and TXR-1507 each
contain a brokerage execution/signature line in addition to client or consumer
signature lines. The prior draft foundation allowed a client/consumer-only
plan, which could produce a draft that did not account for the source's
brokerage execution line.

## Change made

- TXR-1501 now accepts only `clients_and_associate` or `clients_and_broker`.
- TXR-1507 now accepts only `clients_and_associate` or `clients_and_broker` and
  returns explicit associate/broker signature/date fields in its signer map.
- TXR-1506 now accepts only `consumers_and_associate` or `consumers_and_broker`.
- The private-draft UI no longer offers client/consumer-only choices.
- Rejected legacy plans fail before a private draft can be created.

## Evidence

- The exact supplied source PDFs were rendered and reviewed page by page in
  `txr-source-render-review-2026-07-31-all.md`.
- The updated source-specific renderer and parser tests pass.
- The broader local suite passes with 92 tests.

## Release boundary

This is still draft-foundation work. The SignWell coordinates added for the
brokerage signer are provisional and have not been approved for production
send/sign. Before enabling any of these forms, the source owner must confirm
the signer order, the fields must be rendered against the exact private source,
and a completed signed PDF must be inspected visually. No production offer
packet or existing production signing flow is changed by this evidence.
