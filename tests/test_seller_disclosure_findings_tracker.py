from pathlib import Path
import re
import unittest

SQL = (Path(__file__).resolve().parents[1] / "supabase" /
       "homeofferflow_seller_disclosure_findings_2026_10_15.sql").read_text()


class SellerDisclosureFindingsTrackerTests(unittest.TestCase):
    def test_update_targets_one_exact_unchanged_baseline(self):
        self.assertEqual(SQL.lower().count("update public."), 1)
        for guard in ("id = '56d51351-422f-4d27-88f7-54cd8ba3734c'",
                      "slug = 'seller-workflow'", "matched <> 1", "raise exception",
                      "md5(coalesce(metadata", "md5(coalesce(known_issues",
                      "md5(coalesce(next_action", "and current_release ="):
            self.assertIn(guard, SQL)
        self.assertIn("statement_timeout = '5s'", SQL)

    def test_only_factual_notes_and_additive_metadata_can_change(self):
        assignment = SQL.split("  set ", 1)[1].split("  where ", 1)[0]
        columns = re.findall(r"^\s*(\w+)\s*=", assignment, re.MULTILINE)
        self.assertEqual(columns, ["known_issues", "next_action", "metadata", "updated_at"])
        self.assertIn("coalesce(metadata, '{}'::jsonb) || jsonb_build_object", assignment)
        self.assertIn("'candidate_deployed', false", assignment)
        self.assertIn("'explanation_coverage_complete', false", assignment)
        self.assertIn("'completed_provider_review', 'pending'", assignment)
        self.assertIn("not only completed-signature QA", assignment)
