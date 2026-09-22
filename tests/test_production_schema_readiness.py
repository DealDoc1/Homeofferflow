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
