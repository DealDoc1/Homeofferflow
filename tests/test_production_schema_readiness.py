import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_production_schema_readiness.py"
MIGRATION = (
    ROOT
    / "supabase/migrations/20260921203652_homeofferflow_release_schema_readiness.sql"
).read_text(encoding="utf-8")
FIX_MIGRATION = (
    ROOT
    / "supabase/migrations/20260922053000_fix_release_schema_readiness_coalesce.sql"
).read_text(encoding="utf-8")
SPEC = importlib.util.spec_from_file_location("check_production_schema_readiness", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProductionSchemaReadinessTests(unittest.TestCase):
    def test_readiness_probes_new_public_profile_columns_without_reading_rows(self):
        import json
        from contextlib import contextmanager
        requests = []
        @contextmanager
        def open_fixture(request, timeout):
            requests.append(request)
            body = {"contract": MODULE.EXPECTED_CONTRACT, "ready": True, "missing": []} if len(requests) == 1 else []
            if request.full_url.endswith('/rpc/hof_purchase_disclosure_schema_readiness'):
                body = {'contract':'homeofferflow-purchase-disclosure-v1','ready':True,'missing':[]}
            if request.full_url.endswith('/rpc/hof_lease_listing_schema_readiness'):
                body = {'contract':MODULE.LEASE_CONTRACT,'ready':True,'missing':[]}
            if request.full_url.endswith('/rpc/hof_rental_source_schema_readiness'):
                body = {'contract':'homeofferflow-rental-source-schema-v1','ready':True,'missing':[]}
            yield io.StringIO(json.dumps(body))
        with patch.object(MODULE, 'urlopen', side_effect=open_fixture):
            result = MODULE.fetch_readiness('https://fixture.supabase.co', 'sb_secret_fixture')
        self.assertTrue(result['ready'])
        self.assertEqual(len(requests), 8)
        self.assertTrue(requests[0].full_url.endswith('/rpc/hof_listing_package_schema_readiness'))
        self.assertEqual(requests[1].method, 'GET')
        self.assertIn('onboarding_public_contact_phone', requests[1].full_url)
        self.assertIn('onboarding_public_headshot_url', requests[1].full_url)
        self.assertTrue(requests[1].full_url.endswith('&limit=0'))
        self.assertNotIn('contact_email', requests[1].full_url)
        self.assertIn('signature_packet_id', requests[2].full_url)
        self.assertTrue(requests[2].full_url.endswith('&limit=0'))
        self.assertIn('questionnaire_enabled,review_content_revision,review_render_revision', requests[3].full_url)
        self.assertTrue(requests[3].full_url.endswith('&limit=0'))
        self.assertNotIn('seller_email', requests[3].full_url)
        self.assertNotIn('seller_email', requests[2].full_url)
        self.assertTrue(requests[4].full_url.endswith('/rpc/hof_purchase_disclosure_schema_readiness'))
        self.assertIn('select=signature_offer_id&limit=0', requests[5].full_url)
        self.assertTrue(requests[6].full_url.endswith('/rpc/hof_lease_listing_schema_readiness'))
        self.assertEqual(requests[6].method, 'POST')
        self.assertEqual(requests[6].data, b'{}')
        self.assertEqual(requests[6].get_header('Apikey'), 'sb_secret_fixture')
        self.assertIsNone(requests[6].get_header('Authorization'))
        self.assertTrue(requests[7].full_url.endswith('/rpc/hof_rental_source_schema_readiness'))

    def test_disabled_purchase_binding_guard_cannot_pass_release_readiness(self):
        import json
        from contextlib import contextmanager
        @contextmanager
        def open_fixture(request, timeout):
            body = []
            if request.full_url.endswith('/rpc/hof_listing_package_schema_readiness'):
                body = {'contract':MODULE.EXPECTED_CONTRACT,'ready':True,'missing':[]}
            if request.full_url.endswith('/rpc/hof_purchase_disclosure_schema_readiness'):
                body = {'contract':'homeofferflow-purchase-disclosure-v1','ready':False,'missing':['trigger:hof_purchase_disclosure_signature_guard']}
            if request.full_url.endswith('/rpc/hof_lease_listing_schema_readiness'):
                body = {'contract':MODULE.LEASE_CONTRACT,'ready':True,'missing':[]}
            if request.full_url.endswith('/rpc/hof_rental_source_schema_readiness'):
                body = {'contract':'homeofferflow-rental-source-schema-v1','ready':True,'missing':[]}
            yield io.StringIO(json.dumps(body))
        with patch.object(MODULE, 'urlopen', side_effect=open_fixture):
            result = MODULE.fetch_readiness('https://fixture.supabase.co', 'sb_secret_fixture')
        self.assertFalse(result['ready'])
        self.assertIn('trigger:hof_purchase_disclosure_signature_guard', result['missing'])

    def lease_fixture(self, result):
        import json
        from contextlib import contextmanager
        from urllib.error import HTTPError
        @contextmanager
        def open_fixture(request, timeout):
            body = []
            if request.full_url.endswith('/rpc/hof_listing_package_schema_readiness'):
                body = {'contract':MODULE.EXPECTED_CONTRACT,'ready':True,'missing':[]}
            elif request.full_url.endswith('/rpc/hof_purchase_disclosure_schema_readiness'):
                body = {'contract':'homeofferflow-purchase-disclosure-v1','ready':True,'missing':[]}
            elif request.full_url.endswith('/rpc/hof_rental_source_schema_readiness'):
                body = {'contract':'homeofferflow-rental-source-schema-v1','ready':True,'missing':[]}
            elif request.full_url.endswith('/rpc/hof_lease_listing_schema_readiness'):
                if isinstance(result, int):
                    raise HTTPError(request.full_url, result, 'fictional unavailable lease RPC', {}, None)
                body = result
            yield io.StringIO(json.dumps(body))
        return patch.object(MODULE, 'urlopen', side_effect=open_fixture)

    def test_lease_constraint_failure_or_inconsistent_ready_flag_cannot_pass(self):
        missing = ['form_code:hof_standalone_agreements.TXR-1102']
        for ready, failures in ((False, missing), (False, []), (True, missing)):
            with self.subTest(ready=ready, failures=failures), self.lease_fixture(
                    {'contract':MODULE.LEASE_CONTRACT,'ready':ready,'missing':failures}):
                result = MODULE.fetch_readiness('https://fixture.supabase.co', 'sb_secret_fixture')
                self.assertFalse(result['ready'])
                self.assertIn('lease-listing:not-ready', result['missing'])
                for failure in failures:
                    self.assertIn(failure, result['missing'])

    def test_missing_or_inaccessible_lease_rpc_cannot_be_silently_ignored(self):
        from urllib.error import HTTPError
        for status in (401, 403, 404, 503):
            with self.subTest(status=status), self.lease_fixture(status), self.assertRaises(HTTPError):
                MODULE.fetch_readiness('https://fixture.supabase.co', 'sb_secret_fixture')

    def test_malformed_or_wrong_lease_contract_never_claims_readiness(self):
        good = {'contract':MODULE.LEASE_CONTRACT,'ready':True,'missing':[]}
        for payload in (None, [], {}, {**good,'contract':'wrong'}, {**good,'ready':'true'},
                        {**good,'ready':1}, {**good,'missing':None}, {**good,'missing':'missing'},
                        {**good,'missing':[{'unsafe':'object'}]}):
            with self.subTest(payload=payload), self.lease_fixture(payload), self.assertRaises(ValueError):
                MODULE.fetch_readiness('https://fixture.supabase.co', 'sb_secret_fixture')

    def test_lease_wrapper_remains_separate_service_only_and_additive(self):
        sql = (ROOT/'supabase/migrations/20261020231654_add_txr1102_lease_listing_drafts.sql').read_text()
        self.assertIn(MODULE.LEASE_CONTRACT, sql)
        self.assertIn('baseline := public.hof_release_schema_readiness()', sql)
        self.assertNotIn('create or replace function public.hof_release_schema_readiness()', sql)
        self.assertIn('security invoker set search_path=pg_catalog', sql)
        self.assertIn('revoke all on function public.hof_lease_listing_schema_readiness() from public,anon,authenticated', sql)
        self.assertIn('grant execute on function public.hof_lease_listing_schema_readiness() to service_role', sql)
        self.assertIn('and c.contype=\'c\' and c.convalidated', sql)
    def test_rental_source_probe_requires_validated_complete_catalog(self):
        import json
        from contextlib import contextmanager
        for rental in ({'contract':'wrong','ready':True,'missing':[]},
                       {'contract':'homeofferflow-rental-source-schema-v1','ready':False,'missing':['source-code:TXR-2008']},
                       {'contract':'homeofferflow-rental-source-schema-v1','ready':True,'missing':['source-code:TXR-2015']}):
            @contextmanager
            def open_fixture(request, timeout):
                body = []
                if request.full_url.endswith('/rpc/hof_listing_package_schema_readiness'):
                    body = {'contract':MODULE.EXPECTED_CONTRACT,'ready':True,'missing':[]}
                elif request.full_url.endswith('/rpc/hof_purchase_disclosure_schema_readiness'):
                    body = {'contract':'homeofferflow-purchase-disclosure-v1','ready':True,'missing':[]}
                elif request.full_url.endswith('/rpc/hof_lease_listing_schema_readiness'):
                    body = {'contract':MODULE.LEASE_CONTRACT,'ready':True,'missing':[]}
                elif request.full_url.endswith('/rpc/hof_rental_source_schema_readiness'):
                    body = rental
                yield io.StringIO(json.dumps(body))
            with self.subTest(rental=rental), patch.object(MODULE,'urlopen',side_effect=open_fixture):
                if rental['contract']=='wrong':
                    with self.assertRaises(ValueError): MODULE.fetch_readiness('https://fixture.supabase.co','fixture')
                else:
                    result=MODULE.fetch_readiness('https://fixture.supabase.co','fixture')
                    self.assertFalse(result['ready'])
                    self.assertIn('rental-source:not-ready',result['missing'])

    def test_questionnaire_readiness_matches_only_the_released_schema(self):
        sql = (ROOT / 'supabase/migrations/20261018134817_seller_disclosure_questionnaire_access.sql').read_text()
        self.assertIn('homeofferflow-release-schema-v2', sql)
        self.assertIn('hof_save_seller_questionnaire', sql)
        self.assertNotIn("'TXR-1101'", sql)
        self.assertNotIn('drop index', sql.lower())
        self.assertIn('create unique index hof_seller_questionnaire_active_idx', sql)
        self.assertIn('create function public.hof_seller_disclosure_schema_readiness()', sql)
        self.assertIn('baseline := public.hof_release_schema_readiness()', sql)
        self.assertNotIn('create or replace function public.hof_release_schema_readiness()', sql)

    def test_listing_readiness_extends_but_does_not_replace_applied_contracts(self):
        listing=(ROOT/'supabase/migrations/20261017131634_add_txr1101_listing_drafts.sql').read_text()
        binding=(ROOT/'supabase/migrations/20261019000034_bind_disclosure_to_listing_signature.sql').read_text()
        self.assertEqual(MODULE.EXPECTED_CONTRACT,'homeofferflow-release-schema-v3')
        self.assertIn(MODULE.EXPECTED_CONTRACT,binding)
        self.assertIn('baseline := public.hof_seller_disclosure_schema_readiness()',binding)
        self.assertIn("'TXR-1101'",listing)
        self.assertIn('signature_packet_id',binding)
        self.assertNotIn('create or replace function public.hof_release_schema_readiness()',listing+binding)

    def test_missing_public_profile_columns_cannot_be_silently_ignored(self):
        import json
        from contextlib import contextmanager
        from urllib.error import HTTPError
        calls = []
        @contextmanager
        def open_fixture(request, timeout):
            calls.append(request.full_url)
            if len(calls) == 1:
                yield io.StringIO(json.dumps({'contract':MODULE.EXPECTED_CONTRACT, 'ready':True, 'missing':[]}))
            else:
                raise HTTPError(request.full_url, 400, 'missing columns', {}, None)
        with patch.object(MODULE, 'urlopen', side_effect=open_fixture):
            with self.assertRaises(HTTPError): MODULE.fetch_readiness('https://fixture.supabase.co', 'fixture')
        self.assertEqual(len(calls), 2)
        self.assertIn('onboarding_public_contact_phone', calls[1])

    def test_workflow_secret_overrides_masked_pulled_legacy_value(self):
        values = {"SUPABASE_SERVICE_ROLE_KEY": "[SENSITIVE]"}

        with patch.dict(
            MODULE.os.environ,
            {"SUPABASE_SECRET_KEY": "sb_secret_workflow"},
            clear=True,
        ):
            selected = MODULE.first_value(MODULE.SERVICE_KEY_KEYS, values)

        self.assertEqual(selected, "sb_secret_workflow")

    def test_modern_secret_key_is_not_sent_as_a_bearer_token(self):
        headers = MODULE.request_headers("sb_secret_fixture")

        self.assertEqual(headers["apikey"], "sb_secret_fixture")
        self.assertNotIn("Authorization", headers)

    def test_legacy_service_role_key_remains_a_bearer_token(self):
        headers = MODULE.request_headers("legacy-service-role-jwt")

        self.assertEqual(headers["apikey"], "legacy-service-role-jwt")
        self.assertEqual(
            headers["Authorization"], "Bearer legacy-service-role-jwt"
        )

    def test_migration_checks_every_release_dependency_and_is_service_only(self):
        for expected in (
            "hof_agent_profile_aliases",
            "hof_email_deliveries",
            "hof_packet_generations",
            "hof_checkout_payloads",
            "hof_usage_events",
            "generation_key",
            "hof_claim_packet_generation",
            "hof_complete_packet_generation",
            "hof_release_unrendered_packet",
            "hof_packet_usage_summary",
            "hof_preserve_email_delivery",
            "hof_protect_offer_packet_autosave",
            "hof_preserve_checkout_payload",
        ):
            self.assertIn(expected, MIGRATION)
        self.assertIn("security invoker", MIGRATION.lower())
        self.assertIn("set search_path = ''", MIGRATION.lower())
        self.assertIn(
            "revoke all on function public.hof_release_schema_readiness() from public, anon, authenticated",
            MIGRATION.lower(),
        )
        self.assertIn(
            "grant execute on function public.hof_release_schema_readiness() to service_role",
            MIGRATION.lower(),
        )

    def test_readiness_uses_sql_coalesce_without_schema_qualification(self):
        expected = "coalesce(pg_catalog.array_length(missing, 1), 0) = 0"
        self.assertIn(expected, MIGRATION.lower())
        self.assertIn(expected, FIX_MIGRATION.lower())
        self.assertNotIn("pg_catalog.coalesce", MIGRATION.lower())
        self.assertNotIn("pg_catalog.coalesce", FIX_MIGRATION.lower())

    def test_success_uses_pulled_vercel_environment_without_printing_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            env_file = Path(temp) / ".env.production.local"
            env_file.write_text(
                'SUPABASE_URL="https://project.supabase.co"\n'
                'SUPABASE_SERVICE_ROLE_KEY="super-secret"\n',
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch.dict(MODULE.os.environ, {}, clear=True), patch.object(
                MODULE,
                "fetch_readiness",
                return_value={
                    "contract": MODULE.EXPECTED_CONTRACT,
                    "ready": True,
                    "missing": [],
                },
            ) as fetch, redirect_stdout(output):
                self.assertEqual(MODULE.main(["--env-file", str(env_file)]), 0)
        fetch.assert_called_once_with("https://project.supabase.co", "super-secret")
        self.assertNotIn("super-secret", output.getvalue())

    def test_missing_schema_capability_fails_closed(self):
        error = io.StringIO()
        with patch.dict(
            MODULE.os.environ,
            {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "secret",
            },
            clear=True,
        ), patch.object(
            MODULE,
            "fetch_readiness",
            return_value={
                "contract": MODULE.EXPECTED_CONTRACT,
                "ready": False,
                "missing": ["table:hof_agent_profile_aliases"],
            },
        ), redirect_stderr(error):
            self.assertEqual(MODULE.main([]), 1)
        self.assertIn("table:hof_agent_profile_aliases", error.getvalue())
        self.assertNotIn("secret", error.getvalue())

    def test_missing_credentials_fails_closed_without_network(self):
        error = io.StringIO()
        with patch.dict(MODULE.os.environ, {}, clear=True), patch.object(
            MODULE, "fetch_readiness"
        ) as fetch, redirect_stderr(error):
            self.assertEqual(MODULE.main([]), 2)
        fetch.assert_not_called()
        self.assertIn("credential is unavailable", error.getvalue())


if __name__ == "__main__":
    unittest.main()
