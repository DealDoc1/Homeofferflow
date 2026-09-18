"""Private, synthetic source-blank review; never sends a signing request."""
import argparse
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from lib.txr_1919 import render_txr_1919, build_signwell_fields_txr1919
from scripts.render_txr_signwell_map_review import _overlay
from tests.test_txr_1919_renderer import sample_data
from tests.test_txr1919_source_bounds import long_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.read_bytes()
    reader = PdfReader(BytesIO(source))
    widgets = [a for page in reader.pages for a in page.get('/Annots', [])
               if a.get_object().get('/Subtype') == '/Widget']
    if reader.get_fields() or widgets:
        raise ValueError('Inspect interactive source before using this static source QA helper')
    normal = {**sample_data(), '_for_signing': True}
    normal['credit_documents'] = ['credit_report', 'employment', 'funds', 'financial_statement', 'other']
    second_only = {**sample_data(), '_for_signing': True}
    second_only['loans']['first']['enabled'] = False
    second_only['variance']['adjustment'] = 'sales_price'
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in [('both-loans-cash', normal), ('second-loan-price', second_only), ('long-answers', long_data())]:
        rendered = PdfReader(BytesIO(render_txr_1919(source, data)))
        fields = build_signwell_fields_txr1919(data)[0]
        writer = PdfWriter()
        writer.clone_document_from_reader(rendered)
        for number, page in enumerate(writer.pages, 1):
            if any(field['page'] == number for field in fields):
                page.merge_page(PdfReader(BytesIO(_overlay(number, fields))).pages[0])
        writer.add_metadata({'/Title': f'QA ONLY TXR-1919 {name} - synthetic and unsigned'})
        target = args.output_dir / f'{name}.pdf'
        writer.write(target)
        print(f'{name}: {len(writer.pages)} pages; {len(fields)} field outlines')


if __name__ == '__main__':
    main()
