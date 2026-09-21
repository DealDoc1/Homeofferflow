"""Consumer notice layout and real rendering through offline signing delivery."""
import base64
import copy
from io import BytesIO
import unittest

import pdfplumber
from pypdf import PdfReader
from lib.txr_1506 import _overlay, render_txr_1506, build_signwell_fields_txr1506
from lib.txr1506_answers import answer_layout
from tests.test_txr_1506_renderer import blank_six_page_pdf, sample_data
from tests.test_txr_render_send_snapshot import RenderSendFixture
from tests.test_txr_signing_request_path import MODULE


class Txr1506AnswerBoundsTests(unittest.TestCase):
    def test_names_clear_the_source_rules_and_consumer_headers_are_populated(self):
        data = {**sample_data(), 'client_names': ['ConsumerOne', 'ConsumerTwo']}
        with pdfplumber.open(BytesIO(_overlay(data, {'name': 'BrokerName'}))) as pdf:
            self.assertEqual(len(pdf.pages), 6)
            self.assertFalse(pdf.pages[0].chars)
            for page in pdf.pages[1:]:
                header = page.crop((231.89, 24, 504.034, 38.1))
                self.assertIn('ConsumerOne, ConsumerTwo', header.extract_text())
                self.assertTrue(all(c['x0'] >= 231.89 and c['x1'] <= 504.034 and
                                    c['bottom'] < 38.1 for c in header.chars))
            words = pdf.pages[5].extract_words()
            for text, top in [('BrokerName', 581.83), ('ConsumerOne', 686.86), ('ConsumerTwo', 721.42)]:
                word = next(w for w in words if w['text'] == text and w['top'] > 550)
                self.assertGreaterEqual(word['x0'], 36)
                self.assertLessEqual(word['x1'], 288.05)
                self.assertGreaterEqual(word['top'], top - 12)
                self.assertLess(word['bottom'], top - 1)

    def test_signing_copy_has_no_typed_answer_in_any_provider_field(self):
        for role in ('associate', 'broker'):
            data = {**sample_data(), '_for_signing': True, 'signer_plan': 'consumers_and_' + role}
            with pdfplumber.open(BytesIO(_overlay(data, {'name': 'Notice Brokerage'}))) as pdf:
                for field in build_signwell_fields_txr1506(data, client_count=2)[0]:
                    left, top = field['x'] * .75, field['y'] * .75
                    right, bottom = left + field['width'] * .75, top + field['height'] * .75
                    for char in pdf.pages[field['page']-1].chars:
                        self.assertFalse(char['x0'] < right and char['x1'] > left and
                                         char['top'] < bottom and char['bottom'] > top,
                                         f'Typed answer overlaps {field["api_id"]}')
                self.assertIn('Test Consumer One', pdf.pages[5].extract_text())

    def test_other_information_uses_only_its_two_lines(self):
        text = ('Ask the broker about the property before signing. ' * 4).strip()
        data = {**sample_data(), 'additional_notice': text}
        pages, overflow = answer_layout(data, {})
        self.assertFalse(overflow)
        with pdfplumber.open(BytesIO(_overlay(data, {}))) as pdf:
            answer = pdf.pages[5].crop((36,460.55,574.58,485.87))
            self.assertEqual(' '.join(answer.extract_text().split()), text)
            self.assertTrue(all(c['x0'] >= 36 and c['x1'] <= 574.58 for c in answer.chars))
            for baseline, underline_top in [(324, 472), (311, 484.7)]:
                line = [c for c in answer.chars if abs((792 - c['bottom']) - (baseline - 1.656)) < .1]
                self.assertTrue(line)
                self.assertTrue(all(c['bottom'] < underline_top for c in line))

    def test_long_notice_and_names_preserved_in_signed_and_unsigned_copies(self):
        for signing in (False, True):
            data = {**sample_data(), '_for_signing': signing,
                    'additional_notice': 'W' * 1000,
                    'client_names': ['José <b>Consumer</b> & 李 ' * 7, 'Second ' + 'N' * 170]}
            broker = {'legal_name': 'Broker' + 'B' * 175}
            original = copy.deepcopy((data, broker))
            self.assertNotIn('Consumer names', answer_layout(data, broker)[1])
            raw = render_txr_1506(blank_six_page_pdf(), data, broker)
            with pdfplumber.open(BytesIO(raw)) as pdf:
                self.assertGreater(len(pdf.pages), 6)
                body = ''.join(''.join((p.crop((48,106,564,680)).extract_text() or '').split()) for p in pdf.pages[6:])
                for value in answer_layout(data, broker)[1].values():
                    self.assertIn(''.join(value.split()), body)
                for page in pdf.pages[6:]:
                    text = page.extract_text()
                    self.assertIn('attached consumer notice', text)
                    self.assertIn('Consumer 1 initials', text)
                    self.assertIn('Consumer 2 initials', text)
                    self.assertIn('Associate initials', text)
                    self.assertNotIn('Client', text)
                    self.assertNotIn('attached agreement', text)
                    self.assertTrue(page.crop((48,106,564,680)).chars)
                self.assertTrue(all(c['size'] >= 7 for page in pdf.pages[:6] for c in page.chars))
            self.assertEqual((data, broker), original)

    def test_real_offline_send_preserves_names_and_initials_all_appended_pages(self):
        for role in ('associate', 'broker'):
            for count in (1, 2):
                for long in (False, True):
                    with self.subTest(role=role, count=count, long=long):
                        f = RenderSendFixture(self, code='TXR-1506', role=role, count=count, long=long)
                        self.assertTrue(f.run()['ok'])
                        raw = base64.b64decode(f.document['files'][0]['file_base64'])
                        pages = PdfReader(BytesIO(raw)).pages
                        self.assertEqual(len(pages) > 6, long)
                        self.assertIn('Draft Client One', pages[5].extract_text())
                        with pdfplumber.open(BytesIO(raw)) as pdf:
                            self.assertFalse(pdf.pages[5].crop((36,668,288.05,723)).chars)
                        fields = f.document['fields'][0]
                        base = build_signwell_fields_txr1506(f.row['agreement_data'], client_count=count)[0]
                        self.assertEqual([v for v in fields if v['page'] <= 6], base)
                        self.assertEqual(len({v['api_id'] for v in fields}), len(fields))
                        for page in range(7, len(pages)+1):
                            extra = [v for v in fields if v['page'] == page]
                            self.assertEqual({v['recipient_id'] for v in extra}, {r['id'] for r in f.recipients})
                            self.assertTrue(all(v['required'] and v['type'] == 'initials' for v in extra))
                        self.assertFalse(f.document['apply_signing_order'])
                        self.assertEqual(f.downloads, 1)
                        self.assertEqual(f.sends, 1)

    def test_inline_unicode_names_remain_readable(self):
        raw = render_txr_1506(blank_six_page_pdf(),
            {**sample_data(), 'client_names': ['José 李', 'Ana Gómez']}, {})
        text = PdfReader(BytesIO(raw)).pages[5].extract_text()
        self.assertIn('José 李', text)
        self.assertIn('Ana Gómez', text)

    def test_invalid_page_counts_and_old_prepared_map_rejected(self):
        for count in (5, 0, True, 6.5):
            with self.assertRaises(ValueError):
                build_signwell_fields_txr1506(sample_data(), page_count=count)
        with self.assertRaisesRegex(ValueError, 'prepared again'):
            MODULE._current_txr_signing_map_revision('TXR-1506', {
                'signing_map_revision': 'txr-1506-2026-09-09-final-page-calibrated-v1'})


if __name__ == '__main__':
    unittest.main()
