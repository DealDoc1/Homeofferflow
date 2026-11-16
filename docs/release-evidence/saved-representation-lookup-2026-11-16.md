# Find saved agreements from representation choices

The buyer and tenant representation choosers offer **Find a saved
agreement**. It opens Guided Forms and focuses Prepared Documents search.
The agent keeps their existing search terms and loaded rows. If the search
is grouped under Other transaction documents, it expands that section.
When the search is unavailable, focus moves to the Guided Forms heading.
A changed account or tab cancels pending focus.

Ported the previously tested application change from `7d77e6346` onto
production revision `b4a863b87`. The installed shell advances from v197
to v198 so installed browsers can receive the change.

Six Node runtime checks, 49 dashboard tests, and 19 PWA baseline tests
passed. Offline Chrome (390px buyer flow and 1280px tenant flow) exercised
the production dashboard launchers, grouped search, preserved query,
filtering fictional signed and draft rows, unavailable-search fallback,
and account-change focus suppression. No packet was created or sent.
The change uses the existing API and signed-in document access rules.
