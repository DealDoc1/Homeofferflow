import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "preflight_supabase_branch", ROOT / "scripts" / "preflight_supabase_branch.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SupabaseBranchPreflightTests(unittest.TestCase):
    def test_current_repository_has_a_complete_ordered_migration_chain(self):
        report = MODULE.inspect_repository(ROOT)
        self.assertTrue(report["ok"])
        self.assertGreaterEqual(report["migrationCount"], 62)

    def test_complete_ordered_chain_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            supabase = root / "supabase"
            migrations = supabase / "migrations"
            migrations.mkdir(parents=True)
            (supabase / "config.toml").write_text("project_id = \"test\"\n", encoding="utf-8")
            (migrations / "20260808000000_initial.sql").write_text("select 1;\n", encoding="utf-8")
            (migrations / "20260808000001_followup.sql").write_text("select 2;\n", encoding="utf-8")

            report = MODULE.inspect_repository(root)

        self.assertTrue(report["ok"])
        self.assertEqual(report["migrationCount"], 2)

    def test_invalid_and_duplicate_versions_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            migrations = root / "supabase" / "migrations"
            migrations.mkdir(parents=True)
            (root / "supabase" / "config.toml").write_text("", encoding="utf-8")
            (migrations / "20260808000000_first.sql").write_text("", encoding="utf-8")
            (migrations / "20260808000000_second.sql").write_text("", encoding="utf-8")
            (migrations / "not-a-migration.sql").write_text("", encoding="utf-8")

            report = MODULE.inspect_repository(root)

        self.assertFalse(report["ok"])
        self.assertIn("migration version prefixes must be unique", report["errors"])
        self.assertTrue(any("14-digit version prefix" in error for error in report["errors"]))
        self.assertTrue(any("migration file is empty" in error for error in report["errors"]))

    def test_missing_project_id_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            migrations = root / "supabase" / "migrations"
            migrations.mkdir(parents=True)
            (root / "supabase" / "config.toml").write_text("[api]\nenabled = true\n", encoding="utf-8")
            (migrations / "20260808000000_initial.sql").write_text("select 1;\n", encoding="utf-8")

            report = MODULE.inspect_repository(root)

        self.assertFalse(report["ok"])
        self.assertIn("supabase/config.toml must declare a non-empty project_id", report["errors"])


if __name__ == "__main__":
    unittest.main()
