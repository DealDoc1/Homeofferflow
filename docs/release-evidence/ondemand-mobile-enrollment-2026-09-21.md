# OnDemand mobile enrollment focus — September 21, 2026

## Outcome

The dedicated OnDemand Realty enrollment page now places the complete trial
card before the supporting marketing copy on phone and tablet layouts. Desktop
retains the existing side-by-side presentation. The change reduces the mobile
distance to the email field without adding a modal, intermediate question, new
account requirement, or additional page.

The privacy-safe `ondemand_email_started` signal now records the first email
field focus as well as the first input event. The existing session-level
deduplication still records at most one signal per browser session. This also
captures deliberate starts when browser autofill does not emit an input event.

## Evidence boundary

The production event ledger was read on September 21 before this change. Across
the preceding 90 days it contained 20 `ondemand_landing_viewed` events, one
`ondemand_trial_entry_selected` event, and no `ondemand_email_started`,
`ondemand_magic_link_requested`, or OnDemand subscription-checkout start
events. These are aggregate event counts, not verified unique visitors, and
some may be internal QA. They are sufficient to identify mobile distance and
intent-measurement as the next low-risk test; they are not evidence for a
pricing or demand conclusion.

## Scope and invariants

- No trial duration, $29 monthly price, card requirement, cancellation copy,
  Stripe route, Supabase authentication, legal acceptance, or eligibility rule
  changed.
- No customer identity, email address, property data, or free-form text was
  added to analytics.
- Desktop layout and the signed-in checkout state are unchanged.
- Automatic Git and preview deployments remain disabled. This change belongs
  in the single coordinated post-reset production release.
- The refreshed production manifest excludes a linked-worktree `.git` pointer;
  repository-control metadata is not part of the customer runtime bundle.

## Verification

- Focused OnDemand funnel tests cover responsive ordering, focus/input intent
  capture, and session-level deduplication.
- The full repository suite must pass on the exact merged commit.
- Production verification remains pending the coordinated release. After that
  release, inspect the canonical mobile layout and compare landing, email-start,
  magic-link, checkout, and first-transaction signals before changing pricing
  or adding another prompt.
