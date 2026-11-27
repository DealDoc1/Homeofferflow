# Find saved purchase offers by co-buyer

November 27, 2026. Implemented locally, focused tests passed, functional rendered
UX reviewed. Not deployed or production verified.

## Outcome and scope

The shared authenticated offer-history/detail projection discarded co-buyer
names. The web workspace also searched only the primary buyer. Agents could
miss an existing saved transaction when searching by its second buyer, and
the native app's advertised co-buyer search lacked this name in API-loaded rows.

The projection now returns a canonical `buyer2_name`, preferring a nonblank
top-level name and otherwise the existing `offer_data.buyer2` or legacy
`offer_data.buyer2Name`. It accepts strings only, trims whitespace and bounds
the output to 200 characters. The existing owner and deleted-row restrictions,
pagination and API response shape are preserved with this additive field.
Secondary email/contact data stays excluded. No schema migration is needed.
A read-only production catalog check confirmed the existing buyer2_name column.

Web search includes this canonical name and existing cached/legacy name fields
in its existing all-terms matching. No layout or customer-facing copy changed.
No native code change is needed to consume the canonical summary name.

The current verified production baseline remains seller release
`6d66e3e1cc600e5d26f9b60ebeb498851bbb2b60`. No source PDF, signer map, billing
configuration, permission, customer record or external message changed.

## Focused verification

New API and rendered-search regressions failed before implementation. The
API cases cover source precedence, blank/malformed names, legacy names, length
limits, missing names and exclusion of secondary contact details. The runtime
test executes the actual index.html workspace script and inspects rendered
offer cards and result feedback, including normalized accented names,
cross-field matching, names belonging to separate offers, clearing and focus.

Using the pinned project Python:

```sh
python -m unittest tests.test_agent_offer_history_api \
  tests.test_agent_offer_detail_api tests.test_offer_workspace_search \
  tests.test_offer_workspace_export tests.test_offer_history_timeline_merge \
  tests.test_offer_history_concurrency -q
```

19 tests passed. Patch whitespace passed. An initially appended fixture inherited
the prior test's summary focus; setting the fixture's typing focus explicitly
corrected that setup without changing application behavior.

This was functional rendered-DOM UX review, not native-device or live browser
visual review. The browser remains handed to the owner for Expo sign-in.
Full regression, installed-shell versioning and normal release/cost checks
remain for the isolated production candidate. No build or deployment occurred.
