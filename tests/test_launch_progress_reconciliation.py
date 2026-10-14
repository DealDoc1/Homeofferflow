from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / 'supabase/homeofferflow_launch_progress_reconciliation_2026_10_14.sql').read_text()


class LaunchProgressReconciliationTests(unittest.TestCase):
    def test_update_targets_only_the_two_inspected_ids_and_slugs(self):
        self.assertEqual(re.findall(r"'([0-9a-f-]{36})'::uuid", SQL), [
            '56d51351-422f-4d27-88f7-54cd8ba3734c',
            'e603b953-3b83-4041-a873-6a9415244cbe',
        ])
        self.assertIn('where item.id = evidence.id', SQL)
        self.assertIn('and item.slug = evidence.slug', SQL)
        self.assertIn('item.current_release in (evidence.previous_release, evidence.current_release)', SQL)

    def test_existing_partial_states_and_other_metadata_are_preserved(self):
        assignments = SQL.split('set ', 1)[1].split('from (values', 1)[0]
        self.assertNotRegex(assignments, r'\b(?:status|qa_status|environment|completed_at|is_locked)\s*=')
        self.assertIn("item.status = 'in_progress'", SQL)
        self.assertIn("item.qa_status = 'partial'", SQL)
        self.assertIn("coalesce(item.metadata, '{}'::jsonb) || evidence.snapshot", SQL)
        self.assertEqual(SQL.lower().count('update public.'), 1)
        self.assertNotRegex(SQL.lower(), r'\b(?:insert into|delete from|alter table|grant|revoke)\b')

    def test_evidence_does_not_infer_completed_signing_or_broker_admin_qa(self):
        self.assertIn('PR #1330 / 83241c3', SQL)
        self.assertIn('PR #1333 / 4fe45d0', SQL)
        self.assertIn('integrated completed-signature QA remains incomplete', SQL)
        self.assertIn('This session does not expose broker-admin controls', SQL)
        self.assertIn('unfinished implementation, not a brokerage-seat or per-agent approval requirement', SQL)
        self.assertIn('entire intended brokerage roster', SQL)
        self.assertIn('without owner review of its draft', SQL)


if __name__ == '__main__':
    unittest.main()
