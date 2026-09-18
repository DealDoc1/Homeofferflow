"""Offline before/after imprint QA. Requires private blank sources and Poppler."""
import argparse
import hashlib
import importlib
from io import BytesIO
from pathlib import Path
import subprocess
from unittest.mock import patch

from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter
from lib.txr_source_imprint import SOURCE_IMPRINTS, remove_known_source_imprint
from scripts.run_private_txr_draft_qa import _data, _renderers


def review_cases():
    cases = {code: (renderer, _data()[code], pages)
             for code, (_, renderer, pages) in _renderers().items()}
    common = {'property_address': '100 Example Street, Frisco',
              'buyer_names': ['Example Buyer One', 'Example Buyer Two'],
              'seller_names': ['Example Seller One', 'Example Seller Two']}
    overrides = {
        1905: {'reservation_choice': 'all', 'surface_rights': 'waived'},
        1919: {'credit_days': '7', 'credit_documents': ['credit_report'],
               'loans': {'first': {'enabled': True, 'lender': 'Example lender',
                                   'balance': '400000', 'monthly_payment': '2500'}},
               'loan_terms': {'first_fee_cap': '1500', 'first_rate_cap': '4'},
               'variance': {'adjustment': 'cash', 'termination_threshold': '1000'}},
        1953: {'lease_status': 'assignment', 'delivery_choice': 'not_received', 'delivery_days': '7'},
        1954: {'leased_fixture_types': ['solar_panels'], 'assumed_fixture_leases': ['solar_panels'],
               'buyer_first_cost': '2500', 'removal_choice': 'will_not', 'delivery_choice': 'received'},
    }
    for number, data in overrides.items():
        module = importlib.import_module(f'lib.txr_{number}')
        answers = {**common, **data}
        cases[f'TXR{number}'] = (getattr(module, f'render_txr_{number}'), answers, 2 if number == 1919 else 1)
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_dir', type=Path)
    parser.add_argument('output_dir', type=Path)
    parser.add_argument('--forms', nargs='+', choices=tuple(review_cases()),
                        help='Limit review to selected privately supplied source forms.')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pages_checked = 0
    for code, (renderer, data, expected_pages) in review_cases().items():
        if args.forms and code not in args.forms:
            continue
        form_code = code.replace('TXR', 'TXR-')
        source = args.source_dir / f'{code}.pdf'
        raw = source.read_bytes()
        digest, indices = SOURCE_IMPRINTS[form_code]
        assert hashlib.sha256(raw).hexdigest() == digest, f'{code}: unreviewed source'
        original = PdfReader(BytesIO(raw))
        writer = PdfWriter()
        for page in original.pages:
            writer.add_page(page)
        expected = [[entry for i, entry in enumerate(page.get_contents().operations) if i not in indices[n]]
                    for n, page in enumerate(original.pages)]
        imprint_lines = [[str(page.get_contents().operations[i][0][0][0]) for i in indices[n]]
                         for n, page in enumerate(original.pages)]
        assert remove_known_source_imprint(writer, raw, form_code) == 2 * expected_pages
        for number, page in enumerate(writer.pages):
            assert page.get_contents().operations == expected[number], f'{code}: non-imprint operations changed'
        with patch(f'lib.txr_{code[3:]}.remove_known_source_imprint', return_value=0):
            before = renderer(raw, data)
        after = renderer(raw, data)
        assert len(PdfReader(BytesIO(after)).pages) == expected_pages
        for label, content in [('before', before), ('after', after)]:
            target = args.output_dir / f'{code}-{label}.pdf'
            target.write_bytes(content)
            subprocess.run(['pdftoppm', '-r', '100', '-png', str(target), str(target.with_suffix(''))], check=True)
        for number in range(1, expected_pages + 1):
            before_image = Image.open(args.output_dir / f'{code}-before-{number}.png').convert('RGB')
            after_image = Image.open(args.output_dir / f'{code}-after-{number}.png').convert('RGB')
            assert before_image.size == after_image.size
            diff = ImageChops.difference(before_image, after_image).getbbox()
            assert diff is not None, f'{code} p{number}: imprint still visible'
            # Original imprint baselines are 17/26pt from the bottom; no
            # difference is permitted outside that measured bottom 34pt band.
            assert diff[1] >= after_image.height - 34 * 100 / 72, (code, number, diff)
            text = PdfReader(BytesIO(after)).pages[number - 1].extract_text()
            assert all(''.join(line.split()) not in ''.join(text.split()) for line in imprint_lines[number - 1])
            # pypdf 4 inserts a space before the source's hyphen; this is an
            # extraction difference, not a visible form-code change.
            assert code in ''.join(text.split()).replace('-', '')
            if code in _renderers():
                assert f'Page {number} of {expected_pages}' in ' '.join(text.split())
            pages_checked += 1
        assert source.read_bytes() == raw, f'{code}: source file changed'
        print(f'{code}: {expected_pages} pages; only two footer operations removed per page; all pixels above footer unchanged')
    print(f'PASS: {pages_checked} pages, source files preserved, no network/provider/database activity.')


if __name__ == '__main__':
    main()
