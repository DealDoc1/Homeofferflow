"""Independent measurements from private TXR1501 06-15-26 page 6.

The source has one shared left execution rule, not a separate associate row.
No source PDF or signed artwork is stored in this test.
"""
from copy import deepcopy
import unittest
from lib.txr_1501 import build_signwell_fields_txr1501


def assert_source_bounds(test, fields):
    for field in fields:
        with test.subTest(field=field['api_id']):
            test.assertEqual(field['page'], 6)
            # Limits are source text/rule measurements, not widget positions.
            second = field['recipient_id'] == '2'
            client = field['recipient_id'] in ('1', '2')
            top = field['y'] * .75
            bottom = (field['y'] + field['height']) * .75
            left = field['x'] * .75
            right = (field['x'] + field['width']) * .75
            test.assertGreaterEqual(top, 495.88 if second else 423.38)
            test.assertLessEqual(bottom, 526.02996 if second else 443.22999)
            test.assertGreaterEqual(left, 324 if client else 36)
            test.assertLessEqual(right, 576.10 if client else 288.05)
            if field['type'] == 'date':
                # 49.21pt observed provider date plus margin, not proof of
                # this form's future completed-provider appearance.
                test.assertGreaterEqual(field['width'] * .75, 53)
                signature = next(f for f in fields if f['type']=='signature'
                                 and f['recipient_id']==field['recipient_id'])
                test.assertGreater(left, (signature['x']+signature['width'])*.75)


class Txr1501ExecutionBoundsTests(unittest.TestCase):
    def test_all_signer_variants_fit_measured_source_execution_regions(self):
        for role in ('broker', 'associate'):
            for count in (1, 2):
                with self.subTest(role=role, count=count):
                    fields=build_signwell_fields_txr1501(
                        {'signer_plan':'clients_and_'+role},client_count=count)[0]
                    self.assertEqual({f['recipient_id'] for f in fields},
                                     {'1',role} if count==1 else {'1','2',role})
                    assert_source_bounds(self,fields)

    def test_preceding_associate_row_and_date_width_fail_source_bounds(self):
        # Plain TestCase avoids subTest absorbing the expected assertion.
        check=unittest.TestCase()
        fields=build_signwell_fields_txr1501({'signer_plan':'clients_and_associate'},client_count=2)[0]
        for defect in ('old_row','old_date_width'):
            old=deepcopy(fields)
            for f in old:
                if defect=='old_row' and f['recipient_id']=='associate':
                    f['y'] += 111
                if defect=='old_date_width' and f['type']=='date':
                    f['width']=48
            with self.subTest(defect=defect), self.assertRaises(AssertionError):
                assert_source_bounds(check,old)


if __name__=='__main__':unittest.main()
