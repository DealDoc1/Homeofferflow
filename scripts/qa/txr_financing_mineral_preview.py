"""Render synthetic source-specific QA outlines; no provider or network calls."""
import argparse
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from lib import txr_1905 as mineral, txr_1914 as financing
from scripts.render_txr_signwell_map_review import _overlay
from tests.test_txr_1914_renderer import sample_data
from tests.test_txr_financing_mineral_source_bounds import mineral_data


def specimens():
    standard = {**sample_data(), '_for_signing': True,
                'credit_documents': ['credit_report', 'employment', 'funds', 'financial_statement', 'other']}
    yield financing, 1914, 'monthly', standard
    yield financing, 1914, 'single', {**standard, 'payment': {
        'plan': 'one_payment', 'due_after_months': '12', 'interest_timing': 'quarterly'},
        'property_transfer': 'consent_not_required', 'casualty_insurance': 'not_required',
        'escrow': {'choice': 'not_required'}}
    yield financing, 1914, 'interest-only', {**standard, 'payment': {
        'plan': 'interest_only_then_installments', 'interest_only_months': '12',
        'installment_amount': '1750', 'interest_style': 'plus_interest',
        'begins_after_months': '13', 'payoff_after_months': '120'},
        'escrow': {'choice': 'required', 'third_party_servicer': 'will_not', 'cost_paid_by': 'seller'}}
    yield mineral, 1905, 'partial', mineral_data()
    yield mineral, 1905, 'all', {**mineral_data(), 'reservation_choice': 'all', 'surface_rights': 'waived'}
    long = {**mineral_data(), 'property_address': 'LongAddress' * 35,
            'buyer_names': ['BuyerName' * 20], 'seller_names': ['SellerName' * 18, 'OtherSeller' * 16],
            'credit_other': 'Documentation' * 13}
    yield financing, 1914, 'overflow', long
    yield mineral, 1905, 'overflow', long


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for module, code, name, data in specimens():
        raw = (args.source_dir / f'TXR{code}.pdf').read_bytes()
        source = PdfReader(BytesIO(raw))
        widgets = [a for page in source.pages for a in page.get('/Annots', [])
                   if a.get_object().get('/Subtype') == '/Widget']
        if source.get_fields() or widgets:
            raise ValueError('Inspect interactive source before using this static-source QA helper')
        rendered = PdfReader(BytesIO(getattr(module, f'render_txr_{code}')(raw, data)))
        fields = getattr(module, f'build_signwell_fields_txr{code}')(data)[0]
        writer = PdfWriter()
        writer.clone_document_from_reader(rendered)
        for number, page in enumerate(writer.pages, 1):
            if any(field['page'] == number for field in fields):
                page.merge_page(PdfReader(BytesIO(_overlay(number, fields))).pages[0])
        writer.add_metadata({'/Title': f'QA ONLY TXR-{code} {name} - synthetic and unsigned'})
        writer.write(args.output_dir / f'txr{code}-{name}.pdf')
        print(f'TXR-{code} {name}: {len(writer.pages)} pages, {len(fields)} field outlines')


if __name__ == '__main__':
    main()
