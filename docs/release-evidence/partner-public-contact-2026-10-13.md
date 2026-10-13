# Opt-in partner profiles and direct calls

## Batch contract

- Outcome: directory and offer follow-up users can visit an approved partner website or call its explicitly public contact directly, without forwarding customer information. Company logos and short descriptions clarify service fit.
- Scope: existing central partner onboarding, public directory API, directory/offer-follow-up renderers, shared client contact helper, nullable approved-public fields, PWA shell and schema-readiness probe. No form source, contract wording, signer geometry, access role, subscription or partner-activation rule changes.
- Verified production baseline `49297cbf727df96160e36ec8450458bce60d5978`, READY `dpl_FadWqGGEoc7Thz5T1M8QYhxrpszJ`; GitHub main independently matches. One intentional spend-guarded prebuilt release, no routine previews. Standing owner implementation/release authority applies.

## Implementation and focused evidence

- Explicit optional public phone/name/description fields are distinct from private contact_phone, contact_email and internal application messages. Blank phone removes calling, and older cached setup submissions preserve previously approved public fields. Partner entering the public number is explicitly told that it appears as a call button.
- Server validates and normalizes US/international numbers to E.164, rejects arbitrary URI, extension, newline and overlong input before saving or agreement dispatch. The directory joins only active platform-wide placements to their matching approved-public fields, strips the lead identifier and allowlists the response. Internal contacts/messages are never fallback data.
- Shared lightweight client helper validates website/telephone schemes, rejects credentials/attribute injection, preserves custom website labels except misleading Call/Text/SMS labels, and uses existing aggregate-only tracking markers for both actions. No customer/offer payload is forwarded. Invalid or missing public number means no call button.
- Both directory and offer-follow-up show approved logo/description and separate website/call actions. Non-regulated free-beta profiles say Beta partner rather than implying paid sponsorship tier. Existing neutral categories and placement ordering are unchanged.
- 90 focused Python checks passed, including actual JavaScript runtime checks, onboarding, directory privacy, readiness and PWA. Additional actual-source offer-follow-up renderer cases cover logo/description escaping, beta wording, both destinations and no private-contact fallback.
- Full frozen runtime candidate: 2,576 local tests in 86.115 seconds, OK (one environment-dependent skip). Expected negative fixtures print fail-closed messages; no real send/payment or signing test is run. Whitespace passes.

## Browser and data evidence

- Local real directory and API served with synthetic placement data only. API executes the actual public-directory function against an explicit local HTTP-client fixture; telemetry POSTs terminate locally. Not a production activation, real call or completed lead referral.
- Desktop and 390x844 layouts visually reviewed. Logo, service market, concise description, Beta partner and separate Visit website/Call Tedd Hansen are visible. Phone view page width equals viewport width (390), no horizontal overflow. DOM confirms `https://www.constructionwithintegrity.com/` and `tel:+19728376378`. No action link clicked. Screenshots `/private/tmp/hof-partner-public-desktop.png` and `/private/tmp/hof-partner-public-mobile.png`.
- Official CLI created `20261013201734_partner_public_profile.sql`; authenticated migration applied successfully. Independent schema read confirms three nullable text fields, bounded name/description and E.164 constraint. Existing RLS is still enabled, with unchanged server-only lead policy and no new grants/security-definer function.
- Security advisors returned no notice for the touched partner-leads table. Broader existing INFO server-only/no-policy and WARN authenticated GraphQL-schema-discovery notices were not modified as part of this feature. Reference: https://supabase.com/docs/guides/database/database-linter?lint=0027_pg_graphql_authenticated_table_exposed.
- Owner-supplied Tedd Hansen public name, +19728376378 and exact 525-character description saved only to existing beta application `b7b2ede6-bca8-400f-86d7-6ec80a5a2575`. Independent readback confirms beta/payment not_started/onboarding in_progress/agreement not_started/zero active placements. No charge, invitation, automatic billing conversion, false signed status or publication.
- Schema-readiness now probes the three columns with limit=0 before deployment, without reading application rows. No secret is copied onto this workstation or printed. Existing protected release credentials remain inside the CI connection.

## Release boundary

- Independent exact-head CI, canonical deployed asset/API/page verification and bounded error sample remain to be recorded after completion. The shared capability will be deployed, but Integrity First itself must not be described as publicly live from this synthetic preview or saved setup.
- Separate corrected TXR-1508 QA remains at final electronic-disclosure acceptance. No duplicate test, signature acceptance or customer-map promotion occurs here.
