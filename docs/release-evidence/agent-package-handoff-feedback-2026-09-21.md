# Agent package handoff feedback — 2026-09-21

## Outcome

The agent package interview now acknowledges a direct package choice immediately
in the existing transaction status area. It says that the selected workspace is
opening, confirms only after the destination is present, and points to the
existing retry action if the handoff times out.

This removes a period where the interview closed while account-backed content
loaded with no visible acknowledgement, which could make a successful click
feel broken and invite duplicate clicks.

## Scope and privacy

- No new modal, popup, page, field, provider, or database write was added.
- Nested document choices keep their existing in-panel opening feedback.
- Status text contains only the selected package label; no client, property,
  offer, or document value is recorded or displayed.
- Existing aggregate selected, started, timeout, and recovery telemetry remains
  unchanged so the post-release funnel can be compared consistently.

## Evidence basis

The production 30-day aggregate funnel showed package selections exceeding
verified workspace starts. No timeout events were present, so this change does
not claim that the workspace failed. It addresses the observable feedback gap
while preserving the distinction between selection and an actually opened
workspace.

## Verification

- Focused package interview, funnel, accessibility, and routing tests cover the
  immediate, success, failure, and retry messages.
- Runtime tests execute the shipped status and workspace-observation handlers,
  proving that success is not announced before the destination is present and
  that timeout feedback exposes the existing recovery action.
- A local browser smoke check confirmed the agent sign-in continuation renders
  cleanly with no browser console warnings or errors. The authenticated package
  handoff itself is verified by the runtime model rather than claimed as live QA.
- The complete local test suite is run before merge.
- Production verification remains part of the single coordinated post-reset
  release; no preview deployment is required for this change.
