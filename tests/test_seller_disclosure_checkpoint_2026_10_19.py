from pathlib import Path
import re
import unittest

SQL = (Path(__file__).resolve().parents[1] / 'supabase' /
       'homeofferflow_seller_disclosure_checkpoint_2026_10_19.sql').read_text()


class DisclosureOperationalCheckpointTests(unittest.TestCase):
    def test_one_exact_optimistically_guarded_existing_row(self):
        self.assertEqual(SQL.lower().count('update public.'), 1)
        for guard in ("id = '56d51351-422f-4d27-88f7-54cd8ba3734c'",
                      "slug = 'seller-workflow'", "status = 'in_progress'",
                      "qa_status = 'partial'", 'and current_release =',
                      'md5(coalesce(metadata', 'md5(coalesce(known_issues',
                      'md5(coalesce(next_action', 'matched <> 1', 'raise exception',
                      "statement_timeout = '5s'"):
            self.assertIn(guard, SQL)

    def test_preserves_release_history_and_does_not_claim_completed_qa(self):
        assignments = SQL.split('  set ', 1)[1].split('  where ', 1)[0]
        self.assertEqual(re.findall(r'^\s*(\w+)\s*=', assignments, re.MULTILINE),
                         ['known_issues', 'next_action', 'metadata', 'updated_at'])
        for fact in ("coalesce(metadata, '{}'::jsonb) || jsonb_build_object",
                     "'candidate_deployed', false", "'qa_a_status', 'completed_verified'",
                     "'qa_b_status', 'owner_reports_complete_provider_proof_pending'",
                     "'completed_provider_review', 'not_verified'",
                     "'purchase_combined_packet', 'not_implemented'",
                     'source-owner authorization is not a blocker',
                     'packet-specific test consent is already authorized'):
            self.assertIn(fact, SQL)
