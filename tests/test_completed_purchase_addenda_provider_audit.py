from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.qa.audit_completed_purchase_addenda import (
    current_fields, component_marks, COMPONENT_PAGES, SOURCE_PINS,
    COMPLETED_SHA256, BACKGROUNDS, WATERMARKS, MARK_KEYS)
from scripts.qa.audit_txr1506_completed import match_marks

ROOT = Path(__file__).resolve().parents[1]
OBSERVED = json.loads((ROOT / 'tests/fixtures/completed_purchase_addenda_ordinary_geometry.json').read_text())


class CompletedPurchaseAddendaAuditTests(unittest.TestCase):
    def test_three_current_maps_match_twelve_independently_measured_signatures(self):
        for form, case in OBSERVED['components'].items():
            with self.subTest(form=form):
                self.assertEqual(len(match_marks(current_fields(form), case['marks'])), 4)
                self.assertEqual({f['recipient_id'] for f in current_fields(form)}, {'1','2','3','4'})
                self.assertTrue(all(f['type']=='signature' and f['required'] for f in current_fields(form)))
                self.assertEqual(case['composite_page'], COMPONENT_PAGES[form])
                self.assertEqual(case['source_sha256'], SOURCE_PINS[form])
        self.assertEqual(OBSERVED['completed_sha256'], COMPLETED_SHA256)
        self.assertFalse(OBSERVED['all_form_cases_passed'])
        self.assertFalse(OBSERVED['combined_packet_assembly_verified'])

    def test_shifted_or_clipped_fields_cannot_reuse_completed_evidence(self):
        for form, case in OBSERVED['components'].items():
            for key in ('x','y','height','width'):
                fields = deepcopy(current_fields(form))
                fields[0][key] = 1
                with self.subTest(form=form,key=key), self.assertRaises(ValueError):
                    match_marks(fields, case['marks'])

    def test_missing_duplicate_or_wrong_page_marks_reject(self):
        for form, case in OBSERVED['components'].items():
            marks = case['marks']
            for bad in (marks[:-1], marks+[marks[0]], marks[:-1]+[marks[0]],
                        [{**m,'page':2} for m in marks]):
                with self.subTest(form=form), self.assertRaises(ValueError):
                    match_marks(current_fields(form), bad)

    def test_only_exact_backgrounds_are_excluded(self):
        for form, case in OBSERVED['components'].items():
            backgrounds = [dict(zip(MARK_KEYS, box)) for box in BACKGROUNDS[form]+WATERMARKS]
            images = backgrounds + deepcopy(case['marks'])
            self.assertEqual(component_marks(form, images), case['marks'])
            images.append({'x0':10,'top':600,'width':200,'height':35})
            with self.assertRaises(ValueError):
                match_marks(current_fields(form), component_marks(form, images))
            with self.assertRaises(ValueError):
                component_marks(form, backgrounds[1:]+case['marks'])
            with self.assertRaises(ValueError):
                component_marks(form, backgrounds+[backgrounds[0]]+case['marks'])

    def test_operational_case_update_is_atomic_scoped_and_keeps_qa_partial(self):
        sql = (ROOT / 'supabase/homeofferflow_ordinary_addenda_provider_qa_2026_10_14.sql').read_text()
        assignments = sql.split('set known_issues',1)[1].split('from reviewed',1)[0]
        self.assertNotRegex(assignments, r'\b(?:status|qa_status|current_release|completed_at)\s*=')
        for identity in ('78a39a5a-83e0-436a-a00a-ea2d127a068c',
                         'cf8cb9d9-7f25-4e2c-bff4-1082711d7c13',
                         '0d1ffe90-afc6-48ee-9be3-a0d5935f1729'):
            self.assertIn(identity, sql)
        for guard in ("item.id = reviewed.id", "item.slug = reviewed.slug",
                      "item.status = 'in_progress'", "item.qa_status = 'partial'",
                      'if touched <> 3 then', "'all_form_cases_passed', false",
                      "'combined_packet_assembly_verified', false"):
            self.assertIn(guard, sql)
        self.assertIn(COMPLETED_SHA256, sql)
        for source_pin in SOURCE_PINS.values():
            self.assertIn(source_pin, sql)


if __name__ == '__main__':
    unittest.main()
