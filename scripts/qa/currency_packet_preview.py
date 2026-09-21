"""Render synthetic interview answers through the real packet builder, locally."""
import argparse
from io import BytesIO
import json
from pathlib import Path
from pypdf import PdfReader
from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms
from tests.test_currency_precision import collected_offer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    configure_local_forms()
    for financing in ('cash', 'conventional', 'fha', 'va', 'usda'):
        offer = collected_offer(financing)
        offer.update(buyer1='QA Currency Buyer', seller='QA Currency Seller',
                     address='100 QA ONLY Street', city='Frisco', county='Collin', zip='75034',
                     buyerEmail='buyer@example.test')
        raw = adapter.fill_and_merge_20_19(offer)
        path = output / (financing + '.pdf')
        path.write_bytes(raw)
        reader = PdfReader(BytesIO(raw))
        print(json.dumps({'financing': financing, 'pages': len(reader.pages), 'output': str(path),
                          'providerContacted': False, 'price': offer['price'],
                          'moneyPages': [i+1 for i, p in enumerate(reader.pages) if any(value in p.extract_text() for value in ('500,000.55','450,000.44','5,000.45','250.99','150.75','650.25','1,000.75','1,500.25','1,000.55','50.25'))]}))


if __name__ == '__main__':
    main()
