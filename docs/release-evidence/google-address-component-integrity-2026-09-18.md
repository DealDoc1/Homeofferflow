# Address component integrity - September 18

## Status and scope

Implemented and tested locally, not pushed or deployed. This extends the
shared Google address picker without changing providers, adding required
onboarding steps, or creating a paid resource. No live Places call, Vercel
build, or new signing request was made during this pass.

## Confirmed problems

- Purchase address filling skipped empty new components, leaving the previous
  property's city, county, or ZIP in place when Google omitted a value.
- Office and buyer-representation companion fields had the same stale-value
  behavior, and component parsing assumed Texas when no state was returned.
- Reconstructing addresses discarded the supplied apartment/unit and ZIP+4
  suffix, including the buyer's mailing address.
- The representation dialog's address control has a `name` but no `id`.
  Discovery found it, but callback lookup only used `id`, so its city/state/ZIP
  companion was not filled by the intended handler.
- Several programmatic address updates did not emit events for draft or
  progress listeners, or emitted them before all related fields were updated.

## Corrections

- Share component parsing across buyer mailing, purchase property, office,
  representation mailing, and seller-property handlers.
- Preserve unit numbers and postal suffixes; respect supplied non-Texas
  states and city-before-sublocality precedence. Component parsing no longer
  invents a state. The existing Texas purchase collector default is unchanged.
- Clear old companion fields at the start of a new selection, including the
  lookup-failure path. Missing details remain editable blanks instead of
  retaining values from a different property.
- Apply related values together before input/change events, preserving the
  existing autosave and progress listeners without triggering another search.
- Resolve callbacks and companion controls by either input ID or input name.
- Preserve the selected formatted fallback when components have no street
  route; a lone street number cannot replace the entire address.
- Keep the existing legacy Google compatibility path, but ignore empty place
  events and events from removed controls. It also clears stale companions.
- Do not flash empty missing components as successfully filled values.

## Verification

- Initial ten-case component test matrix reproduced eight failures in the old
  source. Final component matrix: eighteen pass in the new source; against
  `4017faf7`, two pass and sixteen fail. Some added tests cover helpers absent
  in the prior implementation; the initial eight failures directly reproduced
  incorrect field values or missing callbacks/events.
- Combined component and asynchronous-address matrix: **42 runtime checks pass**.
- The tests execute production functions with controlled DOM/provider doubles,
  including the actual `collectData()` purchase and buyer steps. Collected offer
  data contains the new address without the old county or ZIP, and buyer data
  retains the selected unit and postal suffix.
- Tests also exercise partial/failing lookups, name-only controls, legacy
  selection, removed controls, component-event consistency, and the prior
  out-of-order request protections. No external service is called by them.
- Final focused Python coverage: **51 tests pass** in 0.560 seconds.
- Final full discovery: **2,109 tests in 34.793 seconds; 2,107 pass and two
  fail**. These are the unchanged TXR-1507 approved-map reference checks still
  awaiting completed-provider placement verification. No additional full-suite
  regression failure was reported; this is not an all-green release claim.

Actual browser visuals, live Google behavior, production saving, and final
PDF output from a live address selection have not been verified in this pass.
No conversion, revenue, or dollar savings are claimed.

## Separate signing work

Refreshed the exact existing SignWell placement-test page. It still shows
**Sent**, not completed. The test tab remains available; no duplicate test,
reminder, or customer document change occurred. Completed-provider PDF visual
inspection and production release remain outstanding.
