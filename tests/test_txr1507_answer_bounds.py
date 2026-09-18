"""Independent 06-15-26 source-rule bounds and lossless short-form answers."""
from io import BytesIO
import unittest
import pdfplumber
from pypdf import PdfReader
from lib.txr_1507 import _overlay, render_txr_1507
from lib.txr1507_answers import answer_layout
from tests.test_txr_1507_renderer import blank_two_page_pdf, sample_data
from tests.test_txr_signing_request_path import MODULE
from tests.test_txr_render_send_snapshot import RenderSendFixture


class Txr1507AnswerBoundsTests(unittest.TestCase):
    def test_every_compensation_amount_fits_its_actual_printed_blank(self):
        data = {**sample_data(), 'showing_fee': '987.65',
                'compensation': {'purchase_percentage': '3.125', 'purchase_flat_fee': '12500.25',
                    'lease_one_month_percentage': '100', 'lease_total_rents_percentage': '4.375',
                    'lease_flat_fee': '2500.75'}}
        # Measured source rectangle extents; independent of the answer map.
        regions = {'3.125': (156.02, 587.99, 216.04, 598.99),
                   '12500.25': (403.15, 587.99, 504.09, 598.99),
                   '100': (137.66, 606.74, 180.02, 617.74),
                   '4.375': (312.65, 606.74, 360.07, 617.74),
                   '2500.75': (221.45, 619.34, 324.05, 630.34)}
        with pdfplumber.open(BytesIO(_overlay(data, {}, {}))) as pdf:
            words = pdf.pages[0].extract_words()
            for value, (left, top, right, bottom) in regions.items():
                with self.subTest(value=value):
                    matches = [w for w in words if w['text'] == value]
                    self.assertEqual(len(matches), 1)
                    word = matches[0]
                    self.assertGreaterEqual(word['x0'], left)
                    self.assertGreaterEqual(word['top'], top)
                    self.assertLessEqual(word['x1'], right)
                    self.assertLessEqual(word['bottom'], bottom)

    def test_dates_and_execution_values_fit_their_source_regions(self):
        data = {**sample_data(), 'client_names': ['ClientOne', 'ClientTwo']}
        broker = {'legal_name': 'BrokerName', 'license_number': '1234567'}
        agent = {'agent_name': 'AssociateName', 'license_number': '7654321'}
        with pdfplumber.open(BytesIO(_overlay(data, broker, agent))) as pdf:
            for value, left, right in [('2026-08-01', 223.61, 297.17), ('2027-01-31', 430.87, 531.69)]:
                word = next(w for w in pdf.pages[0].extract_words() if w['text'] == value)
                self.assertGreaterEqual(word['x0'], left)
                self.assertLessEqual(word['x1'], right)
                self.assertLessEqual(word['bottom'], 272.69)
            words = pdf.pages[1].extract_words()
            for value, left, right, baseline in [
                ('BrokerName', 36, 236, 502.87), ('1234567', 238.61, 288.05, 502.87),
                ('ClientOne', 324.05, 576.10, 502.87), ('AssociateName', 36, 236, 575.35),
                ('7654321', 238.61, 288.05, 575.35), ('ClientTwo', 324.05, 576.10, 575.35),
            ]:
                word = next(w for w in words if w['text'] == value and w['top'] > 450)
                self.assertGreaterEqual(word['x0'], left)
                self.assertLessEqual(word['x1'], right)
                self.assertGreaterEqual(word['top'], baseline - 12)
                self.assertLessEqual(word['bottom'], baseline)

    def test_long_answers_preserve_full_values_and_source_bounds(self):
        data = {**sample_data(), 'client_names': ['José <b>Client</b> & 李 ' * 7, 'Second ' + 'N' * 170],
                'market_area': 'Market' + 'W' * 790}
        broker = {'legal_name': 'Broker' + 'B' * 174}
        agent = {'name': 'Associate' + 'A' * 170}
        raw = render_txr_1507(blank_two_page_pdf(), data, broker, agent)
        with pdfplumber.open(BytesIO(raw)) as pdf:
            self.assertGreater(len(pdf.pages), 2)
            body = ''.join(''.join((p.crop((48,106,564,680)).extract_text() or '').split()) for p in pdf.pages[2:])
            for value in answer_layout(data, broker, agent)[1].values():
                self.assertIn(''.join(value.split()), body)
            for p in pdf.pages[:2]:
                self.assertTrue(all(c['size'] >= 7 and 35 <= c['x0'] < c['x1'] <= 576.1 for c in p.chars))
            self.assertIn('See exhibit', pdf.pages[0].extract_text())
            self.assertIn('TXR-1507 - Answer Continuation', pdf.pages[2].extract_text())

    def test_actual_short_form_send_initials_every_appended_page(self):
        import base64
        for role in ('associate', 'broker'):
            for count in (1, 2):
                with self.subTest(role=role, count=count):
                    f = RenderSendFixture(self, code='TXR-1507', role=role, count=count, long=True)
                    f.run()
                    pages = PdfReader(BytesIO(base64.b64decode(f.document['files'][0]['file_base64']))).pages
                    self.assertGreater(len(pages), 2)
                    for page in range(3, len(pages) + 1):
                        fields = [v for v in f.document['fields'][0] if v['page'] == page]
                        self.assertEqual({v['recipient_id'] for v in fields}, {r['id'] for r in f.recipients})
                        self.assertTrue(all(v['required'] and v['type'] == 'initials' for v in fields))

    def test_previous_prepared_copy_cannot_silently_use_new_continuations(self):
        with self.assertRaisesRegex(ValueError, 'prepared again'):
            MODULE._current_txr_signing_map_revision('TXR-1507', {
                'signing_map_revision': 'txr-1507-2026-09-12-completed-packet-calibrated-v2'})

    def test_continuation_heading_stays_with_its_answer(self):
        data = {**sample_data(),
                'client_names': ['Review Client One ' + 'FamilyName ' * 14,
                                 'Review Client Two ' + 'FamilyName ' * 14],
                'market_area': ('QA district and surrounding review neighborhoods; ' * 16).strip()}
        raw = render_txr_1507(blank_two_page_pdf(), data,
            {'legal_name': 'Review Brokerage ' + 'Regional Office ' * 10},
            {'name': 'Review Associate ' + 'Professional Name ' * 8})
        with pdfplumber.open(BytesIO(raw)) as pdf:
            self.assertGreater(len(pdf.pages), 3)
            for page in pdf.pages[2:]:
                lines = page.crop((48,106,564,680)).extract_text().splitlines()
                self.assertFalse(lines[-1].startswith(('Paragraph ', 'Execution - ')))


if __name__ == '__main__':
    unittest.main()
