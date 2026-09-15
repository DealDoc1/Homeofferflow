# Hydrostatic testing: interview and combined purchase packet

## Scope and status

Local implementation, not deployed or production-verified. Continues the source
renderer in commit `797f1e22`; the earlier foundation note remains a historical
snapshot. This work connects TREC 48-1 to the existing purchase workflow rather
than creating a separate document-order process.

Official source: https://www.trec.texas.gov/forms/addendum-authorizing-hydrostatic-testing-0
Source PDF: https://www.trec.texas.gov/sites/default/files/pdf-forms/48-1.pdf

## Customer experience

- The existing Addenda step asks whether a hydrostatic plumbing test is requested.
  Only a Yes answer reveals the risk-allocation question. Nothing selects liability
  terms for the user. A capped-buyer selection additionally asks for the amount.
- The form's three choices are preserved without adding an unsupported allocation
  of excess damages. The interview identifies the buyer-paid test and recommends
  consulting a licensed plumber about its risks, consistent with the source form.
- Property address and buyer identities are reused. Seller signing contacts share
  the existing closing fields or, for a Paragraph 4 lease, its existing contacts.
  No extra address field, brokerage-seat requirement, service, or plan is added.
- The review shows the selected risk and cap. Seller signing scope distinguishes
  hydrostatic-only packets from the existing seller-temporary-lease workflow,
  which also includes seller signatures on the purchase contract.
- Both generation entry points validate terms and distinct, complete signer
  identities. Amounts retain cents; deselection clears obsolete risk/cap values.
  Saved-draft restoration also clears previous seller contacts rather than leaving
  another offer's optional second signer in the inputs.

## Packet and signing behavior

- Assemble the existing contract/addenda, then Paragraph 4 lease forms, then the
  one-page hydrostatic form, then uploaded disclosures. Remains one combined PDF.
- Preserve editable canonical AcroForm values, widget values, and appearances.
  Namespace the hydrostatic fields to avoid ordinary form-name collisions.
- Select the hydrostatic checkbox in contract Paragraph 22 only when included.
- Derive signature positions from verified official source rectangles; use the
  actual absolute page after other generated addenda. Buyer IDs remain 1/2;
  Seller IDs remain 3/4. All invitations use `apply_signing_order: false`.
- Preserve all existing temporary-lease signature positions and source/render
  fingerprinting. Deselected Paragraph 4 seller answers do not override the
  currently displayed hydrostatic sellers.
- Include the source PDF explicitly in the function's deployment-file list.
  Git deployment remains disabled; no build or deployment was initiated.

## Verification

- Full Python suite: **1,992 passed** (includes the JS-runtime wrapper).
- Ten actual-JavaScript runtime checks cover syntax, conditional fields, money
  validation, signer validation, deselection, review text, draft restoration,
  accessible invalid-field markers, and both generation entry points.
- Ten combined-packet tests cover canonical/widget agreement and appearances,
  contract-checkbox geometry, all four buyer/seller count combinations, temporary
  leases, Paragraph 4 plus uploaded-file ordering, one-file concurrent delivery
  payloads, malformed/duplicate/conflicting signers, and source-file inclusion.
- `scripts/check_golden_packet_rendering.py --cross-platform`: existing twelve
  packet scenarios match the approved visual baseline. Baseline not rewritten.
- Visually inspected the new unsigned combined packet's contract page 9 and
  addendum page 13 at 1,250-pixel render size: correct checked box, readable reused
  address and capped amount, legal text unchanged, blank execution areas intact.
  This extends the three standalone source-form visual reviews recorded previously.
- `git diff --check`: clean.

The suite's deliberate invalid-PDF fixture prints `ERROR: Invalid fixture PDF`
after the successful unittest summary; it is not a failed test.

## Remaining verification and release work

Browser interaction is **not verified**. The dedicated browser CLI is unavailable,
and the connected browser rejected navigation to the local file under its URL
policy. No alternate browser, indirect navigation, or policy workaround was used.
The runtime tests do not establish mobile layout or full authenticated interview
behavior. Native-app inventory also reported a locked Mac, but no claim is made
that this caused the browser URL rejection.

Completed SignWell PDFs have **not** been obtained or visually reviewed for this
new form. No customer message, signing request, signature, payment, production
database migration, or deployment was made. Provider-completed QA and a permitted
release still remain; this is not a production-ready/completed roadmap item.

The existing daily report automation was read and remains ACTIVE at 08:00 with its
existing thread target. No duplicate automation was created.
