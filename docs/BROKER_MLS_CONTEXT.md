# Broker-authorized MLS context

HomeOfferFlow can add listing context without buying a national data-vendor
contract. The preferred first integration is one broker-authorized local MLS
feed, exposed through a small broker-controlled RESO proxy.

## Why this is the low-cost path

- The broker uses its existing MLS authorization rather than HomeOfferFlow
  purchasing nationwide coverage.
- The browser never receives an MLS credential.
- HomeOfferFlow asks for one compact property-context lookup only when an
  eligible agent deliberately requests it.
- The integration is provider-neutral: a future MLS change is a proxy/config
  change, not a customer-workflow rewrite.

## Cost decision

Start with one participating local MLS through the broker's existing
authorization. MLS Grid is the preferred first option where the local MLS
participates: MLS Grid states that it does not charge a separate Grid license
fee, although the MLS or broker may have its own access or licensing charge.

| Product need | Lowest-cost approach | Avoid at launch |
| --- | --- | --- |
| Confirm a property while preparing or reviewing a packet | One broker-authorized MLS Grid or RESO lookup, requested only for that property | A nationwide data-vendor contract |
| Let a consumer browse every active listing | Defer until search demand proves it | A public IDX portal with duplicate search features and recurring display fees |
| Keep infrastructure use low | Return the compact facts below; do not store or repeatedly refresh listing payloads | Full listing payloads, remarks, photos, or background refresh jobs |

This keeps the first release focused on better transaction guidance rather
than turning HomeOfferFlow into a listing portal. Before activation, confirm
the local MLS's permitted fields and brokerage data-use terms.

## Activation contract

Keep all three server-side values unset until the broker has authorized the
connection:

```text
ENABLE_BROKER_MLS_CONTEXT=true
BROKER_MLS_CONTEXT_URL=https://broker-controlled.example/mls-context
BROKER_MLS_CONTEXT_TOKEN=<server-only secret>
```

The proxy receives a `POST` body with a property address/city/state/ZIP and a
limited requested field list. It returns:

```json
{
  "listing": {
    "listingId": "string",
    "status": "string",
    "listPrice": "string",
    "daysOnMarket": 0,
    "priceChanges": "string",
    "marketEvidence": ["string"],
    "limitations": ["string"]
  }
}
```

This contract intentionally excludes remarks, agent-only details, display
assets, and a full IDX payload. It is for a compact offer-review context—not a
public listing-search product. The proxy is responsible for enforcing the
broker's MLS agreement, permitted fields, retention, rate limits, and audit
requirements.

## Product behavior

The AI review endpoint accepts `includeBrokerMlsContext: true` only as an
explicit request. If the approved broker connection returns a listing, its
context is used in preference to public-web grounding, avoiding a second model
request. If it is not configured or unavailable, HomeOfferFlow continues with
the ordinary review path and does not claim MLS verification.

RESO defines the transport standard; actual data access and credentials come
from the local MLS under its data-use rules. See
https://www.reso.org/reso-web-api/.
