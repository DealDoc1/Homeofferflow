"""Source-measured bounds are independent of renderer constants."""
from io import BytesIO
from itertools import product
import unittest
import pdfplumber
from pypdf import PdfReader
from lib import txr_1905 as mineral, txr_1914 as financing
from tests.test_txr_1914_renderer import blank_pdf, sample_data

# left, right, top, bottom; measured Wingdings source cells.
FINANCE_CELLS = {
    1: {
        'credit_report': (402.24, 412.93, 261.42, 273.42),
        'employment': (484.44, 495.13, 261.42, 273.42),
        'funds': (245.4, 256.09, 272.46, 284.46),
        'financial_statement': (65.88, 76.57, 283.44, 295.44),
        'other': (356.34, 367.03, 283.44, 295.44),
        'one_payment': (65.88, 76.57, 538.44, 550.44),
        'maturity': (206.04, 216.73, 549.42, 561.42),
        'monthly': (280.86, 291.55, 549.42, 561.42),
        'quarterly': (340.32, 351.01, 549.42, 561.42),
        'monthly_installments': (65.88, 76.57, 568.44, 580.44),
        'monthly_including_interest': (336.54, 347.23, 568.44, 580.44),
        'monthly_plus_interest': (445.44, 456.13, 568.44, 580.44),
        'interest_only_then_installments': (65.88, 76.57, 620.46, 632.46),
        'later_including_interest': (285.9, 296.59, 631.44, 643.44),
        'later_plus_interest': (394.5, 405.19, 631.44, 643.44),
        'consent_not_required': (79.38, 90.07, 710.46, 722.46),
    },
    2: {
        'consent_required': (68.94, 79.63, 94.26, 106.26),
        'insurance_required': (409.26, 419.95, 220.26, 232.26),
        'insurance_not_required': (460.26, 470.95, 220.26, 232.26),
        'escrow_not_required': (73.44, 84.13, 269.28, 281.28),
        'escrow_required': (73.44, 84.13, 310.26, 322.26),
        'will': (104.94, 115.63, 409.26, 421.26),
        'will_not': (150.48, 161.17, 409.26, 421.26),
        'buyer': (406.44, 417.13, 409.26, 421.26),
        'seller': (458.1, 468.79, 409.26, 421.26),
    },
}
FINANCE_BLANKS = [
    (34.56, 574.56, 125, 140.76), (128.22, 173.94, 255, 271.8),
    (395.88, 556.18, 280, 295.43), (65.88, 551.88, 296, 304.86),
    (386, 460.53, 430, 443.1), (78.96, 105.42, 454, 463.86),
    (202.5, 421.98, 536, 548.82), (245.22, 328.62, 566, 578.82),
    (223.26, 343.86, 581, 589.86), (208.98, 281.88, 592, 600.9),
    (347.82, 417.18, 618, 630.84), (181.5, 282.06, 633, 641.82),
    (179.94, 295.74, 644, 652.86), (164.4, 234.78, 655, 663.9),
]
MINERAL_CELLS = {'all': (73.44, 85.90, 267.90, 281.88),
                 'undivided_interest': (73.44, 85.90, 289.44, 303.42),
                 'waived': (103.86, 116.32, 330.24, 344.22),
                 'not_waived': (147, 159.46, 330.24, 344.22)}


def inside(char, bounds):
    left, right, top, bottom = bounds
    return left <= char['x0'] < char['x1'] <= right and top <= char['top'] < char['bottom'] <= bottom


def marks(page):
    return [c for c in page.chars if c['text'] == 'X' and c['fontname'] == 'Helvetica-Bold']


def mineral_data():
    return {**sample_data(), 'reservation_choice': 'undivided_interest',
            'undivided_interest': '25', 'surface_rights': 'not_waived', '_for_signing': True}


def payment_variants():
    for timing in ('maturity', 'monthly', 'quarterly'):
        yield {'plan': 'one_payment', 'interest_timing': timing, 'due_after_months': '12'}, {'one_payment', timing}
    for plan, prefix in [('monthly_installments', 'monthly'), ('interest_only_then_installments', 'later')]:
        for style in ('including_interest', 'plus_interest'):
            yield {'plan': plan, 'interest_style': style, 'installment_amount': '1800',
                   'begins_after_months': '1', 'payoff_after_months': '180', 'interest_only_months': '12'}, {plan, prefix + '_' + style}


class FinancingMineralBoundsTests(unittest.TestCase):
    def assert_cells(self, page, expected, cells):
        selected = marks(page)
        self.assertEqual(len(selected), len(expected))
        for key in expected:
            self.assertEqual(sum(inside(c, cells[key]) for c in selected), 1, key)

    def test_financing_payment_elections_and_all_answers_fit_source(self):
        docs = {'credit_report', 'employment', 'funds', 'financial_statement', 'other'}
        for payment, expected in payment_variants():
            with self.subTest(payment=payment):
                data = {**sample_data(), '_for_signing': True, 'payment': payment,
                        'credit_documents': list(docs), 'property_transfer': 'consent_not_required'}
                raw = financing.render_txr_1914(blank_pdf(), data)
                with pdfplumber.open(BytesIO(raw)) as pdf:
                    self.assert_cells(pdf.pages[0], expected | docs | {'consent_not_required'}, FINANCE_CELLS[1])
                    selected = marks(pdf.pages[0])
                    for char in pdf.pages[0].chars:
                        if char not in selected and char['text'] != ' ':
                            self.assertTrue(any(inside(char, box) for box in FINANCE_BLANKS), char)
                    for char in pdf.pages[1].chars:
                        if char not in marks(pdf.pages[1]) and char['text'] != ' ':
                            self.assertTrue(inside(char, (37.44, 568.44, 48, 63.6)), char)
                text = PdfReader(BytesIO(raw)).pages[0].extract_text()
                self.assertIn('12 months' if payment['plan'] == 'one_payment' else '1 month', text)

    def test_financing_all_page_two_elections_are_explicit_and_in_correct_boxes(self):
        escrows = [{'choice': 'not_required', 'third_party_servicer': 'will', 'cost_paid_by': 'buyer'}]
        escrows += [{'choice': 'required', 'third_party_servicer': service, 'cost_paid_by': payer}
                    for service, payer in product(('will', 'will_not'), ('buyer', 'seller'))]
        for consent, insurance, escrow in product(('consent_required', 'consent_not_required'),
                                                 ('required', 'not_required'), escrows):
            data = {**sample_data(), '_for_signing': True, 'property_transfer': consent,
                    'casualty_insurance': insurance, 'escrow': escrow}
            expected = {'insurance_' + insurance, 'escrow_' + escrow['choice']}
            if consent == 'consent_required':
                expected.add(consent)
            if escrow['choice'] == 'required':
                expected |= {escrow['third_party_servicer'], escrow['cost_paid_by']}
            with pdfplumber.open(BytesIO(financing.render_txr_1914(blank_pdf(), data))) as pdf:
                self.assert_cells(pdf.pages[1], expected, FINANCE_CELLS[2])

    def test_mineral_elections_fit_and_percentage_has_its_unit(self):
        for reservation, surface in product(('all', 'undivided_interest'), ('waived', 'not_waived')):
            data = {**mineral_data(), 'reservation_choice': reservation, 'surface_rights': surface}
            raw = mineral.render_txr_1905(blank_pdf(1), data)
            with pdfplumber.open(BytesIO(raw)) as pdf:
                self.assert_cells(pdf.pages[0], {reservation, surface}, MINERAL_CELLS)
                for char in pdf.pages[0].chars:
                    if char not in marks(pdf.pages[0]) and char['text'] != ' ':
                        self.assertTrue(any(inside(char, bounds) for bounds in
                            [(37.08, 577.08, 90, 107.28), (241.2, 289.44, 285, 301.26)]), char)
            text = PdfReader(BytesIO(raw)).pages[0].extract_text()
            self.assertEqual('25%' in text, reservation == 'undivided_interest')

    def test_blank_data_does_not_invent_financial_or_mineral_elections(self):
        for module, code, pages in [(financing, 1914, 2), (mineral, 1905, 1)]:
            raw = getattr(module, f'render_txr_{code}')(blank_pdf(pages), {'_for_signing': True})
            with pdfplumber.open(BytesIO(raw)) as pdf:
                self.assertTrue(all(not marks(page) for page in pdf.pages))

    def test_execution_fields_and_initials_fit_rules_for_each_party_count(self):
        for buyers, sellers in product((1, 2), repeat=2):
            for module, code in [(financing, 1914), (mineral, 1905)]:
                data = {'buyer_names': ['Buyer One', 'Buyer Two'][:buyers],
                        'seller_names': ['Seller One', 'Seller Two'][:sellers]}
                fields = getattr(module, f'build_signwell_fields_txr{code}')(data)[0]
                for field in fields:
                    role = 'buyer' if '_buyer' in field['api_id'] else 'seller'
                    second = role + '2_' in field['api_id']
                    expected = (2 if second else 1) + (buyers if role == 'seller' else 0)
                    self.assertEqual(field['recipient_id'], str(expected))
                    if field['type'] == 'initials':
                        left, right, bottom = (194.02, 278.44, 769.86) if role == 'buyer' else (343.44, 408.24, 769.86)
                    elif code == 1914:
                        left, right = (55.44, 298.92) if role == 'buyer' else (311.94, 559.44)
                        bottom = 632.76 if second else 555.78
                    else:
                        left, right = (55.14, 312.66) if role == 'buyer' else (329.04, 561)
                        bottom = 679.8 if second else 623.46
                    self.assertGreaterEqual(field['x'] * .75, left)
                    self.assertLessEqual((field['x'] + field['width']) * .75, right)
                    self.assertLessEqual((field['y'] + field['height']) * .75, bottom)
                    self.assertGreaterEqual(field['y'] * .75, bottom - 22)

    def test_long_answers_preserved_and_continuations_route_to_actual_party_ids(self):
        for module, code, source_pages in [(financing, 1914, 2), (mineral, 1905, 1)]:
            data = {**mineral_data(), 'property_address': 'LongAddress' * 35,
                    'buyer_names': ['BuyerName' * 20], 'seller_names': ['SellerName' * 18, 'OtherSeller' * 16],
                    'credit_other': 'Documentation' * 13}
            raw = getattr(module, f'render_txr_{code}')(blank_pdf(source_pages), data)
            reader = PdfReader(BytesIO(raw))
            self.assertGreater(len(reader.pages), source_pages)
            text = ''.join(''.join((p.extract_text() or '').split()) for p in reader.pages[source_pages:])
            for value in [data['property_address'], *data['buyer_names'], *data['seller_names']]:
                self.assertIn(value, text)
            if code == 1914:
                self.assertIn(data['credit_other'], text)
            review = getattr(module, f'render_txr_{code}')(blank_pdf(source_pages), {**data, '_for_signing': False})
            self.assertEqual(len(PdfReader(BytesIO(review)).pages), len(reader.pages))
            fields = getattr(module, f'build_signwell_fields_txr{code}')(data)[0]
            for page in range(source_pages + 1, len(reader.pages) + 1):
                initials = [f for f in fields if f['page'] == page]
                self.assertEqual({f['recipient_id'] for f in initials}, {'1', '2', '3'})
                seller = next(f for f in initials if 'seller1' in f['api_id'])
                self.assertEqual(seller['recipient_id'], '2')
                self.assertEqual(seller['x'] * .75, 374)
            with pdfplumber.open(BytesIO(raw)) as pdf:
                for page in pdf.pages[source_pages:]:
                    self.assertTrue(all(0 <= c['x0'] < c['x1'] <= 612 for c in page.chars))


if __name__ == '__main__':
    unittest.main()
