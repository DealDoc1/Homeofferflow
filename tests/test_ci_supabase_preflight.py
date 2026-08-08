import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CiSupabasePreflightTests(unittest.TestCase):
    def test_main_test_workflow_runs_supabase_branch_preflight(self):
        workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        self.assertIn("- name: Run Supabase branch preflight", workflow)
        self.assertIn("python scripts/preflight_supabase_branch.py", workflow)


if __name__ == "__main__":
    unittest.main()
