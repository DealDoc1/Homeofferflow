from pathlib import Path
import re
import unittest

SQL = (Path(__file__).resolve().parents[1] / 'supabase' /
       'homeofferflow_seller_disclosure_checkpoint_2026_10_16.sql').read_text()


class SellerDisclosureCheckpointTrackerTests(unittest.TestCase):
    def test_only_exact_existing_partial_record_can_be_changed(self):
        self.assertEqual(SQL.lower().count('update public.'), 1)
        for guard in ("id = '56d51351-422f-4d27-88f7-54cd8ba3734c'",
                      "slug = 'seller-workflow'", "status = 'in_progress'",
                      "qa_status = 'partial'", 'matched <> 1', 'raise exception',
                      'md5(coalesce(metadata', 'md5(coalesce(known_issues',
                      'md5(coalesce(next_action', 'and current_release ='):
            self.assertIn(guard, SQL)
        self.assertIn("statement_timeout = '5s'", SQL)

    def test_checkpoint_preserves_partial_release_and_historical_metadata(self):
        assignment = SQL.split('  set ', 1)[1].split('  where ', 1)[0]
        self.assertEqual(re.findall(r'^\s*(\w+)\s*=', assignment, re.MULTILINE),
                         ['known_issues', 'next_action', 'metadata', 'updated_at'])
        for fact in ("coalesce(metadata, '{}'::jsonb) || jsonb_build_object",
                     "'candidate_deployed', false", "'explanation_implementation', 'locally_tested'",
                     "'completed_provider_review', 'not_verified'",
                     "'integrated_authenticated_signing', 'not_verified'",
                     'do not recreate or resend', 'No brokerage-seat, source-owner or per-agent approval'):
            self.assertIn(fact, SQL)
