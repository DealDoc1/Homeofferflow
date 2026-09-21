# Saved-offer answer and autosave isolation

Status: implemented and locally tested; not deployed or browser-verified.

## Customer-facing correction

- Reopening a saved offer replaces the previous offer's interview answers rather
  than merging them. Missing and intentionally blank values clear old controls,
  including buyer emails, repairs, property details, and conditional choices.
- Reuse Terms retains the existing allow-list of reusable terms and clears
  client/property details and prior payment selection. No extra customer step.
- Saved appraisal, HOA, listing-context, survey, and broker-fee answers restore;
  zero amounts remain zero. Agent quick fields match the saved agent details.
- Account defaults fill empty controls without overriding saved title-payer,
  survey, or financing elections. Existing preferred title-office defaults and
  Google Places integrations remain in place.
- Interview restoration is synchronous and suppresses intermediate autosaves.
- Each in-flight cloud save retains its original offer ID and account ID.
  Switching offers cannot redirect an old payload to the newly opened offer.
  Late completion cannot replace the current draft ID or report the wrong offer
  saved. Account changes also prevent a subsequent write after a pending read.
- Prepared/sent packet copy protection, owner/deletion filters, and the
  last-updated compare-and-set check remain intact. No schema or RLS change.

## Verification

Local baseline: `165bc9a2`.

1. `node --test tests/offer_autosave_switch.runtime.cjs tests/offer_restore_isolation.runtime.cjs`
   — 13 tests passed. These execute extracted application JavaScript against
   lightweight DOM and deferred Supabase query doubles, not a real browser.
2. The same tests with `HOF_TEST_SOURCE_REF=HEAD` before this commit — 12 failed
   on the baseline; the ordinary same-offer save control passed. Failures assert
   wrong offer IDs, stale answers, overwritten elections, or incorrect status.
3. `PYTHONPATH=.:/private/tmp/hof-signing-retry-deps python3 -m unittest discover -s tests -q`
   — 1,994 passed. Existing customer-audience and hydrostatic test harnesses now
   include the required read/helper dependencies; their assertions remain.
4. `git diff --check` — passed.

Supabase guidance informed preservation of explicit ownership filters and
account-switch checks. Current update documentation and changelog reviewed:
https://supabase.com/docs/reference/javascript/update
https://supabase.com/changelog
No relevant SDK/API behavior change was needed; no new dependency added.

## Limits and release status

No customer records, emails, signatures, payments, or production configuration
were changed. No GitHub push or Vercel deployment/build was started. Existing
release spending and publication restrictions remain in effect.

Authenticated live-database verification and browser end-to-end verification
remain unperformed for this batch. The earlier Supabase roadmap reads returned
connector errors; no live roadmap status was changed. Local browser access was
previously rejected by browser policy and was not retried through a workaround.

The existing daily-report automation was read and remains active at 08:00 for
the current thread. This evidence is for that report; it is not a claim that
the production roadmap is complete.
