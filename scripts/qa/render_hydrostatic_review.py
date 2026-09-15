"""Produce three local synthetic QA specimens; never contact a signing service."""
from pathlib import Path
import argparse

from lib.trec_48_1 import render_trec_48_1, build_signwell_fields_trec48_1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--packet', action='store_true', help='Also render a synthetic combined purchase packet.')
    args = parser.parse_args()
    target = Path(args.output_dir)
    target.mkdir(parents=True,exist_ok=True)
    for risk in ('seller','buyer','buyer_capped'):
        raw = render_trec_48_1({'property_address':'123 Example Lane, Frisco',
                               'risk_allocation':risk,'buyer_liability_limit':'2,500.00'})
        (target / f'hydrostatic-{risk}.pdf').write_bytes(raw)
    if args.packet:
        from tests.test_controlled_launch import configure_local_forms
        from tests.test_hydrostatic_packet import hydrostatic_offer
        from lib.production_adapter import fill_and_merge_20_19
        configure_local_forms()
        offer = hydrostatic_offer(buyer1='Buyer One', buyer2='Buyer Two', buyer2Email='buyer2@example.test',
                                 seller='Seller One and Seller Two', seller2Name='Seller Two', seller2Email='seller2@example.test')
        (target / 'hydrostatic-purchase-packet.pdf').write_bytes(fill_and_merge_20_19(offer))
    print({'unsigned_review_pdfs':3,'signature_fields':build_signwell_fields_trec48_1(buyer_count=2,seller_count=2),
           'provider_completed':False})


if __name__ == '__main__':
    main()
