from copy import deepcopy
import json
from pathlib import Path
import unittest

from lib.txr_1506 import build_signwell_fields_txr1506
from scripts.qa.audit_txr1506_completed import match_marks, PROVIDER_SCALE

ROOT = Path(__file__).resolve().parents[1]
OBSERVED = json.loads((ROOT / 'tests/fixtures/txr1506_completed_ordinary_geometry.json').read_text())


class CompletedConsumerNoticeAuditTests(unittest.TestCase):
    def setUp(self):
        self.fields = build_signwell_fields_txr1506(
            {'signer_plan':'consumers_and_associate'},client_count=2,page_count=6)[0]

    def test_current_customer_map_matches_thirteen_independently_measured_marks(self):
        result = match_marks(self.fields, OBSERVED['marks'])
        self.assertEqual(len(result),13)
        self.assertEqual(sum(f['type']=='initials' for f in result),10)
        self.assertEqual(sum(f['type']=='signature' for f in result),3)
        self.assertEqual(PROVIDER_SCALE, OBSERVED['provider_scale'])
        self.assertEqual(OBSERVED['composite_pages'],list(range(23,29)))
        self.assertFalse(OBSERVED['visual_review']['all_form_cases_passed'])

    def test_shifted_or_clipped_current_map_cannot_reuse_old_provider_evidence(self):
        for key, value in [('y',986),('x',464),('width',10),('height',26)]:
            with self.subTest(key=key):
                fields=deepcopy(self.fields)
                fields[0][key]=value
                with self.assertRaises(ValueError):
                    match_marks(fields,OBSERVED['marks'])

    def test_missing_duplicate_or_wrong_page_marks_fail_closed(self):
        for marks in [OBSERVED['marks'][:-1],OBSERVED['marks']+[OBSERVED['marks'][0]],
                      OBSERVED['marks'][:-1]+[OBSERVED['marks'][0]],
                      [{**m,'page':2} if index==0 else m for index,m in enumerate(OBSERVED['marks'])]]:
            with self.subTest(marks=len(marks)),self.assertRaises(ValueError):
                match_marks(self.fields,marks)

    def test_live_case_record_is_scoped_and_keeps_the_form_matrix_partial(self):
        sql=(ROOT/'supabase/homeofferflow_txr1506_ordinary_provider_qa_2026_10_14.sql').read_text()
        assignments=sql.split('set ',1)[1].split('where id',1)[0]
        self.assertNotRegex(assignments,r'\b(?:status|qa_status|current_release|completed_at)\s*=')
        self.assertIn("where id = 'c136e9af-3340-403c-b178-c97fc4c74921'",sql)
        self.assertIn("and slug = 'txr-1506-general-information-notice'",sql)
        self.assertIn("and status = 'in_progress'",sql)
        self.assertIn("and qa_status = 'partial'",sql)
        self.assertIn("and metadata ->> 'revision' = '06-15-26'",sql)
        self.assertIn('"all_form_cases_passed":false',sql)
        self.assertIn(OBSERVED['completed_sha256'],sql)
        self.assertIn('instead of resending it',sql)


if __name__ == '__main__':
    unittest.main()
