# Fresh-offer calculator and field reset

Status: locally implemented and tested; not deployed or browser-verified.

## Customer outcome

Fresh offers now use the same field-reset helper as saved-offer switching.
It clears the prior transaction's values and per-input edit flags, selected
address marker, validation flags/borders, radio-card styling, and plan UI.
Previously a field edited in the prior offer stayed marked as edited after
its value was cleared, preventing calculator suggestions in the next offer.

The shared reset also removes old calculator recommendation hints. Fresh
starts clear the prior packet's save-as-copy warning state. Existing reset
behavior still preserves the current terms checkbox and signed-in account,
clears transaction attachments, and deselects the payment plan. Saved profile
preferences are not erased and can populate the new offer normally, including
intentional zero values. Existing calculation formulas are unchanged.

## Verification

Baseline: `8d480d30`.

- Saved-offer/reset runtime suite: 37 passing cases, including seven new cases.
- Against the baseline: all seven new cases fail; 30 existing controls pass.
- Actual fresh-reset, hydration, profile-default, price-calculator and
  financing-calculator functions execute with mocked DOM/storage boundaries.
- Agent, investor, and homebuyer fresh starts regain the existing numeric
  suggestions after earlier fields were edited. Tests preserve both checked
  and unchecked terms states, account/session identity, zero preferences,
  title preference and transaction-state cleanup.
- Both fresh starts and saved-offer hydration clear obsolete hints and field
  validation/address markers. The test DOM now represents `style` as an
  object rather than copying HTML style strings into that property.
- Full suite: 1,997 passed in 16.268 seconds. The expected invalid fixture PDF
  diagnostic following `OK` is negative-case output, not a failing test.
- All 45 inline scripts parse; `git diff --check` passes.

## Release limits

No authenticated browser, live database, or production verification performed.
No customer messages, signatures, payments, documents, or external settings
changed. No GitHub publication or Vercel build/preview/deployment started.
No new dependency or recurring service cost. Record in the daily report as
locally tested and awaiting release, not deployed.
