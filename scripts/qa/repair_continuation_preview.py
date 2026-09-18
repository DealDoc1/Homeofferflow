"""Local-only synthetic unsigned specimens; never send these to customers."""
from pathlib import Path
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer
from tests.test_repair_continuation import long_terms


def main():
    configure_local_forms()
    target = Path('tmp/pdfs/repair-continuation')
    target.mkdir(parents=True, exist_ok=True)
    for label, count in [('one-page', 18), ('multi-page', 70)]:
        offer = minimal_offer(buyer1='Example QA Buyer', buyerEmail='buyer@example.com',
                              buyer2='Second QA Buyer', buyer2Email='second@example.com',
                              seller='Example QA Seller', address='123 Example Street',
                              city='Example City', asIs='repairs', repairsText=long_terms(count))
        output = target / (label + '.pdf')
        output.write_bytes(adapter.fill_and_merge_20_19(offer))
        print(output)


if __name__ == '__main__':
    main()
