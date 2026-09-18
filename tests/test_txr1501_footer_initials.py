"""Independent footer regions measured on TXR1501 06-15-26 pages 1-5."""
import unittest
from lib.txr_1501 import build_signwell_fields_txr1501


class Txr1501FooterInitialTests(unittest.TestCase):
    def test_all_pages_have_exactly_each_selected_signers_required_initials(self):
        for role in ('broker','associate'):
            for count in (1,2):
                fields=build_signwell_fields_txr1501({'signer_plan':'clients_and_'+role},client_count=count)[0]
                initials=[f for f in fields if f['type']=='initials']
                expected={'1',role} if count==1 else {'1','2',role}
                with self.subTest(role=role,count=count):
                    self.assertEqual(len(fields),14 if count==1 else 21)
                    self.assertEqual(len({f['api_id'] for f in fields}),len(fields))
                    self.assertEqual(len(initials),5*len(expected))
                    self.assertEqual({f['page'] for f in initials},set(range(1,6)))
                    for page in range(1,6):
                        page_fields=[f for f in initials if f['page']==page]
                        self.assertEqual({f['recipient_id'] for f in page_fields},expected)
                        self.assertTrue(all(f['required'] is True for f in page_fields))

    def test_full_rectangles_fit_every_source_blank_without_covering_adjacent_words(self):
        for role in ('broker','associate'):
            fields=build_signwell_fields_txr1501({'signer_plan':'clients_and_'+role},client_count=2)[0]
            for field in fields:
                if field['type']!='initials':continue
                # Small source shifts on pages 2-5 must not be rounded away.
                shift=0 if field['page']==1 else .347
                spans={role:(325.982,361.064),'1':(406.523+shift,441.605+shift),
                       '2':(446.555+shift,481.529+shift)}
                left,right=spans[field['recipient_id']]
                with self.subTest(role=role,field=field['api_id']):
                    self.assertGreaterEqual(field['x']*.75,left)
                    self.assertLessEqual((field['x']+field['width'])*.75,right)
                    self.assertGreaterEqual(field['y']*.75,730)
                    self.assertLessEqual((field['y']+field['height'])*.75,745.266)


if __name__=='__main__':unittest.main()
