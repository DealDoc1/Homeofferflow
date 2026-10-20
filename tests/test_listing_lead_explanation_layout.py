from io import BytesIO
from pathlib import Path
import re
import unittest

from pypdf import PdfReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from lib import listing_lead_disclosure as lead
from lib.pdf_text import paragraph_markup


class ListingLeadExplanationLayoutTests(unittest.TestCase):
    def prepare(self, **changes):
        source = (Path(__file__).resolve().parents[1] / 'lead_based_paint_56-0.pdf').read_bytes()
        return lead.prepare_listing_lead(source, {
            'property_address': '100 QA ONLY Example Lane, Example City, TX 75001',
            'client_names': ['QA Seller One', 'QA Seller Two'],
            'signer_plan': 'clients_and_associate', **changes})

    def test_text_uses_line_height_not_paragraph_box_height(self):
        document = self.prepare()
        fields = [f for f in document.fields[0] if f['type'] == 'text']
        self.assertEqual(len(fields), 2)
        self.assertEqual({f['height'] for f in fields}, {18})
        self.assertEqual({f['width'] for f in fields}, {672})
        self.assertTrue(all(f['fixed_width'] and f['page'] == 2 for f in fields))
        self.assertEqual([f['y'] for f in fields], [(792-530)*4/3, (792-360)*4/3])
        self.assertEqual(len(document.checkbox_groups), 2)
        self.assertEqual(len(document.conditional_rules), 2)
        self.assertTrue(all(f['required'] is False for f in fields))

    def test_reserved_printed_regions_fit_long_wide_unicode_and_narrow_samples(self):
        for size in (9.75, 10.5):
            for text in ('W'*200, '李'*200, 'i'*200, 'QA Büro 李 '*20):
                with self.subTest(size=size, text=text[:10]):
                    paragraph = Paragraph(paragraph_markup(text), ParagraphStyle(
                        'preview', fontName='Helvetica', fontSize=size, leading=size*1.3, splitLongWords=True))
                    _, height = paragraph.wrap(500, lead.LIVE_DETAIL_BOX_HEIGHT-4)
                    self.assertLessEqual(height, lead.LIVE_DETAIL_BOX_HEIGHT-4)
        # These are preview bounds, not an assertion about the provider's font.
        self.assertGreater(530-lead.LIVE_DETAIL_BOX_HEIGHT, 360+23+11)
        self.assertGreater(360-lead.LIVE_DETAIL_BOX_HEIGHT, 70)

    def test_length_constraint_prevents_unbounded_manual_line_break_growth(self):
        field = next(f for f in self.prepare().fields[0] if f['type'] == 'text')
        pattern = field['validation_regex']
        for value in ('X', 'W'*200, '李'*200):
            self.assertIsNotNone(re.fullmatch(pattern, value))
        for value in ('', 'X'*201, 'X\nX', 'X\rX', '\n'*100):
            self.assertIsNone(re.fullmatch(pattern, value))
        self.assertIn('one paragraph', field['validation_regex_error_message'])

    def test_positive_missing_details_is_required_without_changing_signatures(self):
        document = self.prepare(lead_disclosure={'knowledge':'known','records':'none'})
        fields = [f for f in document.fields[0] if f['type'] == 'text']
        self.assertEqual(len(fields), 1)
        self.assertIs(fields[0]['required'], True)
        self.assertEqual(document.conditional_rules, [])
        signatures = [f for f in document.fields[0] if f['type'] == 'signature']
        self.assertEqual([f['recipient_id'] for f in signatures], ['1','2','associate'])
        self.assertEqual({f['height'] for f in signatures}, {20*4/3})
        reader = PdfReader(BytesIO(document.pdf))
        self.assertEqual(len(reader.pages), 2)
        self.assertIn('Use one paragraph', reader.pages[1].extract_text())

    def test_only_the_two_explanation_pages_change_from_reviewed_v1_specimen(self):
        from lib import listing_lead_signing_qa as qa
        _, _, cases = qa.build_packet()
        self.assertEqual(cases[0]['content_sha256'][0], '1b1268d9b00b8f87e8bed34332b9541d5a4a26494e347f163d1486215e264fd4')
        self.assertEqual(cases[1]['content_sha256'][0], cases[0]['content_sha256'][0])
        self.assertEqual(cases[2]['content_sha256'], ['6db3d0fca6e818a0d5082b1312b103c3574753b079074fd24f721625e2762e5e'])
        self.assertEqual(cases[3]['content_sha256'], [
            '0b81383b7c1e82463e48f1d0b592772aedb0936f5fae3968ff5bcf52a5662951',
            '3584c0f3e5148cd2c01826355d41fc41af6ba362dcd83062e5ca88fc358cfe14'])


if __name__ == '__main__':
    unittest.main()
