import json
import subprocess
import unittest
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
import pdfplumber
from lib.contract_money import currency_amount, format_currency, CurrencyInputError
from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms, minimal_offer

ROOT = Path(__file__).resolve().parents[1]


def collected_offer(financing):
    code = "const {collectExample}=require('./tests/currency_precision.runtime.cjs');process.stdout.write(JSON.stringify(collectExample(process.argv[1])));"
    answers = json.loads(subprocess.check_output(['node', '-e', code, financing], cwd=ROOT, text=True))
    return minimal_offer(**{key: value for key, value in answers.items() if value != '' and value is not None})


class CurrencyPrecisionTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()

    def test_actual_interview_runtime(self):
        result = subprocess.run(['node', '--test', 'tests/currency_precision.runtime.cjs'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_formatter_retains_whole_dollar_style_and_exact_cents(self):
        for value, expected in [(None, ''), ('', ''), (0, '0'), ('500,000.55', '500,000.55'), (Decimal('123.10'), '123.10'), (500000, '500,000'), ('2.5e2', '250')]:
            self.assertEqual(format_currency(value), expected)
        self.assertEqual(currency_amount('500000.55') - currency_amount('450000.44'), Decimal('50000.11'))

    def test_invalid_or_fractional_cent_amount_is_not_silently_changed(self):
        for value in ['NaN', 'Infinity', 'not money', '1.005', {}, True]:
            with self.subTest(value=value), self.assertRaises(CurrencyInputError):
                format_currency(value)

    def test_interview_values_reach_real_contract_and_addenda(self):
        for financing in ['cash', 'conventional', 'fha', 'va', 'usda']:
            with self.subTest(financing=financing):
                offer = collected_offer(financing)
                packet = adapter.fill_and_merge_20_19(offer)
                reader = PdfReader(BytesIO(packet))
                first = reader.pages[0].extract_text()
                self.assertIn('500,000.55', first)
                self.assertIn('500,000.55' if financing == 'cash' else '50,000.11', first)
                if financing != 'cash':
                    self.assertIn('450,000.44', first)
                    self.assertIn('450,000.44', reader.pages[12].extract_text())
                all_text = '\n'.join(page.extract_text() for page in reader.pages)
                for amount in ['5,000.45', '250.99', '150.75', '650.25', '1,000.75', '1,500.25', '1,000.55', '50.25']:
                    self.assertIn(amount, all_text, amount)

    def test_cash_ignores_stale_hidden_loan_amount(self):
        raw = adapter.fill_and_merge_20_19(minimal_offer(price='500000.55', loanAmount='old invalid answer'))
        self.assertIn('500,000.55', PdfReader(BytesIO(raw)).pages[0].extract_text())

    def test_three_decimal_rates_stay_inside_source_blanks(self):
        # Measured independently from TREC 40-11 (11-04-2024), top-origin points.
        # Keep the whole rendered value above the rule and before the printed %.
        regions = {
            'conventional': [(515.159, 543.959, 250, 260.759), (351.359, 393.599, 271, 282.119)],
            'fha': [(336.719, 380.879, 390, 400.319), (204.480, 243.119, 411, 421.679)],
            'va': [(227.039, 264.239, 447, 457.559), (87.479, 128.880, 468, 478.919)],
            'usda': [(228.959, 256.319, 504, 514.799), (515.039, 543.599, 515, 525.479)],
        }
        for financing, blanks in regions.items():
            for rate, fee in [('6.125', '1.125'), ('12.875', '10.125')]:
                with self.subTest(financing=financing, rate=rate):
                    offer = collected_offer(financing)
                    offer.update(interestRateCap=rate, originationCap=fee)
                    raw = adapter.fill_and_merge_20_19(offer)
                    with pdfplumber.open(BytesIO(raw)) as pdf:
                        # The source has literal space glyphs across its blanks.
                        # Remove only those invisible glyphs from extraction so
                        # they cannot split the overlay's rendered digits.
                        page = pdf.pages[12].filter(lambda obj: obj['object_type'] != 'char'
                                                   or not obj['text'].isspace())
                        for value, (left, right, top, bottom) in zip((rate, fee), blanks):
                            matches = [m for m in page.search(value, regex=False)
                                       if top - 3 < m['top'] < bottom + 3]
                            self.assertEqual(len(matches), 1, (value, matches))
                            box = matches[0]
                            self.assertGreaterEqual(box['x0'], left)
                            self.assertLessEqual(box['x1'], right)
                            self.assertGreaterEqual(box['top'], top)
                            self.assertLessEqual(box['bottom'], bottom)
