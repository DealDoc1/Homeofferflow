# Customer interview release — September 10, 2026

## Deploy result

- Canonical URL: https://www.homeofferflow.com/
- Deployment: https://homeofferflow-grukuxrs3-dealdoc1s-projects.vercel.app
- Target: production
- Status: Ready
- Commit: `923ea7134848279c94bac9d6a3039b7e743acdb4`
- Framework: existing static HTML/JavaScript frontend and Python/JavaScript APIs
- PR: https://github.com/DealDoc1/Homeofferflow/pull/1194
- Release workflow: https://github.com/DealDoc1/Homeofferflow/actions/runs/34508274061
- GitHub build step: 7 seconds; Vercel CLI reported 5 seconds for the build itself
- Prebuilt upload: 29 seconds
- Ready confirmed: September 10, 2026, 17:28:37 UTC

The user explicitly authorized the public UI fixes, tests and sanitized release
notes and the production deployment. The former publication hold is resolved.
One intentional production deployment was made; no preview was created.
Automatic Vercel Git deployments remain disabled. The build ran on GitHub;
Vercel received the prebuilt artifact. This does not make ordinary runtime or
observability usage free. The existing usage page displayed $1.31 in on-demand
charges before release, with a warning that usage can be up to one hour old.

## What changed

- Account restoration no longer replaces the selected customer interview.
  Saved agent/investor defaults apply only to the matching interview.
- Agent questions retain keyboard focus, restore the original transaction
  choice when closed, and scroll focused mobile controls into view.
- Repeated purchase-addendum instructions were removed without removing any
  choices or their relevant guidance.
- The future mobile-app brief preserves independent-agent access to released
  shared forms. The installable web-app shell advanced to v67.

No form sources, signing coordinates, recipients, database schema, account
permissions, subscription entitlements, prices or Google Maps autocomplete
were changed. No signing packets, emails or purchases were submitted for this
release check.

## Verified

- All 1,630 local tests passed in 8.465 seconds.
- PR CI passed, including the existing approved packet-rendering check.
- The exact production workflow passed all 1,630 tests in 13.069 seconds and
  passed release preflight with no packet/form source or mapping changes.
- All 43 inline scripts parse; patch whitespace is clean.
- Canonical site, PWA shell, API health, supported packet runtime and public
  legal-page checks all passed in the release workflow.
- The canonical index and service worker exactly match the tested files:
  - index SHA-256: `f2291ffae3e11acc2ad73d493517fbbb7674dd185b40f6b86594f7f69717b43b`
  - worker SHA-256: `6eaf5deb82186777df7fe4ab3e6375370fc681f770b063054810710b4d8ac1de`
- In the canonical browser after release, the selected Homebuyer interview
  showed Step 1 of 10 while the account control showed Agent Account. A later
  DOM check still showed Step 1 of 10 after account restoration. The consent
  checkbox was not accepted and the interview was not submitted.
- A bounded error/warning log scan for this exact deployment, starting at
  17:28:00 UTC with a 50-entry limit, returned no matching entries. This is a
  point-in-time result, not a claim that every customer transaction is error-free.

## Remaining verification

The live browser connection stalled after the homebuyer check while returning
to the homepage. The documented tab-recovery and close attempts also failed.
The final live four-path/nested-question keyboard and mobile recheck was not
completed. No application error was established from this tool failure.

The prior local browser evidence still covers all four agent questions, five
nested paths, direct Escape, focus wrapping, visible mobile focus and no
horizontal overflow at 375 by 667 pixels. See
`agent-interview-navigation-2026-09-10.md`. Local UI coverage is not relabeled as
production end-to-end or completed-signature QA.

Next verification: reuse a functioning in-app browser session to recheck those
already-deployed questions. Do not create another deployment just for this QA.
Log-drain configuration was not audited in this release.

## Non-blocking maintenance follow-up

GitHub reported that `astral-sh/setup-uv@v6` targets deprecated Node.js 20 and is
being run on Node.js 24. The release succeeded. Review the action's supported
current version in a future locally tested maintenance batch; no additional
deployment was created for that warning.
