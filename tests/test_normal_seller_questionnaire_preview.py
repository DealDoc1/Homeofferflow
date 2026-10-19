from io import BytesIO
import os
from pathlib import Path
import unittest

from pypdf import PdfReader
from lib.seller_questionnaire import required_answers
from scripts.qa.seller_questionnaire_preview import render


class NormalSellerPreviewTests(unittest.TestCase):
    def answers(self, water=False):
        main, well = required_answers(water)
        return {'reviewContentRevision': '44444444-4444-4444-8444-444444444444',
                'responseData': {**dict.fromkeys(main, 'N'), 'seller_occupancy': 'Y',
                                 'working_smoke_detectors': 'Y', 'roof_type': 'Composition', 'roof_age': '8 years'},
                'waterRightsData': dict.fromkeys(well, 'N')}

    def test_incomplete_answers_are_rejected_before_any_source_or_network_use(self):
        data = self.answers(); del data['responseData']['defect_roof']
        with self.assertRaises(ValueError): render(data, b'not-a-source')

    def test_actual_normal_source_has_one_complete_disclosure_and_no_test_matrix(self):
        source = os.environ.get('HOF_DISCLOSURE_SOURCE')
        if not source: self.skipTest('Actual supplied disclosure source not selected')
        result = render(self.answers(), Path(source).read_bytes())
        pdf = PdfReader(BytesIO(result)); text = '\n'.join(p.extract_text() or '' for p in pdf.pages)
        self.assertEqual(len(pdf.pages), 4)
        for content in ('100 Example Lane, Frisco, TX', 'Composition', '8 years'):
            self.assertIn(content, text)
        for content in ('QA ONLY', 'QA Signer', 'Unknown. The Yes/No', 'Not Valid', 'Additional seller information'):
            self.assertNotIn(content, text)

    def test_optional_water_is_one_full_form_not_repeated_execution_pages(self):
        main, water = os.environ.get('HOF_DISCLOSURE_SOURCE'), os.environ.get('HOF_WATER_SOURCE')
        if not main or not water: self.skipTest('Actual supplied disclosure/water sources not selected')
        result = render(self.answers(True), Path(main).read_bytes(), Path(water).read_bytes())
        self.assertEqual(len(PdfReader(BytesIO(result)).pages), 6)
