# TXR private-preview repair and golden regression — 2026-08-27

## Scope

This evidence records the repaired isolated HomeOfferFlow preview used for the
remaining controlled TXR signing QA, plus a fresh full regression of the
currently supported buyer-offer packet catalogue. It does not represent any
of the restricted TXR workflows as generally released for signature.

## Repaired preview

| Item | Evidence |
| --- | --- |
| Preview deployment | `dpl_FvkEGhvWMVuEYpcJpHXzbMgu8mfU` |
| Preview URL | `https://homeofferflow-orarzjybv-dealdoc1s-projects.vercel.app` |
| Source commit | `0427e1de00afdb1cd82afabc13db0d05fa4f75cd` |
| Deployment status | Ready |
| Repair 1 | Private-source previews tolerate an absent host-brokerage row while preserving the independent authorization requirement for sending. |
| Repair 2 | Private previews and signing use `hof_agent_profiles` for agent identity rather than the incompatible `hof_profiles.agent_name` lookup. |
| Focused local regression | 47 tests passed across the standalone-agreement foundation and TXR-1501/1506/1507/1508 renderers and signing path. |
| Full local regression | 1,331 tests passed. |

## Golden visual-regression recheck

Command:

```text
scripts/check_golden_packet_rendering.py --structural-only
```

Result: passed. All eleven approved supported scenarios rendered and matched
the committed baseline for page counts and signing-field identifiers:

- cash single and two-buyer packets;
- conventional single and two-buyer packets;
- HOA, appraisal, sale-of-other-property, and backup addenda;
- seller temporary residential lease;
- all supported addenda stress packet; and
- sparse optional-field packet.

Two existing parser notices (`Ignoring wrong pointing object 9 0`) appeared
while rendering the sale-of-other-property and all-supported-addenda fixtures.
They did not change the successful baseline comparison and are retained here
for traceability.

## Remaining controlled QA

The next evidence is not yet complete: authenticated draft preview and the
completed SignWell PDF visual inspection for TXR-1501, TXR-1506, TXR-1507,
and TXR-1508. That final run must inspect every applicable mapped blank,
checkbox, initial, signature, and date in the completed documents before the
workflows are described as generally signature-ready.
