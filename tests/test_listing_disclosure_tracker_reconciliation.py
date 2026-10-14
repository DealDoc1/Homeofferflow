from pathlib import Path
import re
import unittest


SQL = (Path(__file__).resolve().parents[1] / 'supabase' / 'homeofferflow_listing_disclosure_handoff_tracker.sql').read_text()


class ListingDisclosureTrackerReconciliationTests(unittest.TestCase):
    def test_update_targets_only_the_existing_seller_workflow(self):
        update = SQL[SQL.index('update public.hof_roadmap_items'):SQL.index('commit;')]
        self.assertIn("where id = '56d51351-422f-4d27-88f7-54cd8ba3734c'", update)
        self.assertIn("and slug = 'seller-workflow'", update)
        for field in ['status', 'environment', 'qa_status', 'metadata']:
            self.assertIsNone(re.search(r'\b' + field + r'\s*=', update))

    def test_tracker_distinguishes_deployed_handoff_from_unfinished_form_and_signing_work(self):
        self.assertIn('PR #1330 / 83241c3', SQL)
        self.assertIn('integrated completed-signature QA matrix remains incomplete', SQL)
        self.assertIn('agreement workflows are not yet implemented', SQL)
        self.assertIn('not a brokerage-seat or per-agent approval requirement', SQL)
        self.assertNotIn('remain source-gated', SQL)


if __name__ == '__main__':
    unittest.main()
