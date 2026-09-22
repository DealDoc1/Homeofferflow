# Plain-language document and workspace errors — 2026-09-22

## Scope

- Prevent raw database, API, authentication-token, constraint, and service-provider details from appearing in customer-visible error regions.
- Give agents and brokerage users a clear recovery action when document preparation, signature delivery, previews, downloads, form-library access, or brokerage settings fail.
- Preserve the specific delivery-unconfirmed instruction when the server marks a SignWell delivery result as uncertain, so a user checks status before retrying instead of creating a duplicate request.
- Keep full error objects in browser console logging for diagnosis.

## Verification

- Focused plain-language, account, document, packet, brokerage, SignWell-recovery, inline-script, and browser-runtime coverage: 112 tests passed.
- Customer error-filter runtime coverage confirms short actionable instructions remain visible, technical details are replaced, and interactive recovery controls are preserved.
- Full local suite: 2,430 of 2,431 tests passed. The only failure is the existing local cross-language assumption-checkout preflight environment mismatch; its direct Python and Node preflight coverage passes, and the same full suite passes in GitHub CI.
- `git diff --check` passed.

## Release boundary

- No PDF, field mapping, packet composition, source-form, database schema, billing, or provider-send behavior changed.
- Production deployment is intentionally deferred for bundling with the next verified release to minimize Vercel usage.
