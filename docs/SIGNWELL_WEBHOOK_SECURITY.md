# SignWell webhook security

HomeOfferFlow's `/api/signwell-webhook` verifies every production event before
it can update an offer or write an activity event.

## Required production environment variable

Set the webhook identifier returned by SignWell when the callback is created:

```text
SIGNWELL_WEBHOOK_ID=<SignWell webhook ID>
```

The older `SIGNWELL_WEBHOOK_SECRET` name is accepted only as a temporary
deployment compatibility fallback. Do not put the SignWell API key in either
variable.

## How verification works

SignWell's event payload contains `event.type`, `event.time`, and `event.hash`.
HomeOfferFlow calculates HMAC-SHA256 using the webhook ID as the key and
`type@time` as the message, then compares it in constant time. Events more than
five minutes old are rejected to limit replay exposure. Offer-status updates are
also idempotent, so a legitimate retry does not create a second state change.

## Deployment check

Before deploying this endpoint change:

1. In SignWell, retrieve the ID of the webhook that targets
   `https://www.homeofferflow.com/api/signwell-webhook`.
2. Set `SIGNWELL_WEBHOOK_ID` for Production and Preview in Vercel.
3. Send a SignWell test event and confirm the endpoint returns HTTP 200.
4. Confirm the associated offer's `signwell_status` refreshes and no buyer or
   document contents appear in function logs.

Do not disable verification to make a test event pass.
