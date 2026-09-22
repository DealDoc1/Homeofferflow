# Under-contract companion — September 22, 2026

## Customer outcome

- Adds a plain-language **Track accepted contract** action to generated, signing, and signed offers in My Offers.
- Reuses the saved, Google-completed property address; it adds no duplicate address entry.
- Asks the agent to confirm the effective date and target closing date from the fully signed contract.
- Calculates the option-period date from the confirmed effective date and the option-day count already saved with the offer.
- Saves the confirmed dates privately on that user's offer and creates one calendar file containing the effective date, option-period date, and target closing.
- Adds no subscription, vendor, or deployment service.

## Accuracy boundary

The companion is a reminder tool, not a deadline engine. It expressly tells the agent to use the fully signed contract and separately confirm earnest money and option-fee delivery, title, survey, financing, appraisal, disclosure, amendment, receipt-dependent, weekend, and legal-holiday deadlines.

The option-period reminder follows Paragraph 5B of TREC's One to Four Family Residential Contract (Resale), form 20-19, effective July 1, 2026: the option period is stated as a number of days after the effective date, and a termination notice must be given by 5:00 p.m. local time where the property is located. Source: `https://www.trec.texas.gov/forms/one-four-family-residential-contract-resale` and `https://www.trec.texas.gov/sites/default/files/pdf-forms/20-19_4.pdf`.

## Privacy and reliability

- The write is scoped to both the authenticated user ID and offer ID.
- The app reads the freshest stored offer data immediately before merging the new timeline, reducing the chance that another open tab overwrites newer offer details.
- Saving a timeline does not change the offer's top-level activity timestamp, so signing-age reminders remain accurate.
- Analytics record only the action and whether an option or closing date exists; dates, addresses, and party identities are not included.
- An analytics or workspace rerender failure cannot turn a successfully persisted timeline into a false save failure.
- The calendar is generated locally in the browser and contains no remote tracking.

## Verification

- Focused companion and PWA regression: 87 tests passed locally.
- Whitespace validation passed.
- Production status: not yet deployed. Merge, protected-main CI, and canonical browser verification remain required before this item is production-verified.
