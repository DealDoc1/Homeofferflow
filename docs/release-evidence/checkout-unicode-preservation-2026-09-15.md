# Checkout offer text is preserved across metadata chunks

## Confirmed defect and fix

Checkout used `/.{1,450}/g` to split serialized offer data. JavaScript's dot
does not match Unicode line/paragraph separators, so those characters could
silently disappear from repair or legal-description text even though the
reassembled JSON remained valid. UTF-16 splitting could also separate the two
halves of an emoji across provider metadata values.

Splitting now iterates Unicode code points and keeps each metadata value at
most 450 UTF-16 code units. No content is normalized or discarded. Existing
metadata key names, ordering, and fulfillment reconstruction stay compatible.
The payments skill guided retaining the existing provider/payment contract.

## Verification

- Checkout runtime suite: 107 passing cases. Six new text-preservation cases
  cover both separator characters, accented/CJK names, emoji, combining marks,
  ordinary newlines, and an emoji at the exact chunk boundary.
- Against pre-fix `242e5fb1`, four cases fail and 103 existing/control cases
  pass. Each new chunk is checked for independent UTF-8 round-trip safety.
- A new Python integration test executes the actual Node checkout handler with
  a mocked Stripe SDK, transfers its real metadata into the actual Python
  `handle_checkout`, and asserts unchanged text at the PDF-rendering boundary.
  Rendering, persistence, signing, and email providers remain offline mocks;
  the test does not create or visually inspect a PDF or send customer mail.
- API syntax and `git diff --check` pass. Full local suite: **2,003 tests pass
  in 17.738 seconds**.

## Larger-packet follow-through — not complete

Stripe documents a maximum of 50 metadata entries and 500 characters per
value, recommending external storage and an object ID for larger data:
https://docs.stripe.com/metadata

This fix does not remove that limit. The current checkout sends inline offer
JSON, including uploaded PDFs, while the app supports up to 2.5 MiB of uploaded
PDF content. The current metadata design cannot cover that supported size.

Required next implementation: persist a private immutable checkout payload
before creating the payment session; send only its reference in Stripe
metadata; recover and verify that payload in the signed fulfillment path;
retain legacy metadata compatibility and retry behavior; verify service-only
access, missing/corrupt-payload failures, and supported-size attachment
round trips. No new paid service is needed if existing storage is used.

Do not report larger packets as fixed or test this by charging a customer.

## Release status

Local only. No push, Vercel build, deployment, live checkout, or customer email.
