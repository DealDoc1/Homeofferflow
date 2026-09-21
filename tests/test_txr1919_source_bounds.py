"""Independent source-blank geometry and lossless answer coverage for TXR-1919."""
from io import BytesIO
import unittest

import pdfplumber
from pypdf import PdfReader
from lib import txr_1919 as form
from tests.test_txr_1919_renderer import blank_pdf, sample_data


BOXES = [(386.04, 396.73, 206.76, 218.76), (474.78, 485.47, 206.76, 218.76),
         (214.26, 224.95, 217.74, 229.74), (510.36, 521.05, 217.74, 229.74),
         (183.12, 193.81, 228.78, 240.78), (61.38, 72.07, 413.76, 425.76),
         (61.38, 72.07, 463.74, 475.74), (195.24, 205.93, 524.76, 536.76),
         (332.88, 343.57, 524.76, 536.76)]
# x start/end, top of safe text band, top of printed underline.
BLANK_BOUNDS = [
    (36, 576, 116, 132.18), (97.02, 139.50, 202, 217.14),
    (193.80, 560.88, 224, 239.46), (61.38, 558.36, 241, 250.44),
    (445.02, 560.88, 410, 424.14), (92.88, 263.88, 426, 435.18),
    (472.62, 560.58, 426, 435.18), (102.78, 190.68, 444, 457.20),
    (485.04, 560.88, 460, 474.12), (92.88, 260.94, 476, 485.22),
    (470.40, 560.58, 476, 485.22), (102.78, 194.22, 494, 507.18),
    (67.74, 128.40, 545, 557.22), (316.32, 371.46, 620, 633.18),
    (435.42, 506.34, 620, 633.18), (311.22, 346.38, 642, 655.20),
    (409.50, 441.18, 642, 655.20),
]


def inside(char, bounds):
    left, right, top, bottom = bounds
    return (char['x0'] >= left and char['x1'] <= right and
            char['top'] >= top and char['bottom'] <= bottom)


def long_data():
    data = sample_data()
    data['loans']['first']['lender'] = 'LongLender' * 18
    data['loans']['second']['lender'] = 'SecondLender' * 15
    data['credit_documents'] = ['credit_report', 'employment', 'funds', 'financial_statement', 'other']
    data['credit_other'] = 'DocumentationRequested' * 8
    return {**data, '_for_signing': True}


class Txr1919SourceBoundsTests(unittest.TestCase):
    def test_every_mark_and_answer_is_inside_its_source_blank(self):
        for adjustment in ('cash', 'sales_price'):
            for first, second in ((True, False), (False, True), (True, True)):
                with self.subTest(adjustment=adjustment, first=first, second=second):
                    data = {**sample_data(), '_for_signing': True}
                    data['credit_documents'] = ['credit_report', 'employment', 'funds', 'financial_statement', 'other']
                    data['variance']['adjustment'] = adjustment
                    data['loans']['first']['enabled'] = first
                    data['loans']['second']['enabled'] = second
                    packet = form.render_txr_1919(blank_pdf(), data)
                    with pdfplumber.open(BytesIO(packet)) as pdf:
                        marks = [char for char in pdf.pages[0].chars
                                 if char['text'] == 'X' and char['fontname'] == 'Helvetica-Bold']
                        self.assertEqual(len(marks), 6 + int(first) + int(second))
                        for char in marks:
                            self.assertTrue(any(inside(char, box) for box in BOXES), char)
                        for char in pdf.pages[0].chars:
                            if char not in marks and char['text'] != ' ':
                                self.assertTrue(any(inside(char, box) for box in BLANK_BOUNDS), char)
                        for char in pdf.pages[1].chars:
                            self.assertTrue(inside(char, (38.88, 569.88, 48, 63.60)), char)

    def test_inactive_loan_and_other_document_answers_do_not_render(self):
        data = {**sample_data(), '_for_signing': True}
        data['loans']['second']['enabled'] = False
        data['credit_documents'] = ['credit_report']
        raw = form.render_txr_1919(blank_pdf(), data)
        text = '\n'.join(page.extract_text() or '' for page in PdfReader(BytesIO(raw)).pages)
        for hidden in ('Second Bank', '30000', '2025 tax return'):
            self.assertNotIn(hidden, text)
        self.assertNotIn('100', text, 'Disabled second-loan fee must not be printed')

    def test_long_answers_are_preserved_without_clipping_or_unreadable_type(self):
        data = long_data()
        raw = form.render_txr_1919(blank_pdf(), data)
        reader = PdfReader(BytesIO(raw))
        self.assertGreater(len(reader.pages), 2)
        continuation_text = ''.join(''.join((page.extract_text() or '').split()) for page in reader.pages[2:])
        for expected in (data['loans']['first']['lender'], data['loans']['second']['lender'], data['credit_other']):
            self.assertIn(expected.replace(' ', ''), continuation_text)
        with pdfplumber.open(BytesIO(raw)) as pdf:
            for page in pdf.pages[:2]:
                self.assertTrue(all(char['size'] >= 6 for char in page.chars))
            for page in pdf.pages[2:]:
                self.assertTrue(all(0 <= char['x0'] < char['x1'] <= 612 for char in page.chars))
        review = form.render_txr_1919(blank_pdf(), {**data, '_for_signing': False})
        self.assertEqual(len(PdfReader(BytesIO(review)).pages), len(reader.pages))

    def test_initials_and_continuations_use_correct_party_ids_and_printed_blanks(self):
        for buyers in (1, 2):
            for sellers in (1, 2):
                data = long_data()
                data['buyer_names'] = data['buyer_names'][:buyers]
                data['seller_names'] = data['seller_names'][:sellers]
                raw = form.render_txr_1919(blank_pdf(), data)
                fields = form.build_signwell_fields_txr1919(data)[0]
                initial = [field for field in fields if field['page'] == 1]
                expected = {str(i + 1) for i in range(buyers + sellers)}
                self.assertEqual({field['recipient_id'] for field in initial}, expected)
                for field in initial:
                    low, high = (189.99, 274.41) if 'buyer' in field['api_id'] else (324.47, 389.27)
                    self.assertGreaterEqual(field['x'] * .75, low)
                    self.assertLessEqual((field['x'] + field['width']) * .75, high)
                    self.assertLessEqual((field['y'] + field['height']) * .75, 752.65)
                for page in range(3, len(PdfReader(BytesIO(raw)).pages) + 1):
                    continuation = [field for field in fields if field['page'] == page]
                    self.assertEqual({field['recipient_id'] for field in continuation}, expected)
                    seller = next(field for field in continuation if 'seller1' in field['api_id'])
                    self.assertEqual(seller['recipient_id'], str(buyers + 1))
                    self.assertEqual(seller['x'] * .75, 374)

    def test_long_party_names_address_and_numbers_keep_identical_signing_pages(self):
        data = long_data()
        data['property_address'] = 'Long Address ' * 30
        data['buyer_names'] = ['BuyerName' * 20, 'SecondBuyer' * 16]
        data['seller_names'] = ['SellerName' * 18, 'SecondSeller' * 15]
        data['loan_terms']['first_rate_cap'] = '123456789.123456'
        review = PdfReader(BytesIO(form.render_txr_1919(blank_pdf(), {**data, '_for_signing': False})))
        signed_copy = PdfReader(BytesIO(form.render_txr_1919(blank_pdf(), data)))
        self.assertEqual(len(review.pages), len(signed_copy.pages))
        text = ''.join(''.join((page.extract_text() or '').split()) for page in signed_copy.pages[2:])
        for value in [data['property_address'], *data['buyer_names'], *data['seller_names'],
                      data['loan_terms']['first_rate_cap']]:
            self.assertIn(''.join(value.split()), text)
        for page in signed_copy.pages[:2]:
            self.assertNotIn('BuyerName', page.extract_text() or '')
        self.assertEqual(form.build_signwell_fields_txr1919(data),
                         form.build_signwell_fields_txr1919({**data, '_for_signing': False}))


if __name__ == '__main__':
    unittest.main()
