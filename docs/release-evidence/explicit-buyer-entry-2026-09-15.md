# Explicit buyer entry is respected for signed-in agents

## Confirmed issue

The public homepage deliberately routes a signed-in agent or broker to the
agent workspace when the Homebuyer pill is only the default. However, the
direct buyer link, installed-app Buyer Offer shortcut, shared-context buyer
action, and buyer campaign initialization did not mark their explicit audience
choice. Those buyer actions could therefore send an agent back to `/agents`.
The first three also called the transaction-changing audience selector before
the route decision, modifying and scheduling a save of the previous offer.

## Local implementation

- Explicit buyer links (`?buyer=1`, including the organic buyer guide), Buyer
  Offer app shortcuts, and shared-context buyer actions mark the intentional
  audience choice and use presentation-only selection before the handoff.
- Recognized campaign audiences mark the same intent. Unrecognized campaign
  values and ordinary homepage visits do not bypass the agent-aware default.
- The existing fresh-buyer start remains responsible for the deliberate new
  offer reset. No default pricing, packet content, signer fields, identity,
  account authority, or payment behavior changes.

## Verification

- Full local suite: **1,999 tests pass in 17.232 seconds**.
- Audience runtime harness: 106 passing cases, including 30 new cases. They
  exercise actual entry handlers and actual `beginOfferFrom` routing for
  signed-out visitors, agents, brokers, and investors. Destination new-offer
  creation is mocked to observe the handoff and any premature draft writes.
- Against commit `84a31a6d`, 24 cases reproduce incorrect explicit entry or
  pre-handoff mutation; 82 existing/positive-control cases pass.
- Six controls preserve the ordinary homepage's agent/broker redirect with no
  campaign or invalid campaign values. Explicit-link tests also verify route
  flag cleanup, correct attribution surface, no sign-in prompt, and one buyer
  start invocation rather than an agent-page navigation.
- All 45 executable inline scripts and the share-target asset parse.
  `git diff --check` passes.

This is local source-backed runtime verification, not browser visual QA,
authenticated production testing, or proof of a completed buyer transaction.

## Release/cost status

Local only; no push, Vercel build, preview, production deployment, or new service.
Include in the next authorized cost-controlled release and daily report as
locally verified, not deployed.
