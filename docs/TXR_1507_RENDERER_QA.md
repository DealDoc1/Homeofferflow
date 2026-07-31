# TXR-1507 Short Form Renderer QA

This document records draft-rendering QA only. It is not completed-signature
QA and does not authorize a SignWell release.

## Authorized source

- Private source: `TXR1507.pdf`
- Revision printed on source: `(TXR-1507) 06-15-26`
- Pages: 2
- Source remains outside the public repository and is fetched only from the
  private brokerage form-source vault in the eventual server workflow.

## Draft scenarios rendered and visually inspected

| Scenario | Page 1 | Page 2 | Result |
|---|---|---|---|
| One buyer, Full Services, purchase percentage, intermediary authorized | Client/broker, market area, dates, Full Services, purchase percentage | Authorized intermediary, printed names/license fields | Draft render usable; signatures intentionally blank |
| Two buyers, Full Services, purchase flat fee, intermediary not authorized | Two clients, dates, Full Services, flat fee | Not-authorized intermediary, both client printed-name fields | Draft render usable; signatures intentionally blank |
| One tenant, Showing Services, lease percentage, intermediary not authorized | Showing Services, execution fee, lease percentage | Not-authorized intermediary, tenant printed name | Draft render usable; signatures intentionally blank |

## Validation coverage

- Missing source PDF is rejected.
- Wrong source page count is rejected.
- Unrecognized source revision is rejected.
- Missing or invalid market area, dates, service level, intermediary choice,
  client count, compensation, or showing fee is rejected before rendering.
- Duplicate client names are rejected.

## Remaining release gate

Before this becomes an agent-facing workflow:

1. Render all six planned source scenarios, including both lease compensation
   variants and both intermediary choices.
2. Confirm broker/associate signer responsibilities against the authorized
   source and product policy.
3. Add private generated-PDF storage and agent-only retrieval.
4. Produce completed SignWell staging packets with the approved signer plan.
5. Visually inspect every printed field, checkbox, initial, signature, and date
   on each completed packet.
6. Only then enable the send/sign action and deploy the bundled release.
