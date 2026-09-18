# Lean task handoff generator — September 18, 2026

## Outcome

HomeOfferFlow development tasks can now begin with a compact handoff generated
from the live Git checkout instead of replaying a long conversation. The
generator requires the five batch facts defined by the lean development
protocol and adds the current branch, commit, bounded working-tree status and
eight most recent commits.

## Context and privacy boundary

The output is deliberately small: at most 20 changed paths, eight commits, 240
characters per repository-status line and 500 characters per batch fact. It
reads Git metadata only. It does not inspect task history, browser state,
environment variables, credentials, file contents or customer records.

The tool performs no network request, deployment, database write or paid API
call. It prints to standard output so a new task can receive the handoff
without maintaining another stale generated status file in the repository.

## Verification

Three focused tests pass:

- the five required batch facts and live Git branch/status/commit are included;
- repository sections remain bounded and report omitted entries; and
- contract values collapse to one line, reject empty values and reject inputs
  longer than 500 characters.

The command was also run against the current HomeOfferFlow worktree and
produced the expected bounded handoff. This is a local development-process
improvement; it does not change the customer-facing production site.
