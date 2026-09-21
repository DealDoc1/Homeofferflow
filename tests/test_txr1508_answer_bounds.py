"""Source-measured showing answers, continuations and offline delivery checks."""
import base64
import copy
from io import BytesIO
import unittest

import pdfplumber
from pypdf import PdfReader
from lib.txr_1508 import _overlay, render_txr_1508, build_signwell_fields_txr1508
from lib.txr1508_answers import answer_layout
from tests.test_txr_1508_renderer import blank_one_page_pdf, sample_data
from tests.test_txr_render_send_snapshot import RenderSendFixture
from tests.test_txr_signing_request_path import MODULE


class Txr1508AnswerBoundsTests(unittest.TestCase):
    def test_answers_clear_measured_rules_and_adjoining_labels(self):
        data = {**sample_data(), 'property_address': 'Property', 'client_names': ['CustomerOne', 'CustomerTwo']}
        # Independent source rectangles: x0, x1, top of the printed underline.
        regions = {'Property': (108.02, 576.09, 141.38),
                   'BrokerName': (187.58, 403.63, 480.07),
                   '1234567': (475.66, 559.90, 480.07),
                   'AssociateName': (187.58, 403.63, 498.79),
                   '7654321': (475.66, 559.90, 498.79),
                   'CustomerOne': (137.78, 295.60, 560.47),
                   'CustomerTwo': (137.78, 295.60, 604.06)}
        with pdfplumber.open(BytesIO(_overlay(data,
                {'name': 'BrokerName', 'license_number': '1234567'},
                {'agent_name': 'AssociateName', 'license_number': '7654321'}))) as pdf:
            words = pdf.pages[0].extract_words()
            for value, (left, right, rule) in regions.items():
                with self.subTest(value=value):
                    word = next(w for w in words if w['text'] == value)
                    self.assertGreaterEqual(word['x0'], left)
                    self.assertLessEqual(word['x1'], right)
                    self.assertGreaterEqual(word['top'], rule - 12)
                    self.assertLess(word['bottom'], rule - 1)

    def test_selected_role_and_status_marks_fit_source_cells_including_stroke(self):
        cells = [(90.744, 272.87, 101.436, 284.87),
                 (295.61, 217.07, 306.302, 229.07),
                 (295.61, 173.48, 306.302, 185.48)]
        for role in ('associate', 'broker'):
            for statuses in (['no', 'no'], ['yes', 'no'], ['no', 'yes'], ['yes', 'yes']):
                data = {**sample_data(), 'signer_plan': role + '_and_clients',
                        'other_broker_agreement': statuses}
                with pdfplumber.open(BytesIO(_overlay(data, {}, {}))) as pdf:
                    selected = ([cells[0]] if role == 'associate' else [])
                    selected += [cells[n+1] for n, status in enumerate(statuses) if status == 'yes']
                    lines = pdf.pages[0].lines
                    self.assertEqual(len(lines), 2 * len(selected))
                    for index, (left, bottom, right, top) in enumerate(selected):
                        for line in lines[index*2:index*2+2]:
                            half = line['linewidth'] / 2
                            self.assertGreaterEqual(line['x0'] - half, left)
                            self.assertLessEqual(line['x1'] + half, right)
                            self.assertGreaterEqual(line['y0'] - half, bottom)
                            self.assertLessEqual(line['y1'] + half, top)

    def test_long_and_unicode_values_are_preserved_without_representation_language(self):
        data = {**sample_data(), 'property_address': 'A' * 400,
                'client_names': ['José <b>Customer</b> & 李 ' * 7, 'Second ' + 'N' * 170]}
        broker = {'legal_name': 'Broker' + 'B' * 170, 'license_number': '123456789' * 4}
        associate = {'name': 'Associate' + 'A' * 170, 'license_number': '987654321' * 4}
        original = copy.deepcopy((data, broker, associate))
        raw = render_txr_1508(blank_one_page_pdf(), data, broker, associate)
        with pdfplumber.open(BytesIO(raw)) as pdf:
            self.assertGreater(len(pdf.pages), 1)
            body = ''.join(''.join((p.crop((48,106,564,680)).extract_text() or '').split()) for p in pdf.pages[1:])
            for value in answer_layout(data, broker, associate)[1].values():
                self.assertIn(''.join(value.split()), body)
            for page in pdf.pages[1:]:
                text = page.extract_text()
                self.assertIn('attached showing form', text)
                self.assertIn('Customer 1 initials', text)
                self.assertIn('Customer 2 initials', text)
                self.assertIn('Associate initials', text)
                self.assertNotIn('Client', text)
                self.assertNotIn('attached agreement', text)
                # All footer labels end before their separate initial blanks.
                for x in (110, 286, 462):
                    label = page.crop((x-62,714,x,724))
                    self.assertTrue(label.chars)
                    self.assertLess(max(c['x1'] for c in label.chars), x)
                lines = page.crop((48,106,564,680)).extract_text().splitlines()
                self.assertNotIn(lines[-1], answer_layout(data, broker, associate)[1])
            self.assertTrue(all(c['size'] >= 7 for c in pdf.pages[0].chars))
        self.assertEqual((data, broker, associate), original)

    def test_inline_unicode_names_do_not_turn_into_missing_glyph_boxes(self):
        raw = render_txr_1508(blank_one_page_pdf(),
            {**sample_data(), 'client_names': ['José 李', 'Ana Gómez']}, {}, {})
        text = PdfReader(BytesIO(raw)).pages[0].extract_text()
        self.assertIn('José 李', text)
        self.assertIn('Ana Gómez', text)

    def test_real_offline_send_initials_every_appended_page_with_same_recipients(self):
        for role in ('associate', 'broker'):
            for count in (1, 2):
                for long in (False, True):
                    with self.subTest(role=role, count=count, long=long):
                        f = RenderSendFixture(self, code='TXR-1508', role=role, count=count, long=long)
                        self.assertTrue(f.run()['ok'])
                        pages = PdfReader(BytesIO(base64.b64decode(f.document['files'][0]['file_base64']))).pages
                        self.assertEqual(len(pages) > 1, long)
                        fields = f.document['fields'][0]
                        self.assertEqual(len({v['api_id'] for v in fields}), len(fields))
                        base = build_signwell_fields_txr1508(f.row['agreement_data'], client_count=count)[0]
                        self.assertEqual([v for v in fields if v['page'] == 1], base)
                        for page in range(2, len(pages) + 1):
                            extra = [v for v in fields if v['page'] == page]
                            self.assertEqual({v['recipient_id'] for v in extra}, {r['id'] for r in f.recipients})
                            self.assertTrue(all(v['required'] and v['type'] == 'initials' for v in extra))
                        self.assertFalse(f.document['apply_signing_order'])
                        self.assertEqual(f.downloads, 1)
                        self.assertEqual(f.sends, 1)

    def test_invalid_page_count_and_old_prepared_map_fail_before_send(self):
        for count in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                build_signwell_fields_txr1508(sample_data(), page_count=count)
        with self.assertRaisesRegex(ValueError, 'prepared again'):
            MODULE._current_txr_signing_map_revision('TXR-1508', {
                'signing_map_revision': 'txr-1508-2026-09-09-acknowledgement-calibrated-v1'})


if __name__ == '__main__':
    unittest.main()
