# Agent tenant-representation entry copy alignment

Date: 2026-09-22

## Change

- Updated the public agent transaction card and FAQ to state that tenant representation proceeds directly to the representation agreement that fits the tenant.
- Kept the visible FAQ and FAQ structured data aligned.
- Removed the inaccurate promise of a separate customer-showing-form choice from this entry path.

## Verification

- `git diff --check`
- 159 focused agent-landing, listing-workspace, public-discovery, and technical-SEO tests passed.
- The existing direct tenant-representation route remains unchanged; this release aligns public copy with the tested product behavior.

## Deployment handling

This is a low-risk copy correction intended for the next bundled production release rather than a standalone Vercel deployment.
