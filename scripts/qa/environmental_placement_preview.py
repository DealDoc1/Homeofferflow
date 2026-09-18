"""Local unsigned TXR-1917 overflow/map specimen. Never contacts a provider."""
import argparse
import hashlib
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from lib.production_adapter import ENVIRONMENTAL_SOURCE_SHA256
from lib.txr_1917 import render_txr_1917, build_signwell_fields_txr1917
from scripts.render_txr_signwell_map_review import _overlay


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source = Path(args.source).read_bytes()
    assert hashlib.sha256(source).hexdigest() == ENVIRONMENTAL_SOURCE_SHA256
    reader = PdfReader(BytesIO(source))
    assert not reader.get_fields() and not any(
        ref.get_object().get('/Subtype') == '/Widget'
        for page in reader.pages for ref in page.get('/Annots', []))
    data = {'property_address': 'QA ONLY - NOT A REAL TRANSACTION. ' + 'Long Example Property Description ' * 12,
            'termination_days': '999', 'review_types': ['environmental', 'species', 'wetlands'],
            'buyer_names': ['QA Buyer One', 'QA Buyer Two'],
            'seller_names': ['QA Seller One', 'QA Seller Two'], '_for_signing': True}
    raw = render_txr_1917(source, data)
    fields = build_signwell_fields_txr1917(data)[0]
    writer = PdfWriter()
    for number, page in enumerate(PdfReader(BytesIO(raw)).pages, 1):
        page.merge_page(PdfReader(BytesIO(_overlay(number, fields))).pages[0])
        writer.add_page(page)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('wb') as stream:
        writer.write(stream)
    print({'pages': len(writer.pages), 'fields': len(fields), 'provider_contacted': False,
           'scope': 'Synthetic unsigned field outlines; not completed SignWell artwork'})


if __name__ == '__main__':
    main()
