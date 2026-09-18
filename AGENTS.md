# HomeOfferFlow agent instructions

Before implementation, read `docs/LEAN_DEVELOPMENT_PROTOCOL.md` and follow it for the entire task.

- Use the current repository, roadmap, release evidence, and tests as the source of truth. Do not replay long chat history when the repository already answers the question.
- Keep each task to one bounded, coherent workstream. Finish and checkpoint that slice before expanding scope.
- Run focused tests while developing. Run the full suite once when the release candidate is ready, and again only if that candidate changes materially.
- For PDF changes, follow the PDF skill and visually inspect only the changed pages across the relevant ordinary, branch, single-signer, and long or Unicode cases.
- Report status precisely: implemented locally, tested, visually reviewed, deployed, and production-verified are different states.
- Keep automatic Git deployments disabled. Confirm current Vercel headroom before making one intentional prebuilt production deployment; do not create routine preview deployments.
- Coordinate code and database migrations as one release when they depend on each other.
- Preserve the simple TurboTax-style interview, Google address completion, concise industry-standard wording, simultaneous signer invitations, and agent form access without brokerage-seat or source-owner gates.
- Do not use real customer packets for routine QA. Only mutate live external systems when the current workstream requires it and the action is within the user's standing authorization.
- Leave every workstream as a coherent, locally committed, verified checkpoint with a compact handoff.
