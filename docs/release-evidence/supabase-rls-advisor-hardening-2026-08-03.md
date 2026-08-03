# Supabase RLS advisor hardening — 2026-08-03

## Scope

Behavior-preserving hardening for row-level-security policies that the live
Supabase performance advisor reported as re-evaluating `auth.uid()` for every
row.

## Change

The SQL record in
`supabase/homeofferflow_rls_initplan_hardening.sql` replaces raw
`auth.uid()` calls in the affected ownership policies with
`(select auth.uid())`, preserving the same ownership predicates while allowing
Postgres to evaluate the auth identity once per statement.

## Live verification

- Applied to project `acqylchftrjjoablvqyq` on 2026-08-03.
- Supabase performance advisor after the change: 48 informational notices,
  zero warnings, and no remaining `auth_rls_initplan` notices.
- Repository test suite: 374 tests passed.
- No Vercel runtime deployment was triggered because this was a database
  policy optimization and its SQL record; the live database change was
  verified directly.

## Remaining advisor notices

The remaining notices are informational (legacy tables without policies,
unindexed foreign keys, unused indexes, and GraphQL exposure notices). They
are intentionally not bulk-changed in this pass because doing so could alter
existing API or dashboard behavior. Each requires a table-specific access
review before removal or revocation.
