"""Unsigned synthetic page-six/continuation previews; no external calls."""
from pathlib import Path

from tests.test_contract_terms_continuation import long_answer
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer


def main():
    configure_local_forms()
    target = Path('tmp/pdfs/contract-terms')
    target.mkdir(parents=True, exist_ok=True)
    for mode in ('short', 'wrapped', 'long'):
        text = {'short':'Example informational item.',
                'wrapped':'Example informational item for the synthetic layout review. ' * 3,
                'long':long_answer(count=40)}[mode]
        offer = minimal_offer(address='123 Example Street', city='Example City',
                              buyer1='Example QA Buyer', seller='Example QA Seller',
                              brokerDisclosure=text, specialProvisions=text)
        path = target / (mode + '.pdf')
        path.write_bytes(adapter.fill_and_merge_20_19(offer))
        print(path)


if __name__ == '__main__':
    main()
