"""Offline QA preparation, with optional actual-source integration coverage."""
from hashlib import sha256
from pathlib import Path
import os
import tempfile
import unittest

from scripts.qa.prepare_buyer_representation_package import (
    CASES, build_case, case_data, field_guide, load_sources, run,
)


class BuyerPackageQATests(unittest.TestCase):
    def test_fixed_cases_have_explicit_signers_and_no_delivery_addresses(self):
        for case in CASES:
            agreement, notice, recipients = case_data(case)
            self.assertEqual(agreement['client_names'], notice['client_names'])
            self.assertTrue(notice['_for_signing'])
            self.assertEqual(len(recipients), len(agreement['client_names']) + 1)
            self.assertNotIn('@', repr((agreement, notice, recipients)))
        self.assertEqual(case_data('broker')[2], ['1', 'broker'])
        with self.assertRaises(ValueError):
            case_data('customer')

    def test_source_mismatch_and_missing_iabs_pin_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'TXR1507.pdf').write_bytes(b'wrong')
            with self.assertRaisesRegex(ValueError, 'IABS SHA'):
                load_sources(path, '')
            with self.assertRaisesRegex(ValueError, 'TXR1507 source hash'):
                load_sources(path, 'a' * 64)

    def test_repository_output_refused_before_reading_sources(self):
        root = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(ValueError, 'outside a Git'):
            run(Path('/nonexistent'), root / 'tmp/qa', 'a' * 64)

    @unittest.skipUnless(os.environ.get('HOF_BUYER_QA_SOURCE_DIR'), 'Private sources not supplied')
    def test_actual_sources_all_branches_preserve_page_offsets_and_iabs(self):
        directory = Path(os.environ['HOF_BUYER_QA_SOURCE_DIR'])
        pin = os.environ['HOF_BUYER_QA_IABS_SHA256']
        sources = load_sources(directory, pin)
        for case in CASES:
            with self.subTest(case=case):
                package = build_case(sources, case)
                self.assertTrue(field_guide(package).startswith(b'%PDF'))
                manifest = package.manifest
                self.assertEqual(manifest['included_codes'], ['TXR-1506', 'IABS'])
                self.assertEqual(manifest['related_start_page'], manifest['primary_pages'] + 1)
                self.assertEqual(manifest['iabs_start_page'], manifest['related_end_page'] + 1)
                fields = package.fields[0]
                self.assertTrue(all(f['page'] < manifest['iabs_start_page'] for f in fields))
                self.assertEqual(len({f['api_id'] for f in fields}), len(fields))
                self.assertEqual({f['recipient_id'] for f in fields}, set(case_data(case)[2]))
                notice = [f for f in fields if f['api_id'].startswith('txr1506_')]
                self.assertTrue(notice)
                self.assertTrue(all(manifest['related_start_page'] <= f['page'] <=
                                    manifest['related_end_page'] for f in notice))
                if case == 'long-unicode':
                    self.assertGreater(manifest['primary_pages'], 2)
                    self.assertGreater(manifest['related_end_page'] - manifest['related_start_page'] + 1, 6)
                else:
                    self.assertEqual(manifest['page_count'], 9)
        self.assertEqual(sha256(sources['IABS']).hexdigest(), pin)


if __name__ == '__main__':
    unittest.main()
